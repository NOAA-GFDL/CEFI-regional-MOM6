#!/bin/bash

#SBATCH --nodes=5
#SBATCH --time=60
#SBATCH --job-name="OM4p25.COBALT"
#SBATCH --output=OM4p25.COBALT_o.%j
#SBATCH --error=OM4p25.COBALT_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

# Avoid job errors because of filesystem synchronization delays
sync && sleep 1

srun --ntasks=900 --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc6.intel23/ocean_ice/repro/MOM6SIS2 
