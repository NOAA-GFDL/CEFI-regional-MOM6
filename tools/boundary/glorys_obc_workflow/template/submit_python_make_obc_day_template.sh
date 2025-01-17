#!/bin/bash
#SBATCH --partition=batch
#SBATCH --time={{ _WALLTIME }}
#SBATCH --ntasks={{ _NPROC }}
#SBATCH --mail-type={{ _EMAIL_NOTIFACTION }}
#SBATCH --mail-user={{ _USER_EMAIL }}
#SBATCH --output={{ _LOG_PATH }}
#SBATCH --error={{ _LOG_PATH }}

# Usage: sbatch submit_python_make_obc_day.sh <YEAR> <MONTH> <DAY>
# This script is used to submit sbatch jobs for daily GLORYS OBC file generation on GFDL PPAN

# Setup environment
setup_environment() {
    source $MODULESHOME/init/sh
    module load miniforge
    conda activate /nbhome/role.medgrp/.conda/envs/medpy311
    module load cdo nco gcp
}

# Check if the combined file exists
check_combined_file() {
    local combined_file=$1
    if [[ ! -f "$combined_file" ]]; then
        echo "Error: Combined file not found: $combined_file"
        return 1
    fi
    return 0
}

# dmget the combined file from archive
dmget_combined_file() {
    local combined_file=$1
    echo "dmget combined file: $combined_file"
    dmget "$combined_file" || { echo "Error: Failed to dmget combined file: $combined_file"; return 1; }
    return 0
}

# Run the Python script for daily OBC file generation
run_python_script() {
    local year=$1
    local month=$2
    local day=$3
    local python_script=$4

    echo "Creating daily OBC file: ${year}-${month}-${day}"
    python "$python_script" --config config.yaml --year "$year" --month "$month" --day "$day" || { echo "Error: Python script failed for ${year}-${month}-${day}"; return 1; }
    return 0
}

# Main function
main() {
    # Input arguments
    year=$1
    month=$2
    day=$3

    # Configuration variables
    REGIONAL_GLORYS_ARCHIVE={{ _REGIONAL_GLORYS_ARCHIVE }}
    BASIN_NAME={{ _BASIN_NAME }}
    OUTPUT_PREFIX={{ _OUTPUT_PREFIX }}
    PYTHON_SCRIPT={{ _PYTHON_SCRIPT }}

    # Derived paths
    glorys_arch_dir="${REGIONAL_GLORYS_ARCHIVE}/${BASIN_NAME}"
    filled_dir="$glorys_arch_dir/filled"
    combined_file="$filled_dir/${OUTPUT_PREFIX}_${year}-${month}-${day}.nc"

    # Setup environment
    setup_environment

    # Check if the combined file exists
    check_combined_file "$combined_file" || exit 1

    # dmget the combined file from the archive
    dmget_combined_file "$combined_file" || exit 1

    # Run the Python script to create the daily OBC file
    run_python_script "$year" "$month" "$day" "$PYTHON_SCRIPT" || exit 1

    echo "Daily OBC file generation completed for ${year}-${month}-${day}"
}

# Execute the main function
main "$@"
