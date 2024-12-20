#!/bin/bash

# Load required modules and environments
source $MODULESHOME/init/sh
module load miniforge
conda activate /nbhome/role.medgrp/.conda/envs/uwtools || { echo "Error activating conda environment. Exiting."; exit 1; }

set -eu

# Helper functions
print_usage() {
    echo "Usage: $0 START_DATE END_DATE [--ncrcat] [--adjust-timestamps]"
    echo "  START_DATE and END_DATE must be in YYYY-MM-DD format."
    echo "  --ncrcat: Enable ncrcat step (skips subset, fill, and submit_python steps)."
    echo "  --adjust-timestamps: Adjust timestamps during ncrcat step."
}

validate_date_format() {
    if [[ ! "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "Error: Date $1 must be in YYYY-MM-DD format."
        exit 1
    fi
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Default options
DO_NCRCAT=false
ADJUST_TIMESTAMPS=false
PYTHON_SCRIPT="../write_glorys_boundary_daily.py"

# Parse arguments
START_DATE="$1"
END_DATE="$2"
shift 2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ncrcat)
            DO_NCRCAT=true
            ;;
        --adjust-timestamps)
            ADJUST_TIMESTAMPS=true
            ;;
        *)
            echo "Unknown argument: $1"
            print_usage
            exit 1
            ;;
    esac
    shift
done

validate_date_format "$START_DATE"
validate_date_format "$END_DATE"


start_date_epoch=$(date -d "$START_DATE" +%s)
end_date_epoch=$(date -d "$END_DATE" +%s)
if [[ $start_date_epoch -gt $end_date_epoch ]]; then
    log_message "Error: START_DATE ($START_DATE) must not be after END_DATE ($END_DATE). Exiting."
    exit 1
fi

# Ensure --adjust-timestamps is only used with --ncrcat
if $ADJUST_TIMESTAMPS && ! $DO_NCRCAT; then
    echo "Error: --adjust-timestamps can only be used with --ncrcat."
    exit 1
fi

# Warn user when --ncrcat is enabled
if $DO_NCRCAT; then
    log_message "WARNING: --ncrcat is enabled. The script will SKIP subset, fill, and submit_python steps."
    log_message "Ensure that all daily outputs already exist for the specified date range."
fi

# Prepare directories
CURRENT_DATE=$(date +%Y-%m-%d-%H-%M)
mkdir -p ./log/$CURRENT_DATE ./outputs scripts

# Define user configurations
log_message "Generating config.yaml..."
cat <<EOF > config.yaml
_WALLTIME: "1440"
_NPROC: "1"
_EMAIL_NOTIFACTION: "fail"
_USER_EMAIL: "$USER@noaa.gov"
_LOG_PATH: "./log/$CURRENT_DATE/%x.o%j"
_UDA_GLORYS_DIR: "/uda/Global_Ocean_Physics_Reanalysis/global/daily"
_UDA_GLORYS_FILENAME: "mercatorglorys12v1_gl12_mean"
_REGIONAL_GLORYS_ARCHIVE: "/archive/$USER/datasets/glorys"
_BASIN_NAME: "NWA12"
_OUTPUT_PREFIX: "GLORYS"
_VARS: "thetao so uo vo zos"
_LON_MIN: "-100.0"
_LON_MAX: "-30.0"
_LAT_MIN: "5.0"
_LAT_MAX: "60.0"
_PYTHON_SCRIPT: "$PYTHON_SCRIPT"
first_date: "$START_DATE"
last_date: "$END_DATE"
glorys_dir: "/archive/$USER/datasets/glorys/NWA12/filled"
output_dir: "./outputs"
hgrid: './ocean_hgrid.nc'
ncrcat_names:
  - 'thetao'
  - 'so'
  - 'zos'
  - 'uv'
segments:
  - id: 1
    border: 'south'
  - id: 2
    border: 'north'
  - id: 3
    border: 'east'
variables:
  - 'thetao'
  - 'so'
  - 'zos'
  - 'uv'
EOF


log_message "Preparing scripts directory..."
[[ -d scripts ]] || mkdir scripts
for template in subset_glorys fill_glorys submit_python_make_obc_day ncrcat_obc; do
    rm -f scripts/${template}.sh
    uw template render --input-file template/${template}_template.sh \
                      --values-file config.yaml \
                      --output-file scripts/${template}.sh || { log_message "Error rendering ${template}. Exiting."; exit 1; }
done

# Skip main steps if --ncrcat is enabled
if ! $DO_NCRCAT; then

    # Submit jobs
    current_date_epoch=$start_date_epoch
    job_ids=()

    while [[ $current_date_epoch -le $end_date_epoch ]]; do
        current_date=$(date -d "@$current_date_epoch" +%Y-%m-%d)
        year=$(date -d "$current_date" +%Y)
        month=$(date -d "$current_date" +%m)
        day=$(date -d "$current_date" +%d)

        log_message "Submitting subset job for $current_date..."
        subset_job_id=$(sbatch --job-name="glorys_subset_${year}_${month}_${day}" \
                              scripts/subset_glorys.sh $year $month $day | awk '{print $4}')

        log_message "Submitting fill_nan job for $current_date..."
        fill_job_id=$(sbatch --dependency=afterok:$subset_job_id \
                              --job-name="glorys_fill_${year}_${month}_${day}" \
                              scripts/fill_glorys.sh $year $month $day | awk '{print $4}')

        log_message "Submitting Python job for $current_date..."
        python_job_id=$(sbatch --dependency=afterok:$fill_job_id \
                                --job-name="python_make_obc_day_${year}_${month}_${day}" \
                                scripts/submit_python_make_obc_day.sh $year $month $day | awk '{print $4}')

        job_ids+=($python_job_id)
        current_date_epoch=$((current_date_epoch + 86400))
    done
fi

# Optional ncrcat step
if $DO_NCRCAT; then
    log_message "Submitting ncrcat job..."
    dependency_str=$(IFS=,; echo "${job_ids[*]:-}")
    if $ADJUST_TIMESTAMPS; then
        sbatch --job-name="obc_ncrcat" scripts/ncrcat_obc.sh --config config.yaml --ncrcat_years --adjust_timestamps
    else
        sbatch --job-name="obc_ncrcat" scripts/ncrcat_obc.sh --config config.yaml --ncrcat_years
    fi
fi

log_message "Workflow completed."
