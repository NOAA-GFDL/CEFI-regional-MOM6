#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="NWA12.tidesonly"
#SBATCH --output=NWA12.tidesonly_o.%j
#SBATCH --error=NWA12.tidesonly_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
ntasks1=192

#
echo "Test started:  " `date`

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

#
echo "run tidesonly test ..."
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc6.intel23/ocean_only/debug/MOM6

echo "Test ended:  " `date`
