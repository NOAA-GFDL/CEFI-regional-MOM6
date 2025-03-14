#!/bin/bash
#SBATCH --output=OUTPUT/stdout/CEFI_NWA12_COBALT_V1_%j.job
#SBATCH --job-name=CEFI_NWA12_COBALT_V1
#SBATCH --time=600
#SBATCH --partition=batch
#SBATCH --mail-user=Utheri.Wagura@noaa.gov
#SBATCH --mail-type=fail
#SBATCH --export=NONE
#SBATCH --clusters=c5
#SBATCH --nodes=13
#SBATCH --account=cefi

###########################################################################################
# SET RELEVANT VARIABLES
###########################################################################################
era5_dir="/gpfs/f5/gfdl_med/world-shared/northwest_atlantic/era5"
glofas_dir="/gpfs/f5/gfdl_med/world-shared/northwest_atlantic/nwa12_input/glofas/2023_04_v2/"
env_file="envs/container-gaea.env"

# Make sure variables were set and exist before continuing run
if [[ ! -d "$era5_dir" || ! -d "$glofas_dir" || ! -f "$env_file" ]]; then
    echo "ERROR: One of the era5_dir, glofas_dir, or env_file variables does not exist or was not set" 
    echo "ERROR: Please make sure these variables point to existing directories before running this script"
    exit 1
fi

###########################################################################################
# READ INPUT
###########################################################################################

if [[ -z $1 ]]; then
    echo "ERROR: Please provide the number of years you want to run for as an argument!"
    echo "Usage: $0 n"
    exit 1
else
    simyear=$1
    echo "NOTE ${simyear} years of experiment left to go!" 
fi

###########################################################################################
# HELPER FUNCTIONS
###########################################################################################
combine_output ()
{
    # Cobalt NEUS
    echo -e "\nCombining Cobalt NEUS files ..."
    mppnccombine -64 -h 65536 -m -k 100 ${1}.ocean_cobalt_neus.nc ${1}.ocean_cobalt_neus.nc.????
    #mv ${1}.ocean_cobalt_neus.nc OUTPUT/${1}
    rm -f ${1}.ocean_cobalt_neus.nc.????
     
    # Ocean 3hr NEUS
    echo -e "\nCombining Ocean 3hr files"
    mppnccombine -64 -h 65536 -m -k 100 ${1}.ocean_neus_3hr.nc ${1}.ocean_neus_3hr.nc.????
    #mv ${1}.ocean_neus_3hr.nc OUTPUT/${1}
    rm -f ${1}.ocean_neus_3hr.nc.????

    # Ocean NEUS
    echo -e "\nCombining Ocean NEUS files"
    mppnccombine -64 -h 65536 -m -k 100 ${1}.ocean_neus.nc ${1}.ocean_neus.nc.????
    #mv ${1}.ocean_neus.nc OUTPUT/${1}
    rm -f ${1}.ocean_neus.nc.????

    # Combine netcdf files
    echo -e "\nTarring netcdf files"
    tar -cvf ${1}.tar *.nc
    mv ${1}.tar OUTPUT/${1}
    rm -f *.nc

    # Combine ascii files
    echo -e "\nTarring ascii files"
    tar -cvf ${1}_ascii.tar *.out SIS* COBALT_parameter_doc.* MOM_parameter_doc.* available_diags.000000 time_stamp.out *.stats
    mv ${1}_ascii.tar OUTPUT/${1}
    rm -f *.out SIS* COBALT_parameter_doc.* MOM_parameter_doc.* available_diags.000000  time_stamp.out *.stats
    if [ -f V.velocity_truncations ]; then 
        echo "WARNING: Velocity Truncation files found. Moving to OUTPUT folder"
        mv ?.velocity_truncations OUTPUT/${1}
    fi
}

move_output () 
{
    mv *.nc.???? OUTPUT/${1}
    mv *.nc OUTPUT/${1}
    mv *.out SIS* COBALT_parameter_doc.* MOM_parameter_doc.* available_diags.000000 ?.velocity_truncations time_stamp.out *.stats OUTPUT/${1}/
}

get_forcings () 
{
    echo "NOTE: Ensuring era5 forcing is available for current year"
    for var in "msl" "t2m" "sphum" "strd" "ssrd" "lp" "sf" "u10" "v10" ; do
        if [ -f INPUT/ERA5_${var}_${start_year}_padded.nc ]; then
            echo "NOTE: Found ${start_year} data for ${var}, moving on to next var" 
        else
            echo "NOTE: ${start_year} ERA5 forcing not found for ${var}"
            echo -e "\tNOTE: now copying over ${start_year} ERA5 data for ${var} from ${era5_dir}"

            # Make sure this file exists before attempting to copy it over
            if [ -f ${era5_dir}/ERA5_${var}_${start_year}_padded.nc ]; then 
                cp ${era5_dir}/ERA5_${var}_${start_year}_padded.nc INPUT/
            else
                echo "ERROR: Could not find file ${era5_dir}/ERA5_${var}_${start_year}_padded.nc"
                echo "ERROR: Please make sure this file exists before in the era5_dir you specified"
                exit 1
            fi

            if [ -f INPUT/ERA5_${var}_$(( start_year - 1 ))_padded.nc ]; then
                echo -e "\tWARNING: Found $(( start_year - 1 )) ERA5 data for ${var}, now removing it"
                rm -f INPUT/ERA5_${var}_$((start_year - 1 ))_padded.nc
            fi
        fi
    done

    echo "NOTE: Checking that GloFAS runoff is available for current year"
    if [ -f INPUT/glofas_runoff_${start_year}.nc ]; then
        echo "NOTE: Found ${start_year} GloFAS runoff data"
    else
        echo "NOTE: ${start_year} GloFAS runoff not found, now copying it over from ${glofas_dir}"
        cp ${glofas_dir}/glofas_runoff_${start_year}.nc INPUT/
        if [ -f INPUT/glofas_runoff_$(( start_year -1 )).nc ]; then
            echo -e "\tWARNING: Found glofas runoff data for $(( start_year -1 )), now deleting it"
            rm -f INPUT/glofas_runoff_$(( start_year -1 )).nc
        fi
    fi
}

set_1993_ic ()
{
    # Set the start date of the run
    start_month=01
    start_day=01
    start_year=1993
}

###########################################################################################
# DETERMINE IF RESTART OR INITIAL RUN
###########################################################################################

# Check for non-empty RESTART dirs
if [ -d OLD_RESTART ]; then
    if [ -f OLD_RESTART/coupler.res ]; then
        echo "NOTE: Found restart file, reading start date of new run"
        coupler_end=`tail -n 1 OLD_RESTART/coupler.res | sed 's/    //g' | cut -d " " -f 3,4,5`
        start_year=`echo $coupler_end | cut -d " " -f 1`
        
        # Get start day, format it as 2 digit number
        start_month_single=`echo $coupler_end | cut -d " " -f 2`
        start_month=$(printf %02d ${start_month_single})

        # Same for start month
        start_day_single=`echo $coupler_end | cut -d " " -f 3`
        start_day=$(printf %02d ${start_day_single})

        # Make input.nml as 'r' as the restart flag
        echo "NOTE: Changing restart flag in input.nml to 'r' "
        sed -i "s/input_filename = 'n'/input_filename = 'r'/" input.nml

        # Move current restart files to dir
        ls OLD_RESTART/ | xargs -I % ln OLD_RESTART/% INPUT/%
    else
        echo "ERROR: Could not find coupler restart file in OLD_RESTART, assuming 1993 ICs"
        set_1993_ic
    fi
else
    echo "NOTE: Could not find restart files, assuming this run is starting from inital conditions"
    echo "NOTE: Changing restart flag in input.nml to 'n'"
    sed -i "s/input_filename = 'r'/input_filename = 'n'/" input.nml
    set_1993_ic
fi

date_string=${start_year}${start_month}${start_day}
echo "NOTE: Starting model run on ${date_string}"

###########################################################################################
# SETUP ENVIRONMENT
###########################################################################################

# Get era5 data
get_forcings

# Edit OBC_TIDE_NODAL_REF_DATE variable in MOM_override
echo "NOTE: Changing all instances of $(( start_year -1 )) to ${start_year} in MOM_override"
sed -i "s/$(( start_year -1 ))/${start_year}/" INPUT/MOM_override

# Edit data table to point to correct forcing files
echo "NOTE: Changing ERA5 and GloFAS paths from $(( start_year -1 )) to ${start_year} in data_table"
sed -i "s/$(( start_year - 1))_padded.nc/${start_year}_padded.nc/" data_table 
sed -i "s/$(( start_year - 1)).nc/${start_year}.nc/" data_table

## Make mppnccombine available
#module use -a /ncrc/home2/fms/local/modulefiles
#module load fre/bronx-23

# Clean INPUT DIR of previous restart files
rm INPUT/MOM.res*
rm INPUT/coupler.res
rm INPUT/*.res.nc

###########################################################################################
# RUN MODEL
###########################################################################################

# Set environment to use MPI with container
source $env_file

# Run Module
srun --ntasks=1646 --cpus-per-task=1 --export=ALL apptainer exec --writable-tmpfs CEFI_NWA12_COBALT_V1.sif /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec/mom6_sis2_generic_4p_compile_symm_yaml.x

## Combine Outputs if mppnccombine is available. Otherwise, just move them to their own folder. 
mkdir -p OUTPUT/${date_string}

###########################################################################################
# COMBINE OUTPUTS
###########################################################################################

# Check if mppncombine is availabe. Use it to combine outputs if so, otherwise just move the output
if which mppnccombine > /dev/null 2>&1 ; then
    combine_output ${date_string}
    if [ $? != 0 ]; then
        echo "ERROR: Combining files failed. Manually moving any remaing files to OUTPUT/${date_string}"
        move_output ${date_string}
    fi
else
    echo "WARNING: Could not fine mppnccombine on system. Moving raw output to OUTPUT/${date_string}"
    move_output ${date_string}
fi

###########################################################################################
# PREPARE DIR FOR NEXT RUN
###########################################################################################
rm -rf OLD_RESTART
mv RESTART/ OLD_RESTART/
mkdir RESTART


###########################################################################################
# SUBMIT NEXT RUN
###########################################################################################

nu_simyear=$(( $simyear - 1 ))
if (( ${nu_simyear} > 0 )); then
    echo "NOTE: Now submitting next year. ${nu_simyear} years to go!"
    sbatch run_model.sh ${nu_simyear}
    echo "NOTE: Job submitted succesfully, now exititng"
else
    echo "NOTE: Experiment has reached it's natural conclusion, now exiting"
fi

exit 0
