#!/bin/tcsh
#SBATCH --ntasks=1
#SBATCH --job-name=fill_glorys_nn
#SBATCH --time=2880
#SBATCH --partition=batch

# Usage: sbatch fill_glorys_nn.sh <YEAR> <MONTH>
# This script is used to fill the GLORYS reanalysis data on GFDL PPAN
# We will need better method for the GLORYS real time analysis data (e.g. filtering out bad data before filling data)

module load cdo
module load nco/5.0.1
module load gcp

set year=$1
set month=`printf "%02d" $2`

# Put the regionally-sliced daily GLORYS reanalysis on archive beforehand.

# dmget all of the files for this month from archive.
dmget /archive/acr/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/daily/GLORYS_REANALYSIS_${year}-${month}-*.nc

# copy from archive to vftmp for speed?
gcp /archive/acr/datasets/glorys/GLOBAL_MULTIYEAR_PHY_001_030/daily/GLORYS_REANALYSIS_${year}-${month}-*.nc $TMPDIR

# create a directory to store the filled files.
mkdir $TMPDIR/filled

# look for all of the daily files. 
# loop over them, using cdo setmisstonn to fill the missing data
# and then ncks to compress the resulting file.
find ${TMPDIR}/GLORYS_REANALYSIS_${year}-${month}-*.nc -type f -exec sh -c 'file="$1"; filename="${file##*/}"; cdo setmisstonn "$1" "${TMPDIR}/filled/${filename}"; ncks -4 -L 5 "${TMPDIR}/filled/${filename}" -O "${TMPDIR}/filled/${filename}"' find-sh {} \;

# copy the filled data for this month to /work.
gcp $TMPDIR/filled/*.nc /work/acr/glorys/GLOBAL_MULTIYEAR_PHY_001_030/daily/filled/
