#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=120
#SBATCH --job-name="MOM6SIS2_container_build"
#SBATCH --output=MOM6SIS2_container_build_o.%j
#SBATCH --error=MOM6SIS2_container_build_e.%j
#SBATCH --qos=urgent
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
[ -d "build" ] && rm -rf build

#
echo "Build MOM6 using container started:  " `date`

#
export img=/gpfs/f5/cefi/world-shared/container/cefi_mom6_intel_2024.2.1.sif
apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash linux-build.bash -m docker -p linux-intel -t repro -f mom6solo

#
echo "Build MOM6 using container ended:  " `date`
