#!/bin/bash

#
rm -rf RESTART*

#
echo "Test started:  " `date`

#
echo "run 48hrs test ..."
ln -fs input.nml_48hr input.nml
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/prod/MOM6SIS2 
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 24 1hrs test ..."
ln -fs input.nml_24hr input.nml
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/prod/MOM6SIS2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
mpirun --allow-run-as-root -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/prod/MOM6SIS2
mv RESTART RESTART_24hrs_rst
mv ocean.stats* RESTART_24hrs_rst

# Define the directories containing the files
DIR1="RESTART_24hrs_rst/"
DIR2="RESTART_48hrs/"

if [ ! -d "$DIR1" ] || [ ! -d "$DIR2" ]; then
    echo "At least one of the restart directories does not exist."
    exit 1
fi

diff -q $DIR1/ocean.stats $DIR2/ocean.stats > /dev/null || { echo "Error: ocean.stats are not identical across restart! Exiting now..."; exit 1; }

#
echo "Test ended:  " `date`
