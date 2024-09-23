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

# ncecat --cnk_dmn time,1 -u time GLORYS_thetao_arctic_1994_01.nc GLORYS_thetao_arctic_1994_02.nc GLORYS_thetao_arctic_1994_03.nc GLORYS_thetao_arctic_1994_04.nc GLORYS_thetao_arctic_1994_05.nc GLORYS_thetao_arctic_1994_06.nc GLORYS_thetao_arctic_1994_07.nc GLORYS_thetao_arctic_1994_08.nc GLORYS_thetao_arctic_1994_09.nc GLORYS_thetao_arctic_1994_10.nc GLORYS_thetao_arctic_1994_11.nc GLORYS_thetao_arctic_1994_12.nc GLORYS_thetao_arctic_1994.nc

ncrcat -O /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_thetao_arctic_${year}_*.nc /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_thetao_arctic_${year}.nc
ncrcat -O /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_so_arctic_${year}_*.nc /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_so_arctic_${year}.nc

cp -f /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_so_arctic_${year}.nc /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_arctic_${year}.nc

ncks -A  /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_thetao_arctic_${year}.nc /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_arctic_${year}.nc

#rm  /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_thetao_arctic_${year}_*.nc
#rm  /work/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/filled/GLORYS_so_arctic_${year}_*.nc

