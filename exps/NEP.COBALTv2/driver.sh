#!/bin/bash
#SBATCH --nodes=8
#SBATCH --time=60
#SBATCH --job-name="NEP10.COBALTv2"
#SBATCH --output=NEP10.COBALTv2_o.%j
#SBATCH --error=NEP10.COBALTv2_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
ntasks1=904


# copy MOM_override
rm -rf RESTART*
[[ -f input.nml ]] && rm -rf input.nml

#
echo "Test started:  " `date`

#echo "run 20x56 48hrs test ..."
ln -fs input.nml_48hr input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./MOM6SIS2  > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 20x56 24hrs test ..."
ln -fs input.nml_24hr input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./MOM6SIS2 > out2 2>err2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/MOM.res*.nc ./
ln -fs ../RESTART_24hrs/ice_cobalt.res.nc ./
ln -fs ../RESTART_24hrs/ice_model.res.nc ./
ln -fs ../RESTART_24hrs/ocean_cobalt_airsea_flux.res.nc ./
ln -fs ../RESTART_24hrs/coupler.res ./
popd

#
echo "run 20x56 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./MOM6SIS2 > out3 2>err3
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
