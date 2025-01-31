#!/bin/bash
#SBATCH --nodes=5
#SBATCH --time=120
#SBATCH --job-name="NEP10.COBALT"
#SBATCH --output=NEP10.COBALT_o.%j
#SBATCH --error=NEP10.COBALT_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
ntasks1=904


[[ -f input.nml ]] && rm -rf input.nml

#
echo "Test started:  " `date`

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

#
echo "Create a containerized MOM6SIS2 link ..."
export img=/gpfs/f6/ira-cefi/world-shared/container/ubuntu22.04-intel-ufs-env-v1.8.0-llvm.img
if [ -d "./container_exec" ]; then
  echo "container_exec folder exists, skip ..."
else 
  echo "create container_exec folder ..."       
  apptainer exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng $img bash ../../builds/container-scripts/externalize.sh -e container_exec -p ../../builds/docker/linux-intel.env ../../builds/build/docker-linux-intel/ocean_ice/repro/MOM6SIS2
fi

#
echo "clean RESTART folders ..."
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs/*
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs/*
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst/*

echo "run 20x56 48hrs test ..."
ln -fs input.nml_48hr input.nml
ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs ./RESTART
srun --mpi=pmi2 --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./container_exec/MOM6SIS2 > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 20x56 24hrs test ..."
ln -fs input.nml_24hr input.nml
ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs ./RESTART
srun --mpi=pmi2 --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./container_exec/MOM6SIS2 > out2 2>err2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 20x56 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst ./RESTART
srun --mpi=pmi2 --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./container_exec/MOM6SIS2 > out3 2>err3
mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst

# Define the directories containing the files
module load nccmp
DIR1="./RESTART_24hrs_rst"
DIR2="/gpfs/f6/ira-cefi/proj-shared/github/ci_data/reference/main/NEP10.COBALT/20250131" 

# Define the files to compare
FILES=("$DIR2"/MOM.res*.nc)

# Iterate over the files
for FILE in "${FILES[@]}"; do
    filename=$(basename "$FILE")
    # Compare the files using nccmp
    echo "compare ${filename}"
    nccmp -dfqS "${DIR1}/${filename}" "${DIR2}/${filename}" > /dev/null || { echo "Error: ${filename} is not identical, please check! Exiting now..."; exit 1; }
done

#
echo "All restart files are identical, PASS"

#
echo "clean RESTART folders now ..."
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs/*
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs/*
rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst/*

echo "Test ended:  " `date`
