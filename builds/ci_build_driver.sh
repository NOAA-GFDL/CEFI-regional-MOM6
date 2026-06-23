#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="MOM6SIS2_container_build"
#SBATCH --output=MOM6SIS2_container_build_o.%j
#SBATCH --error=MOM6SIS2_container_build_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=gfdl_med

# 1. Set the default state (Clean by default)
CLEAN_UP=true

# 2. Parse the options
# 'n' stands for 'no-clean'. Note: getopts handles single-letter flags best.
while getopts "n" opt; do
  case $opt in
    n)
      CLEAN_UP=false
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

#
if [ "$CLEAN_UP" = true ]; then
    echo "Cleaning up build directory..."
    [ -d "build" ] && rm -rf build
else
    echo "Skipping cleanup (--no-clean active)."
fi

#
echo "Build MOM6SIS2-COBALT using container started:  " `date`

#
#export img=/gpfs/f6/ira-cefi/world-shared/container/cefi_mom6_intel_2024.2.1.sif
#apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash linux-build.bash -m docker -p linux-intel -t repro -f mom6sis2

export img=/gpfs/f5/cefi/world-shared/container/gaea_intel_2023.2.0.sif

if [ "$USER" = "role.medgrp" ]; then
    apptainer exec \
        -B /gpfs \
	-B /autofs/ncrc-svm1_home1/role.medgrp:/autofs/ncrc-svm1_home1/role.medgrp \
        -B $HOME:$HOME \
        "$img" \
        bash linux-build.bash -m docker -p linux-intel -t repro -f mom6sis2
else
    apptainer exec \
        -B /gpfs \
        -B $HOME:$HOME \
        "$img" \
        bash linux-build.bash -m docker -p linux-intel -t repro -f mom6sis2
fi

#
echo "Build MOM6SIS2-COBALT using container ended:  " `date`
