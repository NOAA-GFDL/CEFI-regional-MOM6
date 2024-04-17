#!/bin/bash
#SBATCH --nodes=13
#SBATCH --time=120
#SBATCH --job-name="NWA12.COBALT"
#SBATCH --output=NWA12.COBALT_o.%j
#SBATCH --error=NWA12.COBALT_e.%j
#SBATCH --qos=normal
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
echo "run 24hrs test ..."
ln -fs input.nml_24hr input.nml
srun --ntasks ${ntasks} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out 2>err
mv RESTART RESTART_24hrs
mv ocean.stats* RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
srun --ntasks ${ntasks} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out2 2>err2
mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst

#
#echo "run 48hrs test ..."
#srun --ntasks ${ntasks} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc5.intel23/ocean_ice/repro/MOM6SIS2 > out 2>err 


# Define the directories containing the files
DIR1="./RESTART_24hrs_rst"
DIR2="/gpfs/f5/cefi/proj-shared/github/ci_data/reference/main/NWA12.COBALT/RESTART"

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
