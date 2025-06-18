#!/bin/bash
#SBATCH --nodes=11
#SBATCH --time=120
#SBATCH --job-name="NEP10.COBALT"
#SBATCH --output=NEP10.COBALT_o.%j
#SBATCH --error=NEP10.COBALT_e.%j
#SBATCH --qos=urgent
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

# Default to not using shared project folders
USE_PROJ_SHARED=false

# Parse optional argument
for arg in "$@"; do
  case $arg in
    --use-proj-shared)
      USE_PROJ_SHARED=true
      shift
      ;;
  esac
done

#
ntasks1=2036


[[ -f input.nml ]] && rm -rf input.nml

#
echo "Test started:  " `date`

module load cray-mpich-abi
module unload cray-hdf5
#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

export img="/gpfs/f6/ira-cefi/world-shared/container/gaea_intel_2023.sif"

echo "SET MPICH_SMP_SINGLE_COPY_MODE"
export MPICH_SMP_SINGLE_COPY_MODE="NONE"

export APPTAINERENV_LD_LIBRARY_PATH=${CRAY_LD_LIBRARY_PATH}:${LD_LIBRARY_PATH}:/opt/cray/pe/lib64:/usr/lib64/libibverbs:/opt/cray/libfabric/1.20.1/lib64:/opt/cray/pals/1.4/lib:\$LD_LIBRARY_PATH

echo "SET APPTAINER_CONTAINLIBS"
export APPTAINER_CONTAINLIBS="/usr/lib64/libcxi.so,/usr/lib64/libcxi.so.1,/usr/lib64/libcxi.so.1.5.0,/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200,/usr/lib64/libnl-genl-3.so.200"

echo "SET APPTAINER_BIND"
export APPTAINER_BIND="/usr/share/libdrm,/var/spool/slurmd,/opt/cray,/opt/intel,${PWD},/etc/libibverbs.d,/usr/lib64/libibverbs,/usr/lib64/libnl3-200,${HOME}"

export FI_VERBS_PREFER_XRC=0

#
if $USE_PROJ_SHARED; then
  echo "clean RESTART folders ..."
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst/*
fi

echo "run 32x80 48hrs test ..."
ln -fs input.nml_48hr input.nml
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs ./RESTART
fi
srun --ntasks ${ntasks1} --export=ALL apptainer exec --writable-tmpfs $img ./execrunscript.sh > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 32x80 24hrs test ..."
ln -fs input.nml_24hr input.nml
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs ./RESTART
fi
srun --ntasks ${ntasks1} --export=ALL apptainer exec --writable-tmpfs $img ./execrunscript.sh > out2 2>err2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 32x80 24hrs rst test ..."
ln -fs input.nml_24hr_rst input.nml
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst ./RESTART
fi
srun --ntasks ${ntasks1} --export=ALL  apptainer exec --writable-tmpfs $img ./execrunscript.sh > out3 2>err3
mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst

# Define the directories containing the files
module load nccmp
DIR1="./RESTART_24hrs_rst"
DIR2="/gpfs/f6/ira-cefi/proj-shared/github/ci_data/reference/main/NEP10.COBALT/20250616" 

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
if $USE_PROJ_SHARED; then
  echo "clean RESTART folders now ..."
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_48hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NEP10/RESTART_24hrs_rst/*
fi

echo "Test ended:  " `date`
