# MOM6 Open Boundary Conditions (OBC) Generation Workflow

This repository provides an example workflow for generating Open Boundary Conditions (OBC) for MOM6 using daily GLORYS data on PPAN.

## Overview

The main script, `mom6_obc_workflow.sh`, orchestrates the entire OBC generation process. The workflow includes the following steps:

1. **Spatial Subsetting of GLORYS Data**  
   - Iterates through each day within a specified date range to spatially subset the original GLORYS dataset on UDA.  
   - Reduces computational cost by limiting input data to the regional domain of interest instead of the entire global GLORYS domain.

2. **Filling Missing Values in Subset GLORYS Files**  
   - Processes each daily subset file using CDO to fill missing values.  
   - Compresses processed files with `ncks -4 -L 5`.  
   - Combines all variables (e.g., `thetao`, `so`, `zos`, `uo`, `vo`) into a single NetCDF file.

3. **Daily Boundary Condition Generation**  
   - Submits jobs to execute the `write_glorys_boundary_daily.py` script for each day.  
   - Regrids GLORYS data and generates daily OBC files.

Template scripts for these steps are provided in the `template` directory. User-specific parameters are configured using [uwtools](https://github.com/ufs-community/uwtools) to render templates, creating a `config.yaml` file based on user input.

---

## Configuration Example

Below is an example `config.yaml` file to set up parameters for the workflow:

```yaml
# General parameters for template scripts
_WALLTIME: "1440" # Wall time (in minutes) for SLURM jobs
_NPROC: "1" # Number of processes for each job
_EMAIL_NOTIFICATION: "fail" # SLURM email notification option
_USER_EMAIL: "your.email@example.com" # Email address for error notifications
_LOG_PATH: "./log/$CURRENT_DATE/%x.o%j" # Path for job logs
_UDA_GLORYS_DIR: "/uda/Global_Ocean_Physics_Reanalysis/global/daily" # Path to original GLORYS data
_UDA_GLORYS_FILENAME: "mercatorglorys12v1_gl12_mean" # File name prefix for GLORYS data
_REGIONAL_GLORYS_ARCHIVE: "/archive/user/datasets/glorys" # Archive path for processed daily files
_BASIN_NAME: "NWA12" # Regional domain name
_OUTPUT_PREFIX: "GLORYS" # Prefix for output files
_VARS: "thetao so uo vo zos" # Variables to process
_LON_MIN: "-100.0" # Minimum longitude for subsetting
_LON_MAX: "-30.0" # Maximum longitude for subsetting
_LAT_MIN: "5.0" # Minimum latitude for subsetting
_LAT_MAX: "60.0" # Maximum latitude for subsetting
_PYTHON_SCRIPT: "$PYTHON_SCRIPT" # Path to the Python script for daily OBC generation

# Date range for processing
first_date: "$START_DATE"
last_date: "$END_DATE"

# Python script parameters
glorys_dir: "/archive/user/datasets/glorys/NWA12/filled" # daily subset of GLORYS DATA after filling NaN
output_dir: "./outputs" # output path for the obc files
hgrid: "./ocean_hgrid.nc" # grid file
ncrcat_names:
  - "thetao"
  - "so"
  - "zos"
  - "uv"
segments:
  - id: 1
    border: "south"
  - id: 2
    border: "north"
  - id: 3
    border: "east"
variables:
  - "thetao"
  - "so"
  - "zos"
  - "uv"
```

# Workflow Usage

## Step 1: Modify Configuration
Update the `cat <<EOF > config.yaml` part in `mom6_obc_workflow.sh` with parameters specific to your domain and workflow requirements.

```
cat <<EOF > config.yaml
_WALLTIME: "1440"
_NPROC: "1"
_EMAIL_NOTIFACTION: "fail"
_USER_EMAIL: "yi-cheng.teng@noaa.gov"
_LOG_PATH: "./log/$CURRENT_DATE/%x.o%j"
_UDA_GLORYS_DIR: "/uda/Global_Ocean_Physics_Reanalysis/global/daily"
_UDA_GLORYS_FILENAME: "mercatorglorys12v1_gl12_mean"
_REGIONAL_GLORYS_ARCHIVE: "/archive/ynt/datasets/glorys"
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
glorys_dir: "/archive/ynt/datasets/glorys/NWA12/filled"
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
```

## Step 2: Generate OBC Files
Run the workflow for a specific year or date range:

```bash
./mom6_obc_workflow.sh 2022-01-01 2022-12-31
./mom6_obc_workflow.sh 2023-01-01 2023-12-31
```

## Step 3: Concatenate Multiple Years of OBC Files
To merge OBC files from multiple years into a single file, use the `--ncrcat` option. Ensure the dates in the command match the range for which you generated OBC files:

```bash
./mom6_obc_workflow.sh 2022-01-01 2023-12-31 --ncrcat
```
### Adjust Timestamps (Optional Substep)
If you need to adjust the timestamps of the first and last records for compatibility with `MOM6` yearly simulation, use the `--adjust-timestamps` option in combination with `--ncrcat`. Note that this is an alternative to the command above and should not be run afterward: 
```
./mom6_obc_workflow.sh 2022-01-01 2023-12-31 --ncrcat --adjust-timestamps
``` 
**Note**: Ensure the date range specified in your command corresponds to the dates for which you generated OBC files. Running this step with a mismatched date range will cause it to fail if files for the specified dates are missing.

TODO:
