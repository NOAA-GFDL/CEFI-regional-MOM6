#!/usr/bin/env python3
"""
This script generated runoff from GloFAS data 
How to use:
./write_runoff_glofas.py --config runoff_glofas.yaml 
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import os
import yaml
import argparse
import xarray
import xesmf

def read_config(config_file):
    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)
    return config

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate runoff file from GloFAS data.')
    parser.add_argument('--config', '-c', default='runoff_glofas.yaml', help='YAML configuration file')
    return parser.parse_args()

def get_coast_mask(mask):
    # Alistair's method of finding coastal cells
    ocn_mask = mask.values
    cst_mask = 0 * ocn_mask # All land should be 0
    is_ocean = ocn_mask > 0
    cst_mask[(is_ocean) & (np.roll(ocn_mask, 1, axis=1) == 0)] = 1 # Land to the west
    cst_mask[(is_ocean) & (np.roll(ocn_mask, -1, axis=1) == 0)] = 1 # Land to the east
    cst_mask[(is_ocean) & (np.roll(ocn_mask, 1, axis=0) == 0)] = 1 # Land to the south
    cst_mask[(is_ocean) & (np.roll(ocn_mask, -1, axis=0) == 0)] = 1 # Land to the north

    # Model boundaries are not coasts
    cst_mask[0, :] = 0
    cst_mask[:, 0] = 0
    cst_mask[-1, :] = 0
    cst_mask[:, -1] = 0

    return cst_mask


def reuse_regrid(*args, **kwargs):
    filename = kwargs.pop('filename', None)
    reuse_weights = kwargs.pop('reuse_weights', False)

    if reuse_weights:
        if os.path.isfile(filename):
            return xesmf.Regridder(*args, reuse_weights=True, filename=filename, **kwargs)
        else:   
            regrid = xesmf.Regridder(*args, **kwargs)
            regrid.to_netcdf(filename)
            return regrid
    else:
        regrid = xesmf.Regridder(*args, **kwargs)
        return regrid


def expand_mask_true(mask, window):
    """Given a 2D bool mask, expand the true values of the
    mask so that at a given point, the mask becomes true
    if any point within a window x window box
    is true.
    Note, points near the edges of the mask, where the 
    box would expand beyond the mask, are always set to false.

    Args:
        mask: 2D boolean numpy array
        window: width of the square box used to expand the mask

    """
    wind = sliding_window_view(mask, (window, window))
    wind_mask = wind.any(axis=(2, 3))
    final_mask = np.zeros_like(mask)
    i = int((window - 1) / 2) # width of edges that can't fit a full box
    final_mask[i:-i, i:-i] = wind_mask
    return final_mask.astype('bool')


def write_runoff(glofas, glofas_mask, hgrid, coast_mask, out_file):
    glofas_latb = np.arange(glofas['lat'][0]+.05, glofas['lat'][-1]-.051, -.1)
    glofas_lonb = np.arange(glofas['lon'][0]-.05, glofas['lon'][-1]+.051, .1)
    
    lon = hgrid.x[1::2, 1::2]
    lonb = hgrid.x[::2, ::2]
    lat = hgrid.y[1::2, 1::2]
    latb = hgrid.y[::2, ::2]
    # From Alistair
    area = (hgrid.area[::2, ::2] + hgrid.area[1::2, 1::2]) + (hgrid.area[1::2, ::2] + hgrid.area[::2, 1::2])
    
    # Convert m3/s to kg/m2/s
    # Borrowed from https://xgcm.readthedocs.io/en/latest/xgcm-examples/05_autogenerate.html
    distance_1deg_equator = 111000.0
    dlon = dlat = 0.1  # GloFAS grid spacing
    dx = dlon * np.cos(np.deg2rad(glofas.lat)) * distance_1deg_equator
    dy = ((glofas.lon * 0) + 1) * dlat * distance_1deg_equator
    glofas_area = dx * dy
    glofas_kg = glofas * 1000.0 / glofas_area
    
    # Conservatively interpolate runoff onto MOM grid
    glofas_to_mom_con = reuse_regrid(
        {'lon': glofas.lon, 'lat': glofas.lat, 'lon_b': glofas_lonb, 'lat_b': glofas_latb},
        {'lat': lat, 'lon': lon, 'lat_b': latb, 'lon_b': lonb},
        method='conservative',
        periodic=True,
        reuse_weights=True,
        filename=os.path.join(os.environ['TMPDIR'], 'glofas_to_mom.nc')
    )
    # Interpolate only from GloFAS points that are river end points.
    glofas_regridded = glofas_to_mom_con(glofas_kg.where(glofas_mask > 0).fillna(0.0))
    
    glofas_regridded = glofas_regridded.rename({'nyp': 'ny', 'nxp': 'nx'}).values

    # For NWA12 only: remove runoff from west coast of Guatemala 
    # and El Salvador that actually drains into the Pacific.
    glofas_regridded[:, 0:190, 0:10] = 0.0
    glofas_regridded[:, 0:150, 0:100] = 0.0
    glofas_regridded[:, 0:125, 100:170] = 0.0
    glofas_regridded[:, 0:60, 170:182] = 0.0
    glofas_regridded[:, 0:45, 180:200] = 0.0
    glofas_regridded[:, 0:40, 200:220] = 0.0
    glofas_regridded[:, 0:45, 220:251] = 0.0
    glofas_regridded[:, 0:50, 227:247] = 0.0
    glofas_regridded[:, 0:35, 250:270] = 0.0

    # Remove runoff along the southern boundary to avoid double counting
    glofas_regridded[:, 0:1, :] = 0.0

    # For NWA12 only: remove runoff from Hudson Bay
    glofas_regridded[:, 700:, 150:300] = 0.0
    
    # For NWA12 only: Mississippi River adjustment.
    # Adjust to be approximately the same as the USGS station at Belle Chasse, LA
    # and relocate closer to the end of the delta.
    ms_total_kg = glofas_regridded[:, 317:320, 106:108] 
    # Convert to m3/s
    ms_total_cms = (ms_total_kg * np.broadcast_to(area[317:320, 106:108], ms_total_kg.shape)).sum(axis=(1, 2)) / 1000.0 
    ms_corrected = 0.5192110112243014 * ms_total_cms + 3084.5571334312735
    glofas_regridded[:, 317:320, 106:108] = 0.0
    new_ms_coords = [(314, 108), (315, 107), (317, 112)]
    for c in new_ms_coords:
        y, x = c
        glofas_regridded[:, y, x] = (1 / len(new_ms_coords)) * ms_corrected * 1000.0 / float(area[y, x])

    # Flatten mask and coordinates to 1D
    flat_mask = coast_mask.ravel().astype('bool')
    coast_lon = lon.values.ravel()[flat_mask]
    coast_lat = lat.values.ravel()[flat_mask]
    mom_id = np.arange(np.prod(coast_mask.shape))

    # Use xesmf to find the index of the nearest coastal cell
    # for every grid cell in the MOM domain
    coast_to_mom = reuse_regrid(
        {'lat': coast_lat, 'lon': coast_lon},
        {'lat': lat, 'lon': lon},
        method='nearest_s2d',
        locstream_in=True,
        reuse_weights=True,
        filename=os.path.join(os.environ['TMPDIR'], 'coast_to_mom.nc')
    )
    coast_id = mom_id[flat_mask]
    nearest_coast = coast_to_mom(coast_id)
    
    # For NWA12 only: the Susquehanna gets mapped to the Delaware
    # because NWA12 only has the lower half of the Chesapeake.
    # Move the nearest grid point for the Susquehanna Region
    # to the one for the lower bay.
    # see notebooks/check_glofas_susq.ipynb
    target = nearest_coast[455, 271]
    nearest_coast[460:480, 265:278] = target
    
    nearest_coast = nearest_coast.ravel()

    # Raw runoff on MOM grid, reshaped to 2D (time, grid_id)
    raw = glofas_regridded.reshape([glofas_regridded.shape[0], -1])

    # Zero array that will be filled with runoff at coastal cells
    filled = np.zeros_like(raw)

    # Loop over each coastal cell and fill the result array
    # with the sum of runoff for every grid cell that
    # has this coastal cell as its closest coastal cell
    for i in coast_id:
        filled[:, i] = raw[:, nearest_coast == i].sum(axis=1)

    # Reshape back to 3D
    filled_reshape = filled.reshape(glofas_regridded.shape)

    # Convert to xarray
    ds = xarray.Dataset({
        'runoff': (['time', 'y', 'x'], filled_reshape),
        'area': (['y', 'x'], area.data),
        'lat': (['y', 'x'], lat.data),
        'lon': (['y', 'x'], lon.data)
        },
        coords={'time': glofas['time'].data, 'y': np.arange(filled_reshape.shape[1]), 'x': np.arange(filled_reshape.shape[2])}
    )

    # Drop '_FillValue' from all variables when writing out
    all_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}

    # Make sure time has the right units and datatype
    # otherwise it will become an int and MOM will fail. 
    encodings['time'].update({
        'units': 'days since 1950-01-01',
        'dtype': 'float', 
        'calendar': 'gregorian'
    })

    ds['time'].attrs = {'cartesian_axis': 'T'}
    ds['x'].attrs = {'cartesian_axis': 'X'}
    ds['y'].attrs = {'cartesian_axis': 'Y'}
    ds['lat'].attrs = {'units': 'degrees_north'}
    ds['lon'].attrs = {'units': 'degrees_east'}
    ds['runoff'].attrs = {'units': 'kg m-2 s-1'}

    # Write out
    ds.to_netcdf(
        out_file,
        unlimited_dims=['time'],
        format='NETCDF3_64BIT',
        encoding=encodings,
        engine='netcdf4'
    )
    ds.close()


if __name__ == '__main__':

    args = parse_arguments()
    config_file = args.config
    config = read_config(config_file)

    ocean_mask = xarray.open_dataset(config['grid_mask_file'])
    hgrid = xarray.open_dataset(config['hgrid_file']) 

    mom_coast_mask = get_coast_mask(ocean_mask['mask'])

    # For NWA12: subset GloFAS to a smaller region containing NWA.
    glofas_subset = dict(
        lat=slice(config['latitude_range']['start'], config['latitude_range']['end']),
        lon=slice(config['longitude_range']['start'], config['longitude_range']['end'])
    )

    ldd = xarray.open_dataarray(config['ldd_file']).sel(**glofas_subset)

    # Start pour point mask to include points where ldd==5
    # and any surrounding point is ocean (nan in ldd)
    adjacent = np.logical_and(ldd==5.0, expand_mask_true(np.isnan(ldd), 3))
    imax = 20 # max number of iterations
    for i in range(imax):
        # Number of points previously:
        npoints = int(adjacent.sum())
        # Update pour point mask to include points where ldd==5
        # and any surrounding point was previously identified as a pour point
        adjacent = np.logical_and(ldd==5.0, expand_mask_true(adjacent, 3))
        # Number of points in updated mask:
        npoints_new = int(adjacent.sum())
        # If the number of points hasn't changed, it has converged.
        if npoints_new == npoints:
            print(f'Converged after {i+1} iterations')
            break
    else:
        raise Exception('Did not converge')

    # Note; converting from dataarray to numpy, because the 
    # glofas ldd coordinates are float32 and the 
    # glofas runoff coordinates are float64 
    glofas_coast_mask = adjacent.values

    if not os.path.exists(config['output_dir']):
        os.makedirs(config['output_dir'])

    for y in range(config['start_year'], config['end_year'] + 1):
        print(y)
        # GloFAS 3.1 data copied to vftmp from:
        # /archive/e1n/datasets/GloFAS/
        # in latest version, should only need to pad at the end of the year
        # (times are refd to midnight)
        glofas_files = [config['glofas_files_pattern'].format(year=y)]
        glofas = (
            xarray.open_mfdataset(glofas_files, combine='by_coords')
            .rename({'latitude': 'lat', 'longitude': 'lon'})
            .sel(time=slice(f'{y-1}-12-31 12:00:00', f'{y+1}-01-01 12:00:00'), **glofas_subset)
            .dis24
        )
        out_file = os.path.join(config['output_dir'], f'glofas_runoff_{y}.nc')
        write_runoff(glofas, glofas_coast_mask, hgrid, mom_coast_mask, out_file)
