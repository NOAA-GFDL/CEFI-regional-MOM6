#!/usr/bin/env python3
"""
How to use
./write_nudging_data.py --config_file config.yaml
"""

import numpy as np
import os
import pandas as pd
import xarray
import xesmf


VARIABLES = ['thetao', 'so']


def add_bounds(ds):
    # Add data points at end of month, since time_bnds aren't used
    # All points extend to 23:59:59 at end of month, except
    # for the end of the year which is padded to 00:00:00 the next Jan 1.
    # normalize=True rolls down to midnight
    mstart = [d - pd.offsets.MonthBegin(normalize=True) if d.day > 1 else d for d in ds['time'].to_pandas()]
    mend = [d + pd.DateOffset(months=1) if d.month == 12 else d + pd.DateOffset(months=1) - pd.Timedelta(seconds=1) for d in mstart]
    starts = ds.copy()
    starts['time'] = mstart
    ends = ds.copy()
    ends['time'] = mend
    bounded = xarray.concat((starts, ends), dim='time').sortby('time')
    # Ensure that order is correct so that time can be unlimited dim
    bounded = bounded.transpose('time', 'depth', 'yh', 'xh')
    return bounded


def reuse_regrid(*args, **kwargs):
    filename = kwargs.pop('filename', None)
    reuse_weights = kwargs.pop('reuse_weights', False)

    if reuse_weights:
        if filename.is_file():
            return xesmf.Regridder(*args, reuse_weights=True, filename=filename, **kwargs)
        else:
            regrid = xesmf.Regridder(*args, **kwargs)
            regrid.to_netcdf(filename)
            return regrid
    else:
        regrid = xesmf.Regridder(*args, **kwargs)
        return regrid



if __name__ == '__main__':
    import argparse
    from pathlib import Path
    from yaml import safe_load
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    args = parser.parse_args()
    with open(args.config, 'r') as file: 
        config = safe_load(file)
    static = xarray.open_dataset(config['filesystem']['ocean_static'])
    target_grid = static[['geolat', 'geolon']].rename({'geolat': 'lat', 'geolon': 'lon'})
    nudging_data = config['filesystem']['monthly_data_nudging']
    regridder = None
    model_input = Path(config['filesystem']['model_input_data']) / 'nudging'
    model_input.mkdir(exist_ok=True)
    for year in range(config['forecasts']['first_year'], config['forecasts']['last_year']+1):
        print(f'{year}')
        glorys = (
            xarray.open_dataset(nudging_data.format(year=year))
            .rename({'latitude': 'lat', 'longitude': 'lon'})
            [VARIABLES]
        )
        print('  Filling')
        filled = glorys.ffill('depth', limit=None)
        filled = filled.compute()
        if regridder is None:
            print('  Setting up regridder')
            regridder = reuse_regrid(
                glorys, target_grid, 
                filename=Path(os.environ['TMPDIR']) / 'regrid_nudging.nc', 
                method='nearest_s2d', 
                reuse_weights=True,
                periodic=False
            )
        print('  Interpolating')
        interped = (
            regridder(filled)
            .drop(['lon', 'lat'], errors='ignore')
            .compute()
        ) 
        print('  Setting time bounds and coordinates')
        bounded = add_bounds(interped)
        # Add coordinate information
        bounded['xh'] = (('xh', ), target_grid.xh.data)
        bounded['yh'] = (('yh', ), target_grid.yh.data)
        all_vars = list(bounded.data_vars.keys()) + list(bounded.coords.keys())
        encodings = {v: {'_FillValue': None} for v in all_vars}
        encodings['time'].update({'dtype':'float64', 'calendar': 'gregorian', 'units': 'days since 1993-01-01'})
        bounded['depth'].attrs = {
            'cartesian_axis': 'Z',
            'positive': 'down'
        }
        bounded['time'].attrs['cartesian_axis'] = 'T'
        bounded['xh'].attrs = {'cartesian_axis': 'X'}
        bounded['yh'].attrs = {'cartesian_axis': 'Y'}
        print('  Writing')
        bounded.to_netcdf(
            model_input / f'nudging_monthly_{year}.nc',
            format='NETCDF3_64BIT',
            engine='netcdf4',
            encoding=encodings,
            unlimited_dims='time'
        )
        glorys.close() 
