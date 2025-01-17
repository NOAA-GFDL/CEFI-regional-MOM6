#!/bin/bash
#SBATCH --partition=batch
#SBATCH --time={{ _WALLTIME }}
#SBATCH --ntasks={{ _NPROC }}
#SBATCH --mail-type={{ _EMAIL_NOTIFACTION }}
#SBATCH --mail-user={{ _USER_EMAIL }}
#SBATCH --output={{ _LOG_PATH }}
#SBATCH --error={{ _LOG_PATH }}

# Usage: sbatch fill_glorys.sh <YEAR> <MONTH> <DAY>
# This script is used to fill the GLORYS reanalysis data on GFDL PPAN

module load cdo
module load nco
module load gcp

# Input arguments
year=$1
month=$2
day=$3

# Configuration variables
REGIONAL_GLORYS_ARCHIVE={{ _REGIONAL_GLORYS_ARCHIVE }}
BASIN_NAME={{ _BASIN_NAME }}
OUTPUT_PREFIX={{ _OUTPUT_PREFIX }}

# Derived paths
glorys_arch_dir="${REGIONAL_GLORYS_ARCHIVE}/${BASIN_NAME}"
filled_dir="$glorys_arch_dir/filled"
tmpdir="$TMPDIR/fill_glorys_${year}_${month}_${day}"
combined_file="$filled_dir/${OUTPUT_PREFIX}_${year}-${month}-${day}.nc"

# Function to set up required directories
setup_directories() {
    mkdir -p "$filled_dir"
    mkdir -p "$tmpdir/filled"
}

# Function to clean up temporary files
cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$tmpdir"
}
trap cleanup EXIT

# Function to check if file exists and handle errors
check_file_exists() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        echo "Error: File does not exist: $file. Skipping."
        return 1
    fi
    return 0
}

# Function to dmget and check if files are available
dmget_files() {
    dmget $glorys_arch_dir/${OUTPUT_PREFIX}_*_${year}-${month}-${day}.nc
    for file in $glorys_arch_dir/${OUTPUT_PREFIX}_*_${year}-${month}-${day}.nc; do
        check_file_exists "$file" || return 1
    done
}

# Function to process and fill a single file
process_file() {
    local file=$1
    local filename="${file##*/}"
    local output_file="$filled_dir/$filename"

    echo "Processing file: $file"

    # Skip `cdo` part if filled file already exists
    if [[ -f "$output_file" ]]; then
        echo "Filled file already exists: $output_file. Skipping filling process."
        return 0
    fi

    # Copy file to TMPDIR for processing
    gcp "$file" "$tmpdir/"
    local input_file="$tmpdir/$filename"

    # Process: Fill missing data and compress
    local filled_tmpfile="$tmpdir/filled/$filename"
    cdo setmisstonn "$input_file" "$filled_tmpfile" || { echo "Error: Failed to fill missing data for $filename."; return 1; }
    
    ncks -4 -L 5 "$filled_tmpfile" -O "$filled_tmpfile" || { echo "Error: Failed to compress filled file for $filename."; return 1; }

    # Copy filled file to the final directory
    gcp "$filled_tmpfile" "$output_file" || { echo "Error: Failed to move filled file to $filled_dir."; return 1; }

    return 0
}

# Function to initialize the combined file
initialize_combined_file() {
    local output_file=$1
    echo "Initializing combined file with: $output_file"
    cp "$output_file" "$combined_file" || { echo "Error: Failed to initialize combined file."; return 1; }
    return 0
}

# Function to append variables to the combined file
append_to_combined_file() {
    local output_file=$1
    echo "Appending variables from $output_file to $combined_file"
    ncks -A "$output_file" "$combined_file" || { echo "Error: Failed to append variables from $output_file to $combined_file."; return 1; }
    return 0
}

# Main processing loop
main() {
    setup_directories

    # dmget files from archive
    dmget_files || exit 1

    # Remove the combined file if it exists
    if [[ -f "$combined_file" ]]; then
        echo "Removing existing combined file: $combined_file"
        rm -f "$combined_file"
    fi

    first_file=true

    for file in $glorys_arch_dir/${OUTPUT_PREFIX}_*_${year}-${month}-${day}.nc; do
        check_file_exists "$file" || continue

        if process_file "$file"; then
            if $first_file; then
                initialize_combined_file "$filled_dir/$(basename $file)" || exit 1
                first_file=false
            else
                append_to_combined_file "$filled_dir/$(basename $file)" || exit 1
            fi
            echo "Successfully processed and appended: $file"
        else
            echo "Skipping file: $file due to errors."
        fi
    done

    # Final verification
    if [[ -f "$combined_file" ]]; then
        echo "Successfully created or updated combined file: $combined_file"
    else
        echo "Error: Combined file was not created."
        exit 1
    fi
}

# Execute the main function
main
