#!/bin/bash
#SBATCH --job-name=make_mom6_obc
#SBATCH --constraint=bigmem
#SBATCH --partition=analysis
#SBATCH --time=00:20:00
#SBATCH --ntasks=1

# Usage: sbatch submit_python_make_obc_day.sh <PYTHON_SCRIPT>  <YEAR> <MONTH> <DAY> <OUTPUT_DIR>
# This script is used to ERA5 no-leap years with daily means or 3hrPt on GFDL PPAN
source $MODULESHOME/init/sh
module load miniforge
module load nco 
conda activate /net3/e1n/miniconda3/envs/mom6 

cd $TMPDIR

python_script=$1
year=$2
monstr=$3
daystr=$4
outdir=$5

#echo $python_script $year $monstr $daystr $outdir
python $python_script $year $monstr $daystr $outdir


