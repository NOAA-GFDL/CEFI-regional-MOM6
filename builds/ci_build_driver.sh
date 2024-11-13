#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=360
#SBATCH --job-name="MOM6SIS2_container_build"
#SBATCH --output=MOM6SIS2_container_build_o.%j
#SBATCH --error=MOM6SIS2_container_build_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
[ -d "build" ] && rm -rf build

#
echo "Build MOM6SIS2-COBALT using container started:  " `date`

#
export img=/gpfs/f6/ira-cefi/world-shared/container/ubuntu22.04-intel-ufs-env-v1.8.0-llvm.img
apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash linux-build.bash -m docker -p linux-intel -t repro -f mom6sis2

#
echo "Build MOM6SIS2-COBALT using container ended:  " `date`
