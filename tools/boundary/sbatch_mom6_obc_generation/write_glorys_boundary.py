from glob import glob
import sys
from subprocess import run
from os import path
import xarray
sys.path.append('/home/Liz.Drenkard/TOOLS/CEFI-regional-MOM6/tools/boundary/')
from boundary import Segment

# xarray gives a lot of unnecessary warnings
import warnings
warnings.filterwarnings('ignore')

def write_year(year, monstr, daystr, glorys_dir, segments):
    glorys = ( 
         xarray.open_dataset(path.join(glorys_dir, f'GLORYS_REANALYSIS_NEP_{year}-{monstr}-{daystr}.nc'),decode_times=False)
        .rename({'latitude': 'lat', 'longitude': 'lon', 'depth': 'z'}))

    suff = (str(year) + '-' + monstr + '-' + daystr)
    for seg in segments:
        seg.regrid_velocity(glorys['uo'], glorys['vo'], suffix=suff, flood=False)
        for tr in ['thetao', 'so']:
            seg.regrid_tracer(glorys[tr], suffix=suff, flood=False)
        seg.regrid_tracer(glorys['zos'], suffix=suff, flood=False)
	

def main(y,m,d,outdir):
    glorys_dir = '/archive/e1n/datasets/GLORYS/'
    output_dir = outdir
    hgrid = xarray.open_dataset('/work/Liz.Drenkard/mom6/nep_5km/setup/grid/ocean_hgrid.nc')
 
    segments = [ 
        Segment(1, 'north', hgrid,output_dir=output_dir),
        Segment(2, 'east',  hgrid,output_dir=output_dir),
        Segment(3, 'south', hgrid,output_dir=output_dir),
        Segment(4, 'west',  hgrid,output_dir=output_dir)]

    write_year(y, m, d, (glorys_dir+str(y)+'/nep_10/'), segments)

if __name__ == '__main__':
    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
