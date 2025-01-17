#!/bin/bash
#SBATCH --partition=batch
#SBATCH --time={{ _WALLTIME }}
#SBATCH --ntasks={{ _NPROC }}
#SBATCH --mail-type={{ _EMAIL_NOTIFACTION }}
#SBATCH --mail-user={{ _USER_EMAIL }}
#SBATCH --output={{ _LOG_PATH }}
#SBATCH --error={{ _LOG_PATH }}

# Usage: sbatch subset_glorys.sh <YEAR> <MONTH> <DAY>

# Load required modules
module load cdo
module load nco/5.0.1
module load gcp

# Input arguments
year=$1
month=$2
day=$3

# Configuration variables
UDA_GLORYS_DIR={{ _UDA_GLORYS_DIR }}
UDA_GLORYS_FILENAME={{ _UDA_GLORYS_FILENAME }}
REGIONAL_GLORYS_ARCHIVE={{ _REGIONAL_GLORYS_ARCHIVE }}
BASIN_NAME={{ _BASIN_NAME }}
OUTPUT_PREFIX={{ _OUTPUT_PREFIX }}
LON_MIN={{ _LON_MIN }}
LON_MAX={{ _LON_MAX }}
LAT_MIN={{ _LAT_MIN }}
LAT_MAX={{ _LAT_MAX }}
VARS=({{ _VARS }})

# Derived variables
apath=${REGIONAL_GLORYS_ARCHIVE}/${BASIN_NAME}
tmpdir="$TMPDIR/subset_glorys_${year}_${month}_${day}"

# Create required directories
setup_directories() {
    mkdir -p "$apath"
    mkdir -p "$tmpdir"
}

# Cleanup temporary files
cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$tmpdir"
}
trap cleanup EXIT

# Check if output file exists
check_output_exists() {
    local output_file=$1
    if [[ -f $output_file ]]; then
        echo "Output file already exists: $output_file. Skipping processing."
        return 0
    fi
    return 1
}

# Process a single variable
process_variable() {
    local var=$1
    local output_file="$apath/${OUTPUT_PREFIX}_${var}_${year}-${month}-${day}.nc"

    # Skip processing if output file exists
    check_output_exists "$output_file" && return

    local var_dir="$tmpdir/${var}_${year}_${month}_${day}"
    mkdir -p "$var_dir"

    local filename_pattern="${UDA_GLORYS_DIR}/${var}/${year}/${var}_${UDA_GLORYS_FILENAME}_${year}${month}${day}*.nc"
    local processed=false

    for filename in $filename_pattern; do
        if [[ -f $filename ]]; then
            echo "Processing file: $filename"
            local subset_file="$var_dir/${var}_subset.nc"

            # Subset and adjust the file
            if ! ncks -d longitude,${LON_MIN},${LON_MAX} -d latitude,${LAT_MIN},${LAT_MAX} --mk_rec_dmn time "$filename" "$subset_file"; then
                echo "Error: ncks failed for $filename"
                exit 1
            fi

            if ! cdo -setreftime,1993-01-01,00:00:00,1day "$subset_file" "$output_file"; then
                echo "Error: cdo failed for $subset_file"
                exit 1
            fi

            echo "Finished processing variable: $var for ${year}-${month}-${day}"
            processed=true
            break
        fi
    done

    if [[ $processed == false ]]; then
        echo "Error: No files matched the pattern: $filename_pattern"
        exit 1
    fi

    # Verify the output file
    if [[ -f $output_file ]]; then
        echo "Output file successfully created: $output_file"
    else
        echo "Error: Failed to create output file: $output_file"
        exit 1
    fi
}

# Main processing loop
main() {
    setup_directories

    for var in "${VARS[@]}"; do
        process_variable "$var"
    done

    echo "All variables processed for ${year}-${month}-${day}"
}

main
