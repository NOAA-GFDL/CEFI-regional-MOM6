#!/usr/bin/env python3
"""
This script generated tide OBC from tpxo9
How to use:
./write_tpxo_boundary.py --config tpxo_obc.yaml
"""
import argparse
import numpy as np
from os import path
import pandas as pd
import xarray
import yaml
import os
from boundary import Segment

def write_tpxo(constituents, tpxo_dir, horizontal_subset):
    tpxo_h = (
        xarray.open_dataset(path.join(tpxo_dir, 'h_tpxo9.v1.nc'))
        .rename({'lon_z': 'lon', 'lat_z': 'lat', 'nc': 'constituent'})
        .isel(constituent=constituents, **horizontal_subset)
    )
    h = tpxo_h['ha'] * np.exp(-1j * np.radians(tpxo_h['hp']))
    mask = tpxo_h['ha'].isel(constituent=0) > 0
    tpxo_h['hRe'] = np.real(h).where(mask)
    tpxo_h['hIm'] = np.imag(h).where(mask)

    tpxo_u = (
        xarray.open_dataset(path.join(tpxo_dir, 'u_tpxo9.v1.nc'))
        .rename({'lon_u': 'lon', 'lat_u': 'lat', 'nc': 'constituent'})
        .isel(constituent=constituents, **horizontal_subset)
    )
    tpxo_u['ua'] *= 0.01  # convert to m/s
    u = tpxo_u['ua'] * np.exp(-1j * np.radians(tpxo_u['up']))
    mask = tpxo_u['ua'].isel(constituent=0) > 0
    tpxo_u['uRe'] = np.real(u).where(mask)
    tpxo_u['uIm'] = np.imag(u).where(mask)

    tpxo_v = (
        xarray.open_dataset(path.join(tpxo_dir, 'u_tpxo9.v1.nc'))
        .rename({'lon_v': 'lon', 'lat_v': 'lat', 'nc': 'constituent'})
        .isel(constituent=constituents, **horizontal_subset)
    )
    tpxo_v['va'] *= 0.01  # convert to m/s
    v = tpxo_v['va'] * np.exp(-1j * np.radians(tpxo_v['vp']))
    mask = tpxo_v['va'].isel(constituent=0) > 0
    tpxo_v['vRe'] = np.real(v).where(mask)
    tpxo_v['vIm'] = np.imag(v).where(mask)

    # Confirm that an old bug in the application of the land mask has not occured.
    for ds in [tpxo_h, tpxo_u, tpxo_v]:
        if ds.lat.isnull().any() or ds.lon.isnull().any():
            raise ValueError('NaNs in lat/lon coordinates')

    # Tidal amplitudes are currently constant over time.
    # Seem to need a time dimension to have it read by MOM.
    # But also, this would later allow nodal modulation
    # or other long-term variations to be added.
    times = xarray.DataArray(
        pd.date_range('1980-12-01', periods=1),
        dims=['time']
    )

    for seg in segments:
        seg.regrid_tidal_elevation(
            tpxo_h[['lon', 'lat', 'hRe']],
            tpxo_h[['lon', 'lat', 'hIm']],
            times,
            flood=True
        )

        seg.regrid_tidal_velocity(
            tpxo_u[['lon', 'lat', 'uRe']],
            tpxo_u[['lon', 'lat', 'uIm']],
            tpxo_v[['lon', 'lat', 'vRe']],
            tpxo_v[['lon', 'lat', 'vIm']],
            times,
            flood=True
        )

if __name__ == '__main__':
    """
    constituents in TPXO9:
    con =
    "m2  ",  0
    "s2  ",  1
    "n2  ",  2
    "k2  ",  3
    "k1  ",  4
    "o1  ",  5
    "p1  ",  6
    "q1  ",  7
    "mm  ",  8
    "mf  ",  9
    "m4  ", 10
    "mn4 ", 11
    "ms4 ", 12
    "2n2 ", 13
    "s1  "  14
    """
    parser = argparse.ArgumentParser(description='Script to write TPXO data to OBC segments.')
    parser.add_argument('--config', type=str, help='Path to YAML configuration file', default='tpxo_obc.yaml')
    args = parser.parse_args()

    # Default configuration
    default_config = {
        'constituents': range(0, 10),
        'tpxo_dir': '/work/acr/tpxo9/',
        'grid_file': '../../datasets/grid/ocean_hgrid.nc',
        'output_dir': './',
    }

    # Load user-specified configuration from YAML file
    with open(args.config, 'r') as file:
        user_config = yaml.safe_load(file)

    # Update default configuration with user-specified values
    config = {**default_config, **user_config}

    # Load configuration parameters
    constituents = config['constituents']
    tpxo_dir = config['tpxo_dir']
    grid_file = config['grid_file']
    output_dir = config['output_dir']

    # Extract indices from the configuration
    ny_start = config['indices']['ny_start']
    ny_end = config['indices']['ny_end']
    nx_start = config['indices']['nx_start']
    nx_end = config['indices']['nx_end']

    # Check if the output folder exists, create it if not
    if not path.exists(output_dir):
        os.makedirs(output_dir)

    # Subset TPXO9 to a region roughly around the NWA domain
    # for computational efficiency.
    print(ny_start,ny_end,nx_start,nx_end)
    horizontal_subset = dict(ny=slice(ny_start, ny_end), nx=slice(nx_start, nx_end))

    # Setup NWA boundaries
    hgrid = xarray.open_dataset(grid_file)

    # Load segments
    segments = []
    for seg_config in config.get('segments', []):
        segment = Segment(seg_config['id'], seg_config['border'], hgrid, output_dir=output_dir)
        segments.append(segment)

    write_tpxo(constituents, tpxo_dir, horizontal_subset)
