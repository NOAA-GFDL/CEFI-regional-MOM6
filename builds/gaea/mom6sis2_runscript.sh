#!/bin/sh
#SBATCH --job-name=mom6-sis2 # Job name
#SBATCH --mail-type=END,FAIL         # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=niki.zadeh@noaa.gov    # Where to send mail	
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=36
#SBATCH --time=1:00:00              # Time limit hrs:min:sec
#SBATCH --output=mom6_sis2_%j.log     # Standard output and error log
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --mail-type=fail
#SBATCH --export=NONE
#SBATCH --clusters=c4
#SBATCH --account=gfdl_f

# Sample run script to run the am4p0 experiment

# ***********************************************************************
# Modify the settings in this section to match your system's environment
# and the directory locations to the executable, input data, initial
# conditions data and work directory.

ulimit -s unlimited

# Name of the mpiexec program to use
#Make sure you have --mpi=pmi2 , otherwise n runs start in parallel!!!e
mpiexec_prog="srun --mpi=pmi2"
# Option used to specify number of MPI process to run (usually -n or -np)
mpiexec_nopt=-n
# Option used to specify number of OpenMP threads to run
mpiexec_topt=-c

src_root=/lustre/f2/dev/Niki.Zadeh
wrk_root=/lustre/f2/dev/Niki.Zadeh
# Where to perform the run
workDir=${wrk_root}/platforms/mom6/exps/mom6_sis2/OM4_1.0deg

# Location of executable (run with $mpiexec_prog)
machine=gaea
platform=intel18
target=prod
executable=${src_root}/platforms/mom6/builds/build/${machine}-${platform}/ocean_ice/${target}/MOM6SIS2

source ${src_root}/platforms/mom6/builds/${machine}/${platform}.env

## Run parameters
#total_npes is the number of cores to run on, omp_threads is the number of
# openMP threads
total_npes=72
omp_threads=1

# End of configuration section
# ***********************************************************************

# Enviornment settings for run
export KMP_STACKSIZE=512m
export NC_BLKSZ=1M
export F_UFMTENDIAN=big

# Remember CWD
initialDir=$(pwd)

# check of required programs
if ! hash tar 2> /dev/null
then
  echo "ERROR: Unable to find \`tar\` in PATH." 1>&2
  echo "ERROR: Halting script." 1>&2
fi
if ! hash ${mpiexec_prog} 2> /dev/null
then
  echo "ERROR: Unable to find \`${mpiexec_prog}\` in PATH." 1>&2
  echo "ERROR: Halting script." 1>&2
fi


# Verify work directory exists, if not create it
if [ ! -e ${workDir} ]
then
  mkdir -p ${workDir}
  if [ $? -ne 0 ]
  then
    echo "ERROR: Unable to create work directory \"${workDir}\"." 1>&2
    echo "ERROR: Halting script." 1>&2
    exit 1
  fi
elif [ ! -d ${workDir} ]
then
  echo "ERROR: Work directory \"${workDir}\" is not a directory." 1>&2
  echo "ERROR: Halting script." 1>&2
  exit 1
fi

# Check if work directory is empty, warn if not
if [ $(ls -1qA ${workDir} | wc -l) -gt 0 ]
then
  echo "NOTE: Work directory \"${workDir}\" is not empty." 1>&2
  echo "NOTE: Data in \"${workDir}\" will be overwritten." 1>&2
fi

# Enter working directory, and setup the directory
cd ${workDir}
if [ $? -ne 0 ]
then
  echo "ERROR: Unable \`cd\` into work directory \"${workDir}\"." 1>&2
  echo "ERROR: Halting script." 1>&2
  exit 1
fi

# Create RESTART directory, if it doesn't eixt.
if [ ! -e RESTART ]
then
  mkdir RESTART
  if [ $? -ne 0 ]
  then
    echo "ERROR: Unable to create directory \"${workDir}/RESTART\"." 1>&2
    echo "ERROR: Halting script." 1>&2
    exit 1
  fi
elif [ ! -d RESTART ]
then
  echo "ERROR: Directory \"${workDir}/RESTART\" is not a directory." 1>&2
  echo "ERROR: Halting script." 1>&2
  exit 1
elif [ $(ls -1qA ${workDir}/RESTART | wc -l) -gt 0 ]
then
  echo "WARNING: Directory \"${workDir}/RESTART\" is not empty." 1>&2
  echo "WARNING: Contents will be overwritten." 1>&2
fi

## Set up INPUT directory
if [ ! -e INPUT ]
then
  mkdir INPUT
  if [ $? -ne 0 ]
  then
    echo "ERROR: Unable to create directory \"${workDir}/RESTART\"." 1>&2
    echo "ERROR: Halting script." 1>&2
    exit 1
  fi
#  ln /home/data/AM4/AM4_run/INPUT/* INPUT
elif [ ! -d INPUT ]
then
  echo "ERROR: Directory \"${workDir}/INPUT\" is not a directory." 1>&2
  echo "ERROR: Halting script." 1>&2
  exit 1
elif [ $(ls -1qA ${workDir}/INPUT | wc -l) -gt 0 ]
then
  echo "NOTE: Directory \"${workDir}/INPUT\" is not empty." 1>&2
  echo "NOTE: Contents will be used." 1>&2
fi

# Run the model
echo ${mpiexec_prog} ${mpiexec_nopt} ${total_npes} ${mpiexec_topt} ${omp_threads} ${executable}
${mpiexec_prog} ${mpiexec_nopt} ${total_npes} ${mpiexec_topt} ${omp_threads} ${executable} 2>&1 | tee ${workDir}/fms.out
if [ $? -ne 0 ]
then
  echo "ERROR: Run failed." 1>&2
  echo "ERROR: Output from run in \"${workDir}/fms.out\"." 1>&2
  exit 1
fi
mv  fms.out  stdout.${machine}-${platform}.${target}.n${total_npes}
mv ocean.stats ocean.stats.${machine}-${platform}.${target}.n${total_npes}
##Combine the restarts
#cd ${workDir}/RESTART
#restart_combine.py -w ${workDir}
# Return to the initial directory
#cd ${initialDir}
#move_files.py --ncores ${total_npes} --nthreads ${omp_threads} -w ${workDir} -e aquaplanet
