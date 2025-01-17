#!/bin/bash
#SBATCH --partition=batch
#SBATCH --time={{ _WALLTIME  }}
#SBATCH --ntasks={{ _NPROC }}
#SBATCH --mail-type={{ _EMAIL_NOTIFACTION }}
#SBATCH --mail-user={{ _USER_EMAIL }}
#SBATCH --output={{ _LOG_PATH }}
#SBATCH --error={{ _LOG_PATH }}

# Usage: sbatch ncrcat_obc.sh <ncrcat_arg>
# This script is used to submit sbatch jobs for concatenating daily obc file on GFDL PPAN

echo "Running ncrcat_obc.sh with arguments: $@"

source $MODULESHOME/init/sh
module load miniforge
conda activate /nbhome/role.medgrp/.conda/envs/medpy311
module load cdo nco gcp

# Configuration variables
REGIONAL_GLORYS_ARCHIVE={{ _REGIONAL_GLORYS_ARCHIVE }}
BASIN_NAME={{ _BASIN_NAME }}
OUTPUT_PREFIX={{ _OUTPUT_PREFIX }}
PYTHON_SCRIPT={{ _PYTHON_SCRIPT }}


#
python "$PYTHON_SCRIPT" "$@" 
