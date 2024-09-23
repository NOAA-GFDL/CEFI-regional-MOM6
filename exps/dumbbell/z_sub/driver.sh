#!/bin/bash

if [ -f ocean.stats ] ; then
    rm ocean.stats ocean.stats.nc
fi

#
echo "First run whole domain case ..."
pushd ../z
../../../builds/build/docker-linux-gnu/ocean_ice/debug/MOM6SIS2

echo "Extract and generate BCs for subdomain run"
bash extract_obc.bash  
python3 extract_obc.py 
popd

#
echo "prepare obc files for age tracer"
cp ../z/west.nc obgc_obc.nc
ncks -A ../z/east.nc obgc_obc.nc

#
echo "Run Sub domian"
../../../builds/build/docker-linux-gnu/ocean_ice/debug/MOM6SIS2
cat ./ocean.stats
cat ./ocean.stats.gnu
diff -q ./ocean.stats ./ocean.stats.gnu > /dev/null || { echo "Error: ocean.stats is not identical, please check! Exiting now..."; exit 1; }

# check err
ln -fs 00010101.prog.nc prog.nc
python3 rms_errors.py ../z_sub
cat ./err.txt
cat ./err.txt.ref
diff -q ./err.txt ./err.txt.ref > /dev/null || { echo "Error: subset error is not identical, please check! Exiting now..."; exit 1; }
