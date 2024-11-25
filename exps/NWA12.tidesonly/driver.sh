#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="NWA12.tidesonly"
#SBATCH --output=NWA12.tidesonly_o.%j
#SBATCH --error=NWA12.tidesonly_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
ntasks1=4

#
echo "Test started:  " `date`

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

echo "Create a containerized MOM6SIS2 link ..."
export img=/gpfs/f6/ira-cefi/world-shared/container/ubuntu22.04-intel-ufs-env-v1.8.0-llvm.img
if [ -d "./container_exec" ]; then
  echo "container_exec folder exists, skip ..."
else
  echo "create container_exec folder ..."       
  apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash ../../builds/container-scripts/externalize.sh -e container_exec -p ../../builds/docker/linux-intel.env ../../builds/build/docker-linux-intel/ocean_only/repro/MOM6
fi

#
echo "run tidesonly test ..."
#srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc6.intel23/ocean_only/debug/MOM6
srun --mpi=pmi2 --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./container_exec/MOM6

echo "Test ended:  " `date`
