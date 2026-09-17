#!/bin/bash
#SBATCH --nodes=9
#SBATCH --time=120
#SBATCH --job-name="NWA12.COBALT"
#SBATCH --output=NWA12.COBALT_o.%j
#SBATCH --qos=normal
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
ntasks1=1600
ntasks2=900

#
echo "Test started:  " `date`
source $MODULESHOME/init/bash
module load cray-mpich-abi
module unload cray-hdf5

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

# UMW 05/27/2026 NOTE: For some reason, symlinking the atmosphere forcing
# files to INPUT causes slow file reads in the atmos loop. This was a
# bigger issue in the NEP than the NWA ( with symlinks, NWA runtime was ~800s)
# but copying this logic here anyways
# TODO: Ideally, we should copy over the restart files too to speed up
# initialization, but holding off on that for now given how large they are.
echo "Copying atmosphere forcing to INPUT dir"
pushd INPUT
for f in ERA5_* ; do
    if [ -L ${f} ] ; then
        echo "Copying ${f}"
        # readlink gets the full path to the symlinked data,
        # cp --remove-destination removes the symlink + copies over the actual data
        cp --remove-destination "$(readlink ${f})" ${f}
    else
        echo "${f} is already copied over, skipping copy"
    fi
done
popd

echo "SET MPICH_SMP_SINGLE_COPY_MODE"
export MPICH_SMP_SINGLE_COPY_MODE="NONE"


export FI_VERBS_PREFER_XRC=0

#
if $USE_PROJ_SHARED; then
  echo "clean RESTART folders ..."
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_48hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst/*
fi

echo "run 40x40 48hrs test ..."
ln -fs input.nml_48hr input.nml
pushd INPUT/
ln -fs MOM_layout_40 MOM_layout
ln -fs MOM_layout_40 SIS_layout
popd
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_48hrs ./RESTART
fi
srun --ntasks ${ntasks1} ../../builds/build/gaea-ncrc6.intel25/ocean_ice/repro/MOM6SIS2 > out1 2>err1
STATUS=$?
if [ ${STATUS} -ne 0 ] then
    echo "ERROR: 48hrs test returned ${STATUS}."
    exit ${STATUS}
fi
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

#
echo "run 40x40 24hrs test ..."
ln -fs input.nml_24hr input.nml
if $USE_PROJ_SHARED; then
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs ./RESTART
fi
srun --ntasks ${ntasks1} ../../builds/build/gaea-ncrc6.intel25/ocean_ice/repro/MOM6SIS2 > out2 2>err2
STATUS=$?
if [ ${STATUS} -ne 0 ] then
    echo "ERROR: 24hrs test returned ${STATUS}."
    exit ${STATUS}
fi
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
  ln -fs /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst ./RESTART
fi
srun --ntasks ${ntasks2} ../../builds/build/gaea-ncrc6.intel25/ocean_ice/repro/MOM6SIS2 > out3 2>err3
STATUS=$?
if [ ${STATUS} -ne 0 ] then
    echo "ERROR: 24hrs_rst test returned ${STATUS}."
    exit ${STATUS}
fi

mv RESTART RESTART_24hrs_rst
mv ocean.stats RESTART_24hrs_rst


# Define the directories containing the files
DIR1="./RESTART_24hrs_rst"
DIR2="/gpfs/f6/ira-cefi/proj-shared/github/ci_data/reference/main/NWA12.COBALT/20260820_ifx/"

# Check if gnu parallel is available
if command -v parallel >/dev/null 2>&1 ; then
    CMD="parallel"
# Othwerise, use predownloaded executable
else
    if [ -x "/gpfs/f6/ira-cefi/world-shared/gnu_parallel/parallel" ]; then
      CMD="/gpfs/f6/ira-cefi/world-shared/gnu_parallel/parallel"
    elif [ -x "/gpfs/f6/ira-cefi/world-shared/gnu_parallel/parallel" ]; then
      CMD="/gpfs/f6/ira-cefi/world-shared/gnu_parallel/parallel"
    else
      echo "Error: gnu parallel is not available, skipping Restart reproducibility test"
      exit 1
    fi
fi

# Compare restarts in parallel
module load nccmp
find ${DIR1} -type f -name "*.nc" -printf "%P\n" | \
${CMD} --halt now,fail=1 "nccmp -dfs -c 10 ${DIR1}/{} ${DIR2}/{}" \
&& echo  "All restart files are identical, PASS"

#
if $USE_PROJ_SHARED; then
  echo "clean RESTART folders now ..."
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_48hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs/*
  rm -rf /gpfs/f6/ira-cefi/proj-shared/github/tmp/NWA12/RESTART_24hrs_rst/*
fi

echo "Test ended:  " `date`
