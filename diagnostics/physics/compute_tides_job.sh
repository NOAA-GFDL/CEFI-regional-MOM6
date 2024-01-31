#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --job-name=harmonic_analysis
#SBATCH --time=2880
#SBATCH --partition=batch

module load gcp
module use -a /home/ynt/modulefiles
module load conda_cefi 
conda activate setup

echo 'show current conda env'
echo $CONDA_DEFAULT_ENV

echo 'Copy files to tmp'
mkdir -p tmp
tar xvf /archive/acr/fre/NWA/2022_12_prod/NWA12_physics_2022_12_SAL_02_tidediags/gfdl.ncrc4-intel21-prod-hdf5/history/19930101.nc.tar -C ./tmp ./19930101.ocean_hour_snap.nc
gcp ../data/geography/ocean_static.nc ./tmp 

echo 'Harmonic analysis'
python compute_tides.py ./tmp/ocean_static.nc ./tmp/19930101.ocean_hour_snap.nc ./tmp/computed_tides.nc 1

echo 'Move computed_tides.nc to figures'
mv ./tmp/computed_tides.nc ./figures/

echo 'plot tide eval results'
python plot_tide_eval.py
