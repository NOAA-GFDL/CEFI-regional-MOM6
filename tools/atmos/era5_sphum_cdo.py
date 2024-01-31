# module load python/3.9 cdo/1.9.10 ncks/5.0.1 gcp 

import os
from subprocess import check_call


def run_cmd(cmd, print_cmd=True):
    if print_cmd:
        print(cmd)
    check_call(cmd, shell=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('year', type=int)
    args = parser.parse_args()
    y = args.year
    tmp = os.environ['TMPDIR']
    run_cmd(f'gcp /work/acr/era5/global/ERA5_d2m_{y}_padded.nc {tmp}')
    run_cmd(f'gcp /work/acr/era5/global/ERA5_sp_{y}_padded.nc {tmp}')
    run_cmd(f'cdo expr,"svp=611.2*exp(17.67*(d2m-273.15)/(d2m-29.65))" {tmp}/ERA5_d2m_{y}_padded.nc {tmp}/ERA5_svp_{y}_padded.nc')
    run_cmd(f'cdo -expr,"_mr=0.622*svp/(sp-svp);sphum=_mr/(1+_mr);" -merge {tmp}/ERA5_svp_{y}_padded.nc {tmp}/ERA5_sp_{y}_padded.nc {tmp}/ERA5_sphum_{y}_padded.nc')
    run_cmd(f'ncks -4 -L 3 {tmp}/ERA5_sphum_{y}_padded.nc -O {tmp}/ERA5_sphum_{y}_padded.nc')
    run_cmd(f'gcp {tmp}/ERA5_sphum_{y}_padded.nc /work/acr/era5/global/')
