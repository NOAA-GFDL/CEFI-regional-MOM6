#!/bin/tcsh
#SBATCH --ntasks=1
#SBATCH --job-name=merge_so_thetao
#SBATCH --time=2880
#SBATCH --partition=batch

# Usage: sbatch merge_so_thetao_year.csh <YEAR> 

module load cdo
module load nco/5.0.1
module load gcp

set year=$1
set wpath='/work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled' 


# Define the file variables for salinity and temperature
set so_file = "${wpath}/GLORYS_so_arctic_${year}.nc"
set thetao_file = "${wpath}/GLORYS_thetao_arctic_${year}.nc"
set final_file = "${wpath}/GLORYS_arctic_${year}.nc"

# Concatenate monthly averages into single files for salinity and temperature
foreach var (so thetao)
    ncrcat -O ${wpath}/GLORYS_${var}_arctic_${year}_*.nc ${wpath}/GLORYS_${var}_arctic_${year}.nc
    end

    # Append temperature data to salinity file directly without copying
    ncks -A ${thetao_file} ${so_file}

    # Rename the combined file to final name
    mv -f ${so_file} ${final_file}
