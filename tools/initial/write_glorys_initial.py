#!/usr/bin/env python3
"""
script for preparing model IC (ssh,T,S,u,v) from Glorys data
How to use
./write_glorys_initial.py --config_file glorys_ic.yaml
"""
import sys
import os
import argparse
import yaml

import numpy as np
import xarray
import xesmf

from HCtFlood import kara as flood

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

#
#sys.path.append(os.path.join(script_dir, './depths'))
from depths import vgrid_to_interfaces, vgrid_to_layers

#
sys.path.append(os.path.join(script_dir, '../boundary'))
from boundary import rotate_uv


def write_initial(config):
    glorys_file = config['glorys_file']
    vgrid_file = config['vgrid_file']
    grid_file = config['grid_file']
    output_file = config['output_file']
    reuse_weights = config.get('reuse_weights', False)

    variable_names = config.get('variable_names', {})
    temp_var = variable_names.get('temperature', 'thetao')
    sal_var = variable_names.get('salinity', 'so')
    ssh_var = variable_names.get('sea_surface_height', 'zos')
    u_var = variable_names.get('zonal_velocity', 'uo')
    v_var = variable_names.get('meridional_velocity', 'vo')

    vgrid = xarray.open_dataarray(vgrid_file)
    z = vgrid_to_layers(vgrid)
    ztarget = xarray.DataArray(
        z,
        name='zl',
        dims=['zl'], 
        coords={'zl': z}, 
    )
    glorys = (
        xarray.open_dataset(glorys_file)
        [[temp_var, sal_var, ssh_var, u_var, v_var]]
        .rename({'longitude': 'lon', 'latitude': 'lat'})
    )
    # Round time down to midnight
    glorys['time'] = (('time', ), glorys['time'].dt.floor('1d').data)
   
    # Interpolate GLORYS vertically onto target grid.
    # Depths below bottom of GLORYS are filled by extrapolating the deepest available value.
    revert = glorys.interp(depth=ztarget, kwargs={'fill_value': 'extrapolate'}).ffill('zl', limit=None)

    # Flood temperature and salinity over land. 
    flooded = xarray.merge((
        flood.flood_kara(revert[v], zdim='zl') for v in [temp_var, sal_var, u_var, v_var]
    ))

    # flood zos separately to avoid the extra z=0 added by flood_kara.
    flooded[ssh_var] = flood.flood_kara(revert[ssh_var]).isel(z=0).drop('z')

    # Horizontally interpolate the vertically interpolated and flooded data onto the MOM grid. 
    target_grid = xarray.open_dataset(grid_file)
    target_t = (
        target_grid
        [['x', 'y']]
        .isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))
        .rename({'y': 'lat', 'x': 'lon', 'nxp': 'xh', 'nyp': 'yh'})
    )
    # Interpolate u and v onto supergrid to make rotation possible
    target_uv = (
        target_grid
        [['x', 'y']]
        .rename({'y': 'lat', 'x': 'lon'})
    )
    
    regrid_kws = dict(method='nearest_s2d', reuse_weights=reuse_weights, periodic=False)

    glorys_to_t = xesmf.Regridder(glorys, target_t, filename='regrid_glorys_tracers.nc', **regrid_kws)
    glorys_to_uv = xesmf.Regridder(glorys, target_uv, filename='regrid_glorys_uv.nc', **regrid_kws)

    interped_t = glorys_to_t(flooded[[temp_var, sal_var, ssh_var]])

    # Interpolate u and v, rotate, then extract individual u and v points
    interped_uv = glorys_to_uv(flooded[[u_var, v_var]])
    urot, vrot = rotate_uv(interped_uv[u_var], interped_uv[v_var], target_grid['angle_dx'])
    uo = urot.isel(nxp=slice(0, None, 2), nyp=slice(1, None, 2)).rename({'nxp': 'xq', 'nyp': 'yh'})
    uo.name = 'uo'
    vo = vrot.isel(nxp=slice(1, None, 2), nyp=slice(0, None, 2)).rename({'nxp': 'xh', 'nyp': 'yq'})
    vo.name = 'vo'
    
    interped = (
        xarray.merge((interped_t, uo, vo))
        .transpose('time', 'zl', 'yh', 'yq', 'xh', 'xq')
    )

    # Rename to match MOM expectations.
    interped = interped.rename({
        temp_var: 'temp',
        sal_var: 'salt',
        ssh_var: 'ssh',
        u_var: 'u',
        v_var: 'v'
    })

    # Fix output metadata, including removing all _FillValues.
    all_vars = list(interped.data_vars.keys()) + list(interped.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}
    encodings['time'].update({'dtype':'float64', 'calendar': 'gregorian'})
    interped['zl'].attrs = {
        'long_name': 'Layer pseudo-depth, -z*',
         'units': 'meter',
         'cartesian_axis': 'Z',
         'positive': 'down'
    }

    # Extract the directory from the output_file pat
    output_folder = os.path.dirname(output_file)
    
    # Check if the output folder exists, and if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)   

    # output results
    interped.to_netcdf(
        output_file,
        format='NETCDF3_64BIT',
        engine='netcdf4',
        encoding=encodings,
        unlimited_dims='time'
    )


def main():

    parser = argparse.ArgumentParser(description='Generate ICs from Glorys.')
    parser.add_argument('--config_file', type=str, default='glorys_ic.yaml' , help='Path to the YAML config file')
    args = parser.parse_args()

    if not args.config_file:
        parser.error('Please provide the path to the YAML config file.')

    with open(args.config_file, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)

    if not all(key in config for key in ['glorys_file', 'vgrid_file', 'grid_file', 'output_file']):
        parser.error('Please provide all required parameters in the YAML config file.')

    write_initial(config)

if __name__ == '__main__':
    main()
