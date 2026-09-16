#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="MOM6SIS2_c6_baremetal_ifx_build"
#SBATCH --output=MOM6SIS2_c6_baremetal_ifx_build_o.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
[ -d "build" ] && rm -rf build

#
echo "Build MOM6SIS2-COBALT using container started:  " `date`

bash linux-build.bash

echo "Build MOM6SIS2-COBALT using container ended:  " `date`
