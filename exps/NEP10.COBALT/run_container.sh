#!/bin/bash

#SBATCH --nodes=5
#SBATCH --time=60
#SBATCH --job-name="container_NEP10"
#SBATCH --output=NEP10.COBALT_o.%j
#SBATCH --error=NEP10.COBALT_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

echo "Model started:  " `date`

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd


#
ln -fs input.nml_24hr input.nml

#
ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_container ./RESTART
rm /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_container/*

#
export img=/gpfs/f6/ira-cefi/world-shared/container/ubuntu22.04-intel-ufs-env-v1.8.0-llvm.img
apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash ../../builds/container-scripts/externalize.sh -e container_exec -p ../../builds/docker/linux-intel.env ../../builds/build/docker-linux-intel/ocean_ice/repro/MOM6SIS2

# Avoid job errors because of filesystem synchronization delays
sync && sleep 1
srun --mpi=pmi2 --ntasks=904 --cpus-per-task=1 --export=ALL ./container_exec/MOM6SIS2

echo "Model ended:    " `date`

#
diff -q ./ocean.stats ref/docker-linux-intel-repro/ocean.stats > /dev/null || { echo "Error: ocean.stats is not identical to ref, please check! Exiting now..."; exit 1; }
echo "ocean.stats is identical to ref, PASS"

#
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_container/*
