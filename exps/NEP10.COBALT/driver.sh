#!/bin/bash
#SBATCH --nodes=8
#SBATCH --time=60
#SBATCH --job-name="NEP10.COBALT"
#SBATCH --output=NEP10.COBALT_o.%j
#SBATCH --error=NEP10.COBALT_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
ntasks1=904


[[ -f input.nml ]] && rm -rf input.nml

#
echo "Test started:  " `date`

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f5/cefi/world-shared/datasets ./
popd

echo "run 20x56 48hrs test ..."
ln -fs input.nml_48hr input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 20x56 24hrs test ..."
ln -fs input.nml_24hr input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out2 2>err2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 20x56 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out3 2>err3
mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst

# Define the directories containing the files
DIR1="./RESTART_24hrs_rst"
DIR2="./RESTART_48hrs" 

# Define the files to compare
FILES=("$DIR2"/MOM.res*.nc)

# Iterate over the files
for FILE in "${FILES[@]}"; do
    filename=$(basename "$FILE")
    # Compare the files using nccmp
    echo "compare ${filename}"
    nccmp -dfqS "${DIR1}/${filename}" "${DIR2}/${filename}" > /dev/null || { echo "Error: ${filename} is not identical, please check! Exiting now..."; exit 1; }
done

#
echo "All restart files are identical, PASS"
echo "Test ended:  " `date`
