#!/bin/bash
#SBATCH --nodes=13
#SBATCH --time=60
#SBATCH --job-name="NWA12.COBALT"
#SBATCH --output=NWA12.COBALT_o.%j
#SBATCH --error=NWA12.COBALT_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
ntasks=1646

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f5/cefi/world-shared/datasets ./
popd

#
rm -rf RESTART*

#
echo "Test started:  " `date`

#
echo "run 48hrs test ..."
srun --ntasks ${ntasks} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out 2>err 


#

# Define the directories containing the files
DIR1="./"
DIR2="/gpfs/f5/cefi/proj-shared/github/ci_data/reference/main/NWA12.COBALT/"

# Define the files to compare
FILES=("ocean.stats")

# Iterate over the files
for FILE in "${FILES[@]}"; do
    # Compare the files using nccmp
    diff "${DIR1}${FILE}" "${DIR2}${FILE}" > /dev/null || { echo "Error: ${FILE} is not identical, please check! Exiting now..."; exit 1; }
done

#
echo "All restart files are identical, PASS"
echo "Test ended:  " `date`
