#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="MOM6SIS2_build"
#SBATCH --output=MOM6SIS2_build_o.%j
#SBATCH --error=MOM6SIS2_build_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#

#
[ -d "build" ] && rm -rf build

#
echo "Build started:  " `date`

#
./linux-build.bash -m gaea -p ncrc5.intel23 -t repro -f mom6sis2

#
echo "Build ended:  " `date`
