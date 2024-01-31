#!/usr/bin/env python3
"""
This script generated T,S, ssh, u, v OBC from Glorys
Have to make sure nan values in Glorys have been filled by non-nan values
Also this script require nco tools (optional) if you want to concatenat
multiple years results. 
Run on analysis, with module load nco/5.0.1
How to use:
./write_glorys_boundary.py --config glorys_obc.yaml 
"""
from subprocess import run
from os import path
import xarray
import yaml
from boundary import Segment
import argparse
import os

# xarray gives a lot of unnecessary warnings
import warnings
warnings.filterwarnings('ignore')

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def write_year(year, glorys_dir, segments, variables, is_first_year=False, is_last_year=False):
    glorys = (
        xarray.open_mfdataset(path.join(glorys_dir, f'GLORYS_REANALYSIS_{year}-*.nc'))
        .rename({'latitude': 'lat', 'longitude': 'lon', 'depth': 'z'})
    )

    # Floor first time down to midnight so that it matches initial conditions
    if is_first_year:
       tnew = xarray.concat((glorys['time'][0].dt.floor('1d'), glorys['time'][1:]), dim='time')
       glorys['time'] = ('time', tnew.data)
    elif is_last_year:
       tnew = xarray.concat((glorys['time'][0:-1], glorys['time'][-1].dt.ceil('1d')), dim='time')
       glorys['time'] = ('time', tnew.data)

    for seg in segments:
        for var in variables:
            if var == 'uv': 
                print(f'{seg.border} {var}')
                seg.regrid_velocity(glorys['uo'], glorys['vo'], suffix=year, flood=False)
            elif var == 'thetao' or var == 'so': 
                print(f'{seg.border} {var}')
                seg.regrid_tracer(glorys[var], suffix=year, flood=False)
            elif var == 'zos':
                print(f'{seg.border} {var}')
                seg.regrid_tracer(glorys['zos'], suffix=year, flood=False)


def ncrcat_years(nsegments, output_dir, variables):            
    for var in variables:
        for seg in range(1, nsegments+1):
            run([f'ncrcat -O {var}_{seg:03d}_* {var}_{seg:03d}.nc'], cwd=output_dir, shell=True)


def main(config_file):
    # Load configuration from YAML file
    config = load_config(config_file)

    # Extract configuration parameters
    first_year = config.get('first_year', 1993)
    last_year = config.get('last_year', 1994)
    glorys_dir = config.get('glorys_dir', '/work/acr/glorys/GLOBAL_MULTIYEAR_PHY_001_030/daily/filled')
    output_dir = config.get('output_dir', './outputs')
    hgrid_file = config.get('hgrid', '../../datasets/grid/ocean_hgrid.nc')
    ncrcat_years_flag = config.get('ncrcat_years', False)

    # Create output directory if it doesn't exist
    if not path.exists(output_dir):
        os.makedirs(output_dir)

    # Load hgrid
    hgrid = xarray.open_dataset(hgrid_file)

    # Load variables
    variables = config.get('variables', [])

    # Load segments
    segments = []
    for seg_config in config.get('segments', []):
        segment = Segment(seg_config['id'], seg_config['border'], hgrid, output_dir=output_dir)
        segments.append(segment)

    for y in range(first_year, last_year+1):
        print(y)
        write_year(y, glorys_dir, segments, variables, is_first_year=y == first_year, is_last_year=y == last_year)

    # Optional step: ncrcat_years
    if ncrcat_years_flag:
        ncrcat_years(len(segments), output_dir, variables)

if __name__ == '__main__':
    # Set default config file name
    default_config_file = 'glorys_obc.yaml'

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate obc from Glorys')
    parser.add_argument('--config', type=str, default=glorys_obc.yaml,
                        help='Specify the YAML configuration file name')
    args = parser.parse_args()

    # Run the main function with the specified or default config file
    main(args.config)
