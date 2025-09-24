#!/bin/bash 
export BACKUP_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
# Set up spack loads
#. /spack/share/spack/setup-env.sh
# Load spack packages
#spack load libyaml
#spack load netcdf-fortran@4.5.4
#spack load hdf5@1.14.0
. /opt/intel/oneapi/setvars.sh
export LD_LIBRARY_PATH=/opt/views/view/lib:$LD_LIBRARY_PATH
export LIBRARY_PATH=/opt/views/view/lib:$LIBRARY_PATH
export PATH=$PATH:/opt/views/view/bin
export LD_LIBRARY_PATH=$BACKUP_LD_LIBRARY_PATH:$LD_LIBRARY_PATH
# Run executable
../../builds/build/docker-linux-intel/ocean_ice/repro/MOM6SIS2
