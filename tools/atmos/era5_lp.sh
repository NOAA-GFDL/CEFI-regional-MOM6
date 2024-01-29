#!/bin/bash -e
#SBATCH --ntasks=1
#SBATCH --job-name=era5_lp
#SBATCH --time=08:00:00
#SBATCH --partition=batch


module load cdo/2.1.0
module load gcp

gcp /work/acr/era5/global/ERA5_tp_${1}_padded.nc /work/acr/era5/global/ERA5_sf_${1}_padded.nc $TMPDIR
cdo -setrtoc,-1e9,0,0 -chname,tp,lp -sub $TMPDIR/ERA5_tp_${1}_padded.nc $TMPDIR/ERA5_sf_${1}_padded.nc $TMPDIR/ERA5_lp_${1}_padded.nc
gcp $TMPDIR/ERA5_lp_${1}_padded.nc /work/acr/era5/global/

