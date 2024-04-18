#!/bin/bash

#
rm -rf RESTART*

#
echo "Test started:  " `date`

#
echo "run 48hrs test ..."
ln -fs input.nml_48hr input.nml
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/debug/MOM6SIS2 > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats* RESTART_48hrs

#
echo "run 24hrs test ..."
ln -fs input.nml_24hr input.nml
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/debug/MOM6SIS2 > out2 2>err2
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
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/debug/MOM6SIS2 > out3 2>err3
mv RESTART RESTART_24hrs_rst
mv ocean.stats* RESTART_24hrs_rst

# Define the directories containing the files
DIR1="RESTART_24hrs_rst/"
DIR2="RESTART_48hrs/"

if [ ! -d "$DIR1" ] || [ ! -d "$DIR2" ]; then
    echo "At least one of the restart directories does not exist."
    exit 1
fi

# Define the files to compare
FILES=("MOM.res.nc" "ice_cobalt.res.nc"  "ice_model.res.nc"  "ocean_cobalt_airsea_flux.res.nc")

# Iterate over the files
for FILE in "${FILES[@]}"; do
    # Compare the files using nccmp
    echo "Compare ${FILE}"
    rm -rf org.txt
    rm -rf ref.txt
    ncdump ${DIR1}/${FILE} > org.txt
    ncdump ${DIR2}/${FILE} > ref.txt
    diff -q ./org.txt ./ref.txt > /dev/null || { echo "Error: ${FILE} is not identical, please check! Exiting now..."; exit 1; }
done

#
echo "All restart files are identical, PASS"
echo "Test ended:  " `date`
