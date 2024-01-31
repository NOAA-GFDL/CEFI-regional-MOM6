#!/usr/bin/env python3
"""
script for preparing bgc model ICs (cobalt-4p)
How to use
./write_bgc_initial.py --config_file bgc_ic.yaml
"""
import datetime as dt
from functools import partial
import sys
import os
import argparse
import yaml

import numpy as np
import xarray
import xesmf

from HCtFlood import kara as flood
from depths import vgrid_to_layers 


def interpolate_flood(target_grid, ztarget, ds, xdim=None, ydim=None, periodic=True):
    revert = ds.interp(z=ztarget).ffill('zl', limit=None).bfill('zl', limit=None)
    if xdim is None and ydim is None:
        flooded = xarray.merge((
            flood.flood_kara(revert[v], zdim='zl') for v in revert.data_vars
        )).squeeze().drop('time')
    else:
        flooded = xarray.merge((
            flood.flood_kara(revert[v], xdim=xdim, ydim=ydim, zdim='zl') for v in revert.data_vars
        )).squeeze().drop('time')
    ds_to_mom = xesmf.Regridder(
        ds, 
        target_grid, 
        method='nearest_s2d', 
        periodic=periodic
    )
    interped = ds_to_mom(flooded).load()
    interped = interped.drop(['lon', 'lat'], errors='ignore')
    # for v in interped.data_vars:
    #     interped[v] = np.clip(interped[v], 0.0, None)
    return interped


def write_bgc(woa_file, esper_file, cobalt_file, time0, interpolator, output_file):
    print('WOA')
    woa = xarray.open_dataset(woa_file).isel(time=0)
    woa_interped = interpolator(woa)

    print('ESPER')
    esper = (
        xarray.open_dataset(esper_file)
        .rename({'st_ocean': 'z', 'yt_ocean': 'lat', 'xt_ocean': 'lon'})
        .rename({'Alk': 'alk', 'DIC': 'dic'})
        .transpose('time', 'z', 'lat', 'lon')
        .sel(time=f'{time0.year}')
        * 1e-6  # micromoles -> moles
    )
    esper_interped = interpolator(esper, periodic=False)

    print('COBALT')
    cobalt_vars = [
        'cadet_arag',
        'cadet_calc',
        'fed', 
        'fedi',
        'felg',
        'fedet',
        'fesm',
        'ldon',
        'ldop', 
        'lith', 
        'lithdet', 
        'nbact', 
        'ndet', 
        'ndi', 
        'nlg', 
        'nsm', 
        'nh4', 
        'pdet', 
        'srdon', 
        'srdop', 
        'sldon', 
        'sldop', 
        'sidet', 
        'silg', 
        'nsmz', 
        'nmdz', 
        'nlgz'
    ]
    cobalt = (
        xarray.open_dataset(cobalt_file)
        .rename({'st_ocean': 'z', 'geolat_t': 'lat', 'geolon_t': 'lon'})
        [cobalt_vars]
        # subset around NWA domain:
        .isel(xt_ocean=slice(170, 250), yt_ocean=slice(100, 170))
        .squeeze()
    )

    cobalt_interped = interpolator(cobalt, periodic=False, xdim='xt_ocean', ydim='yt_ocean')

    # For 4P, create medium properties from large
    for v in ['si', 'fe', 'n']:
        cobalt_interped[f'{v}md'] = cobalt_interped[f'{v}lg']

    # For variable n:p, create p from n
    cobalt_interped['psm'] = cobalt_interped['nsm'] / 24.0
    cobalt_interped['pmd'] = cobalt_interped['nmd'] / 20.0
    cobalt_interped['plg'] = cobalt_interped['nlg'] / 14.0
    cobalt_interped['pdi'] = cobalt_interped['ndi'] / 40.0

    print('Merge')
    interped = xarray.merge((woa_interped, esper_interped, cobalt_interped))

    # Copy xh and yh from the target grid
    for v in ['xh', 'yh']:
        interped[v] = interpolator.args[0][v]
        
    interped['Time'] = ('Time', [time0])

    # Make sure each variable has Time as a dimension
    for v in interped.data_vars:
        interped[v] = interped[v].expand_dims('Time', 0)
        
    interped = interped.set_coords('Time')

    # The model expects these variables in the initial conditions, but we don't have initial 
    # condition data for them, so set them to a very small value everywhere.
    print('Constant')
    zero_vars = [
        'dic14',
        'do14',
        'do14c',
        'di14c',
        'nh3',
        'mu_mem_nsm',
        'mu_mem_nlg',
        'mu_mem_ndi',
        'irr_aclm',
        'fedet_btf',
        'sidet_btf',
        'pdet_btf', 
        'ndet_btf',
        'lithdet_btf',
        'cadet_calc_btf',
        'cadet_arag_btf',
        'co3_ion',
        'cased',
        'chl',
        # new 4P cobalt zero vars:
        'nsm_btf',
        'nmd_btf',
        'nlg_btf',
        'ndi_btf',
        'fesm_btf',
        'femd_btf',
        'felg_btf',
        'fedi_btf',
        'simd_btf',
        'silg_btf',
        'pdi_btf', # x
        'plg_btf', # x
        'pmd_btf', # x
        'psm_btf', # x
        'irr_mem_dp',
        'irr_aclm_sfc',
        'irr_aclm_z',
        'mu_mem_nmd'
    ]
    nt = 1
    nz = len(interped['zl'])
    ny = len(interped['yh'])
    nx = len(interped['xh'])
    for v in zero_vars:
        if '_btf' in v:
            val = 0.0
        else:
            val = 1e-10
        interped[v] = (
            ('Time', 'zl', 'yh', 'xh'), 
            np.zeros((nt, nz, ny, nx))+val
        )

    # set pH
    interped['htotal'] = (
        ('Time', 'zl', 'yh', 'xh'), 
        np.zeros((nt, nz, ny, nx))+1e-8
    )

    print('Write')
    # Make sure no variable has a _FillValue
    all_vars = list(interped.data_vars.keys()) + list(interped.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}

    interped['Time'].attrs = {'cartesian_axis': 'T'}

    interped['zl'].attrs = {
        'long_name': 'Layer pseudo-depth, -z*',
        'units': 'meter',
        'cartesian_axis': 'Z',
        'positive': 'down'
    }

    # Check if the output folder exists, and if not, create it
    output_folder = os.path.dirname(output_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    interped.to_netcdf(
        output_file,
        format='NETCDF3_64BIT',
        encoding=encodings,
        engine='netcdf4'
    )


def main():

    parser = argparse.ArgumentParser(description='Generate BGC initial conditions for mom6-cobalt.')
    parser.add_argument('--config_file', type=str, default='bgc_ic.yaml', help='Path to the YAML config file')
    args = parser.parse_args()

    
    with open(args.config_file, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)

    # Vertical grid to interpolate data to:
    vgrid = xarray.open_dataarray(config['vgrid_file'])
    z = vgrid_to_layers(vgrid)
    ztarget = xarray.DataArray(
        z,
        name='zl',
        dims=['zl'],
        coords={'zl': z},
    )

    # Horizontal grid to interpolate data to:
    grid = xarray.open_dataset(config['grid_file'])
    target_grid = (
        grid
        [['geolat', 'geolon']]
        .rename({'geolat': 'lat', 'geolon': 'lon'})
    )

    # Partial function to flood and horizontally and vertically interpolate
    # data onto the target horizontal and vertical grids:
    global interpolator 
    interpolator = partial(interpolate_flood, target_grid, ztarget)

    # Time of the model initialization:
    time0 = dt.datetime.strptime(str(config['time0']), '%Y-%m-%d')

    write_bgc(config['woa_file'], config['esper_file'], config['cobalt_file'], time0, interpolator, config['output_file'])


if __name__ == '__main__':
    main()
