#!/bin/bash
#SBATCH --nodes=13
#SBATCH --time=55
#SBATCH --job-name="NWA12.COBALT"
#SBATCH --output=NWA12.COBALT_o.%j
#SBATCH --error=NWA12.COBALT_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=gfdl_med

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
ntasks1=1600
ntasks2=900

#
echo "Test started:  " `date`
source ~/.bashrc
echo $TMOUT
source $MODULESHOME/init/bash
module load cray-mpich-abi
module unload cray-hdf5
module list

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f5/gfdl_med/world-shared/datasets ./
popd

export img="/gpfs/f5/cefi/world-shared/container/gaea_intel_2023.2.0.sif"

echo "SET MPICH_SMP_SINGLE_COPY_MODE"
export MPICH_SMP_SINGLE_COPY_MODE="NONE"

export APPTAINERENV_LD_LIBRARY_PATH=${CRAY_LD_LIBRARY_PATH}:${LD_LIBRARY_PATH}:/opt/cray/pe/lib64:/usr/lib64/libibverbs:/opt/cray/libfabric/1.20.1/lib64:/opt/cray/pals/1.4/lib:\$LD_LIBRARY_PATH

echo "SET APPTAINER_CONTAINLIBS"
export APPTAINER_CONTAINLIBS="/opt/cray/pals/1.6/lib/libpals.so.0,/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200,/usr/lib64/libnl-genl-3.so.200"
#export APPTAINER_CONTAINLIBS="/usr/lib64/libcxi.so,/usr/lib64/libcxi.so.1,/usr/lib64/libcxi.so.1.5.0,/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200,/usr/lib64/libnl-genl-3.so.200"

echo "SET APPTAINER_BIND"
export APPTAINER_BIND="/usr/share/libdrm,/var/spool/slurmd,/opt/cray,/opt/intel,${PWD},/etc/libibverbs.d,/usr/lib64/libibverbs,/usr/lib64/libnl3-200,${HOME}"

export FI_VERBS_PREFER_XRC=0

#
if $USE_PROJ_SHARED; then
  echo "clean RESTART folders ..."
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_48hrs/*
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs/*
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst/*
fi

echo "run 40x40 48hrs test ..."
ln -fs input.nml_48hr input.nml
pushd INPUT/
ln -fs MOM_layout_40 MOM_layout
ln -fs MOM_layout_40 SIS_layout
popd
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_48hrs ./RESTART
fi

# Print info about environment
echo -e "\n\n WORKING WITH THE FOLLOWING ENV\n"
env
echo -e "\n\n ENV OVER\n"

srun --ntasks ${ntasks1} --export=ALL apptainer exec -B /gpfs:/gpfs -B $HOME:$HOME -B /autofs/ncrc-svm1_home1/role.medgrp:/autofs/ncrc-svm1_home1/role.medgrp  --writable-tmpfs $img bash ./execrunscript.sh > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 40x40 24hrs test ..."
ln -fs input.nml_24hr input.nml
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs ./RESTART
fi
srun --ntasks ${ntasks1} --export=ALL apptainer exec -B /gpfs:/gpfs -B $HOME:$HOME -B /autofs/ncrc-svm1_home1/role.medgrp:/autofs/ncrc-svm1_home1/role.medgrp --writable-tmpfs $img bash ./execrunscript.sh > out2 2>err2
mv RESTART RESTART_24hrs
mv ocean.stats RESTART_24hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_24hrs/* ./
popd

#
echo "run 30x30 24hrs rst test ..."
#ln -fs input.nml_24hr_rst input.nml
pushd INPUT/
ln -fs MOM_layout_30 MOM_layout
ln -fs MOM_layout_30 SIS_layout
popd
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst ./RESTART
fi
srun --ntasks ${ntasks2} --export=ALL apptainer exec -B /gpfs:/gpfs -B $HOME:$HOME -B /autofs/ncrc-svm1_home1/role.medgrp:/autofs/ncrc-svm1_home1/role.medgrp --writable-tmpfs $img bash ./execrunscript.sh > out3 2>err3
mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst


# Define the directories containing the files
module load nccmp
DIR1="./RESTART_24hrs_rst"
DIR2="/gpfs/f5/gfdl_med/proj-shared/github/ci_data/reference/main/NWA12.COBALT/20250625"

# Define the files to compare
FILES=("$DIR2"/*.nc)

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
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_48hrs/*
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs/*
  rm -rf /gpfs/f5/gfdl_med/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst/*
fi

echo "Test ended:  " `date`
