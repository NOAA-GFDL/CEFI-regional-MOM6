#!/usr/bin/env python3
"""
This script processes daily GLORYS data to generate ocean boundary conditions (OBC) for specified segments and variables. 
It supports regridding of velocity (u, v) and tracer fields (e.g., temperature, salinity, sea surface height) for a single day or concatenating multiple days of outputs. 

Key Features:
1. Processes single-day outputs: Generates regridded NetCDF files for each specified segment and variable.
2. Supports concatenation of results across multiple days or years using NCO tools (ncrcat).
3. Adjusts timestamps in concatenated files (optional).

Dependencies:
- GLORYS data files (NetCDF format) with specific variable names.
- NCO tools for file concatenation (optional, but required for multi-year concatenation).
- Python libraries: xarray, yaml, argparse.

Usage:
1. Process single-day output:
   ./write_glorys_boundary_day.py --config config.yaml --year <YEAR> --month <MONTH> --day <DAY>

2. Concatenate multiple days of results with optional timestamp adjustment:
   ./write_glorys_boundary_day.py --config config.yaml --ncrcat_years [--adjust_timestamps]

Ensure that NaN values in GLORYS data are pre-filled with valid values.
Run on a system with NCO tools installed, e.g., `module load nco/5.0.1` on HPC systems.
"""

import argparse
import os
from datetime import datetime, timedelta
from subprocess import run
from os import path

import xarray
import numpy as np
import yaml
from boundary import Segment

# Suppress xarray warnings
import warnings
warnings.filterwarnings('ignore')

def load_config(config_file):
    """Load configuration from a YAML file."""
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def write_day(date, glorys_dir, segments, variables, output_prefix):
    """Process and regrid data for a specific day."""
    filename = f"{output_prefix}_{date.year}-{date.month:02d}-{date.day:02d}.nc"
    file_path = path.join(glorys_dir, filename)

    if not path.exists(file_path):
        print(f"File does not exist: {file_path}. Skipping.")
        return

    glorys = (
        xarray.open_dataset(file_path, decode_times=False)
        .rename({'latitude': 'lat', 'longitude': 'lon', 'depth': 'z'})
    )

    # Capture time attributes and encoding
    time_attrs = glorys['time'].attrs if 'time' in glorys.coords else None
    time_encoding = glorys['time'].encoding if 'time' in glorys.coords else None

    for segment in segments:
        for variable in variables:
            if variable == 'uv':
                print(f"Processing {segment.border} {variable}")
                segment.regrid_velocity(glorys['uo'], glorys['vo'], suffix=f"{date:%Y%m%d}", flood=False,
                                        time_attrs=time_attrs, time_encoding=time_encoding )
            elif variable in ['thetao', 'so', 'zos']:
                print(f"Processing {segment.border} {variable}")
                segment.regrid_tracer(glorys[variable], suffix=f"{date:%Y%m%d}", flood=False,
                                      time_attrs=time_attrs, time_encoding=time_encoding)

def concatenate_files(nsegments, output_dir, variables, ncrcat_names, first_date, last_date, adjust_timestamps=False):
    """Concatenate annual files using ncrcat."""
    if not ncrcat_names:
        ncrcat_names = variables[:]

    date_list = [(first_date + timedelta(days=i)).strftime("%Y%m%d")
                 for i in range((last_date - first_date).days + 1)]

    for variable, var_name in zip(variables, ncrcat_names):
        for seg_id in range(1, nsegments + 1):
            input_files = [
                path.join(output_dir, f"{variable}_{seg_id:03d}_{date}.nc")
                for date in date_list
            ]
            output_file = path.join(output_dir, f"{var_name}_{seg_id:03d}.nc")

            if path.exists(output_file):
                print(f"Removing existing file: {output_file}")
                os.remove(output_file)

            print(f"Concatenating files for {variable}, segment {seg_id} into {output_file}...")
            run(["ncrcat", "-O", *input_files, output_file], check=True)

            if adjust_timestamps:
                adjust_file_timestamps(output_file)

def adjust_file_timestamps(file_path):
    """
    Adjust timestamps for the first and last records in a file while preserving attributes and raw numerical format.
    """
    with xarray.open_dataset(file_path, decode_times=False) as ds:
        # Explicitly load the dataset into memory if it's lazy-loaded
        ds.load()

        if 'time' in ds:
            # Extract the time variable, attributes, and encoding
            time = ds['time']
            time_attrs = time.attrs  # Save the original attributes
            time_encoding = time.encoding  # Save the original encoding
            time_values = time.values.copy()

            # Ensure the 'time' variable has more than one entry
            if len(time_values) > 1:
                # Adjust the first and last timestamps in raw numerical format
                time_values[0] = np.floor(time_values[0])  # Floor to the start of the day
                time_values[-1] = np.ceil(time_values[-1])  # Ceil to the end of the day

            # Create a new DataArray for time while preserving attributes
            new_time = xarray.DataArray(
                time_values,
                dims=time.dims,
                attrs=time_attrs,
                name='time'
            )

            # Assign the new time variable back to the dataset
            ds = ds.assign_coords(time=new_time)

            # Reapply the original encoding to ensure consistency 
            ds['time'].encoding = time_encoding

            # Save the updated dataset
            ds.to_netcdf(file_path)
            print(f"Timestamps adjusted for {file_path}")

def process_single_day(config, year, month, day):
    """Process data for a single day."""
    specific_date = datetime(year, month, day)
    print(f"Processing data for {specific_date}...")

    glorys_dir = config['glorys_dir']
    output_prefix = config.get('_OUTPUT_PREFIX', 'GLORYS')
    variables = config['variables']

    hgrid = xarray.open_dataset(config['hgrid'])
    segments = [
        Segment(seg_config['id'], seg_config['border'], hgrid, output_dir=config['output_dir'])
        for seg_config in config['segments']
    ]

    write_day(specific_date, glorys_dir, segments, variables, output_prefix)

def concatenate_annual_files(config, adjust_timestamps):
    """Concatenate files for the entire date range."""
    first_date = datetime.strptime(config['first_date'], '%Y-%m-%d')
    last_date = datetime.strptime(config['last_date'], '%Y-%m-%d')

    print(f"Concatenating files from {first_date} to {last_date}...")
    
    concatenate_files(
        len(config['segments']),
        config['output_dir'],
        config['variables'],
        config.get('ncrcat_names', []),
        first_date,
        last_date,
        adjust_timestamps
    )

def main():
    parser = argparse.ArgumentParser(description="Generate OBC from GLORYS")
    parser.add_argument('--config', type=str, default='glorys_obc.yaml', help="Path to the YAML configuration file")
    parser.add_argument('--year', type=int, help="Year for single-day processing")
    parser.add_argument('--month', type=int, help="Month for single-day processing")
    parser.add_argument('--day', type=int, help="Day for single-day processing")
    parser.add_argument('--ncrcat_years', action='store_true', help="Enable annual concatenation mode")
    parser.add_argument('--adjust_timestamps', action='store_true', help="Adjust timestamps during concatenation")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.ncrcat_years:
        concatenate_annual_files(config, args.adjust_timestamps)
    elif args.year and args.month and args.day:
        process_single_day(config, args.year, args.month, args.day)
    else:
        print("Error: Specify either --ncrcat_years or a specific date (--year, --month, --day).")

if __name__ == '__main__':
    main()
