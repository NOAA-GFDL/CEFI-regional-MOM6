#!/bin/tcsh -f
#SBATCH --job-name=cefi-ana-phy-monthly
#SBATCH --constraint=bigmem
#SBATCH --partition=analysis
#SBATCH --output=%x.o%j
#SBATCH --time=60:00:00
#SBATCH --ntasks=1
#SBATCH --chdir=$HOME
#----------------------------------
# Script: cefi_ana_physics_monthly.csh 
# Authors: Yi-cheng.Teng 
# 
# Source data: $pp_root/pp/ocean_monthly/ts/monthly
#
# Output:  Creates figures in $HOME/$analysis_folder/CEFI-regional-MOM6/diagnostics/physics/figures 
# 
# Sample frepp usage (http://www.gfdl.noaa.gov/fms/fre/#analysis):
# <component type="ocean_monthly">
#    <timeSeries ... >
#       <analysis script="script_name [options]"/>
#    </timeSeries>
# </component>
#
# Sample usage to run this script standalone 
# sbatch cefi_physics_monthly.csh $pp_root
#
# Overview:
# This analysis script generates figures for SST, SSS, SSH, and coldpool index 
# in NWA domain. Details can be found in Ross, A. C. et al., 2023
# https://gmd.copernicus.org/articles/16/6943/2023/gmd-16-6943-2023.html` 

#fields set by frepp
set descriptor
set in_data_dir
set out_dir
set WORKDIR
set yr1
set yr2
set databegyr
set dataendyr
set datachunk
set staticfile
set fremodule

set gridspecfile = /archive/acr/mom6_input/nwa12/nwa12_grid_75z.tar


# Check if the user provided pp_root as an optional argument
set pp_root=""
if ($#argv == 1) then
    set pp_root="$argv[1]"
else
    # If no pp_root provided, grab it from in_data_dir
    set pp_root = `echo $in_data_dir | sed 's/pp.*//' | sed 's/pp//'`
endif

#set pp_root = `echo $in_data_dir | sed 's|\(.*gfdl\.ncrc5-intel22-prod\).*|\1|'`

# Check if pp_root is defined
if ( ! $?pp_root || "$pp_root" == "" ) then
    echo "Error: pp_root is not defined. Please set pp_root before running this script."
    exit 1
else
    echo "pp_root:" $pp_root
endif

# load python env
source $MODULESHOME/init/csh
module use -a /home/fms/local/modulefiles
module purge
module load fre/bronx-21
module load gcp
module load git
module use -a /home/ynt/modulefiles
module load conda_cefi
which conda
conda activate setup 

# create analysis folder 
set analysis_folder = "$out_dir/analysis"

# Check if the analysis folder exists
if (! -d $analysis_folder) then
    echo "Creating $analysis_folder folder..."
    mkdir $analysis_folder
    echo "$analysis_folder folder created."
else
    echo "$analysis_folder folder already exists."
endif

# git clone diagnostics repo
cd $analysis_folder
if (! -d CEFI-regional-MOM6) then
    git clone -b main https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git CEFI-regional-MOM6 
else
   echo "old clone exists!"
   cd CEFI-regional-MOM6
   git pull origin main 
   cd ..
endif
cd ./CEFI-regional-MOM6/diagnostics/physics

# Print out the current working directory
set current_path = `pwd`
echo "Current working directory: $current_path"

# create figures folder
if (! -d figures) then
    echo "Creating figures folder..."
    mkdir -p figures 
    echo "figures folder created."
else
    echo "figures folder already exists."
endif
  

#SST eval
echo "===Start SST eval==="
python sst_eval.py $pp_root
echo "===end SST eval===="

#SSS eval
echo "===Start SSS eval==="
python sss_eval.py $pp_root
echo "===end SSS eval===="

#SSH eval
echo "===Start SSH eval==="
python ssh_eval.py $pp_root
echo "===end SSH eval===="

#MLD eval
echo "===Start MLD eval==="
python mld_eval.py $pp_root
echo "===end MLD eval===="

#NWA coldpool index
echo "===Start coldpool eval==="
cd NWA12
python coldpool.py $pp_root
cd ../
echo "===end coldpool eval===="

# clean up
#cd $analysis_folder
#if (! -d $analysis_folder/physics) then
#    mkdir -p $analysis_folder/physics/figures
#else
#    echo "$analysis_folder/physics/figures exists!" 
#endif
#mv $analysis_folder/regional-mom6-diagnostics/physics/figures/* $analysis_folder/physics/figures/
#rm -rf $analysis_folder/regional-mom6-diagnostics 
echo "Done. Please check results here: $HOME/$analysis_folder/CEFI-regional-MOM6/diagnostics/physics/figures"
