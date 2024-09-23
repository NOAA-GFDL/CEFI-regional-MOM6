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
set month=`printf "%02d" $2`

set apath='/archive/Theresa.Morrison/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/thetao'
mkdir ${apath}/thetao_${year}_${month}

set day=1
foreach filename (/uda/Global_Ocean_Physics_Reanalysis/global/daily/thetao/${year}/thetao_mercatorglorys12v1_gl12_mean_${year}${month}*.nc)
  echo $filename 
  set short_name='thetao_arctic_'$day
  ncks -d latitude,39.,91. --mk_rec_dmn time $filename ${apath}/thetao_${year}_${month}/${short_name}'_bd.nc'
  cdo -setreftime,1993-01-01,00:00:00,1day ${apath}/thetao_${year}_${month}/${short_name}'_bd.nc' ${apath}/thetao_${year}_${month}/${short_name}'.nc'
  rm -f ${apath}/thetao_${year}_${month}/${short_name}'_bd.nc'
  set day = `expr $day + 1`
  echo $day
end
ncra -O --cnk_plc=r1d --cnk_dmn=time,1  ${apath}/thetao_${year}_${month}/thetao_arctic_*.nc ${apath}/GLORYS_thetao_arctic_${year}_${month}.nc
rm -f  ${apath}/thetao_${year}_${month}/thetao_arctic_*.nc
rm -rf ${apath}/thetao_${year}_${month}
