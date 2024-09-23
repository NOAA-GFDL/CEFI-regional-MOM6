#!/bin/tcsh
#SBATCH --ntasks=1
#SBATCH --job-name=fill_glorys_arctic
#SBATCH --time=2880
#SBATCH --partition=batch

# Usage: sbatch fill_glorys_nn_monthly.sh <YEAR> <MONTH>

module load cdo
module load nco/5.0.1
module load gcp

set year=$1

set wpath='/work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled' 

# Concatenate monthly averages into single file
ncrcat -O ${wpath}/GLORYS_thetao_arctic_${year}_*.nc ${wpath}/GLORYS_thetao_arctic_${year}.nc
ncrcat -O ${wpath}/GLORYS_so_arctic_${year}_*.nc ${wpath}/GLORYS_so_arctic_${year}.nc

# Copy salt file to name for final file
cp -f ${wpath}/GLORYS_so_arctic_${year}.nc ${wpath}/GLORYS_arctic_${year}.nc

# Append temperature data to renamed salinity data 
ncks -A  ${wpath}/GLORYS_thetao_arctic_${year}.nc ${wpath}/GLORYS_arctic_${year}.nc

