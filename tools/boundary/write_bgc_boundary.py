#!/usr/bin/env python3
"""
This script generate BGC  OBC 
Run on analysis, with module load nco/5.0.1
How to use:
./write_bgc_boundary.py --config bgc_obc.yaml
"""
import argparse
import os
import datetime as dt
from glob import glob
import numpy as np
from os import path
from shutil import copyfile
from subprocess import run
import xarray
import yaml
from boundary import flood_missing, Segment

def read_config(config_file):
    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)
    return config

def write_bgc(segments, time0, woa_file, esper_file, cobalt_file):
    woa_climo = xarray.open_dataset(woa_file)

    esper = (
        xarray.open_dataset(esper_file)
        .rename({'st_ocean': 'z', 'yt_ocean': 'lat', 'xt_ocean': 'lon'})
        .rename({'Alk': 'alk', 'DIC': 'dic'})
        * 1e-6  # micromoles -> moles
    )
    
    # Times are defined in the middle of the year.
    # Insert a data point for the initialization time
    # at the beginning using the first middle of the year data point.
    # To run the last year (2016), another end point will also need to be inserted.
    initial = esper.isel(time=0)
    initial['time'] = [time0]
    last = esper.isel(time=-1)
    last['time'] = [dt.datetime(2022, 1, 1)]
    esper = xarray.concat([initial, esper, last], dim='time')
    esper = esper.transpose('time', 'z', 'lat', 'lon')

    cobalt_vars = [
        # 'alk',
        'cadet_arag',
        'cadet_calc',
        # 'dic',
    #     'dic14',
    #     'do14',
    #     'do14c', 
    #     'di14c',
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
    #     'nh3', 
        'nh4', 
        # 'no3', 
        # 'o2', 
        'pdet', 
        # 'po4', 
        'srdon', 
        'srdop', 
        'sldon', 
        'sldop', 
        'sidet', 
        'silg', 
        # 'sio4', 
        'nsmz', 
        'nmdz', 
        'nlgz'
    ]
    cobalt = (
        xarray.open_mfdataset(cobalt_file)
        .rename({'st_ocean': 'z', 'geolat_t': 'lat', 'geolon_t': 'lon'})
        [cobalt_vars]
    )
    cobalt['time'] = [time0]

    # Flood cobalt all together here, in part so that the lat and lon coordinates can be re-added.
    cobalt_flooded = xarray.merge((
        flood_missing(cobalt[v], xdim='xt_ocean', ydim='yt_ocean', zdim='z') for v in cobalt.data_vars
    ))
    # Need to load or else xesmf will fail when trying to recognize coordinates.
    cobalt_flooded = cobalt_flooded.load()    
    cobalt_flooded = cobalt_flooded.assign_coords(lat=cobalt['lat'], lon=cobalt['lon'])

    # For 4P, create medium properties from large
    for v in ['si', 'fe', 'n']:
        cobalt_flooded[f'{v}md'] = cobalt_flooded[f'{v}lg']

    # For variable n:p, create p from n
    cobalt_flooded['psm'] = cobalt_flooded['nsm'] / 24.0
    cobalt_flooded['pmd'] = cobalt_flooded['nmd'] / 20.0
    cobalt_flooded['plg'] = cobalt_flooded['nlg'] / 14.0
    cobalt_flooded['pdi'] = cobalt_flooded['ndi'] / 40.0

    common_kws = dict(write=False)

    for seg in segments:
        # WOA
        woa_seg = xarray.merge((seg.regrid_tracer(woa_climo[v], regrid_suffix='woa_bgc', flood=True, periodic=False, **common_kws) for v in woa_climo))
        # Make sure no negative values were produced, just in case.
        for v in woa_seg.data_vars:
            woa_seg[v] = np.clip(woa_seg[v], 0.0, None)
        woa_seg = seg.add_coords(woa_seg)
        woa_seg['time'].attrs['units'] = 'days since 0001-01-01'
        woa_seg['time'].attrs['calendar'] = 'noleap'
        woa_seg['time'].attrs['modulo'] = ' '
        woa_seg['time'].attrs['cartesian_axis'] = 'T'
        seg.to_netcdf(woa_seg, 'bgc_woa')
        
        # ESPER
        # No flooding due to size
        esper_seg = xarray.merge((seg.regrid_tracer(esper[v], regrid_suffix='esper', flood=False, periodic=False, **common_kws) for v in esper))
        # Make sure no negative values were produced, just in case.
        for v in esper_seg.data_vars:
            esper_seg[v] = np.clip(esper_seg[v], 0.0, None)
        esper_seg = seg.add_coords(esper_seg)
        seg.to_netcdf(esper_seg, 'bgc_esper')
        
        # COBALT
        cobalt_seg = xarray.merge(
            (seg.regrid_tracer(cobalt_flooded[v], regrid_suffix='cobalt', flood=False, periodic=True, **common_kws) for v in cobalt_flooded)
        )
        # Make sure no negative values were produced, just in case.
        for v in cobalt_seg.data_vars:
            cobalt_seg[v] = np.clip(cobalt_seg[v], 0.0, None)
        cobalt_seg = seg.add_coords(cobalt_seg)
        seg.to_netcdf(cobalt_seg, 'bgc_cobalt')
        

def merge_segment_files(output_dir, source):
    """Merge separate segment files into one file per source of BGC data.
    I used to do this with CDO, but CDO overwrites the attributes for time
    and I can't figure out how to disable that.
    Instead, this appends one file at a time with NCO.
    """
    infiles = glob(path.join(output_dir, f'bgc_{source}_0*'))
    if len(infiles) <= 1:
        print(f'Not merging {source}; found {len(infiles)} files.')
        return None
    outfile = path.join(output_dir, f'bgc_{source}.nc')
    for i, f in enumerate(infiles):
        if i == 0:
            # Copy the first file as the final output file
            copyfile(f, outfile)
        else:
            # Append subsequent files to the copy of the first file
            run([f'ncks -A {f} {outfile}'], shell=True)


def main():
    parser = argparse.ArgumentParser(description='Generate BGC tracers obc.')
    parser.add_argument('--config', dest='config_file', default='bgc_obc.yaml', help='Path to the YAML configuration file')
    args = parser.parse_args()

    config = read_config(args.config_file)

    output_dir = config['output_dir']
    grid_file = config['grid_file']

    # Create output directory if it doesn't exist
    if not path.exists(output_dir):
        os.makedirs(output_dir)

    # Regional model domain and boundaries
    hgrid = xarray.open_dataset(grid_file)

    # Load segments
    segments = []
    for seg_config in config.get('segments', []):
        segment = Segment(seg_config['id'], seg_config['border'], hgrid, output_dir=output_dir)
        segments.append(segment)

    time0 = dt.datetime.strptime(str(config['time0']), '%Y-%m-%d')
    last_time = dt.datetime.strptime(str(config['last_time']), '%Y-%m-%d')   
 
    # WOA for no3, o2, po4, sio4
    woa_file = config['woa_file'] 

    # ESPER for dic and alk 
    esper_file = config['esper_file'] 

    # COBALT climatology for remaining variables
    cobalt_file = config['cobalt_file'] 

    write_bgc(segments, time0, woa_file, esper_file, cobalt_file)

    for source in ['woa', 'esper', 'cobalt']:
        merge_segment_files(output_dir, source)


if __name__ == '__main__':
    main()
