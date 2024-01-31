#!/bin/bash

#assume we are on PPAN
#prerequisite:
# coarsen glorys datasets: users can use coarsen_glorys.py
# to get them for their own application

# First load modules
module load fre/bronx-21

# check if ESPER exists or not, if yes, removed it
if [ -d "./ESPER" ]; then
    echo "The folder ESPER exists. Deleting..."
    rm -rf ESPER 
fi 

# git clone ESPER and checkout specific tag
git clone https://github.com/BRCScienceProducts/ESPER.git
cd ESPER
git checkout ed43822

# modifty ESPER_LIR.m
sed -i 's/nanmean/mean/g' ESPER_LIR.m
cd .. 

# check if outputs folder exists or not
if [ -d "./outputs" ]; then
    echo "The folder outputs exists."
else
    echo "creating folder outputs..."
    mkdir outputs
fi

# run matlab ESPER 
START_YEAR=1993
END_YEAR=2019
if [ -f "ALK_DIC_create_GLORYS_025.m" ]; then
    echo "deleteing ALK_DIC_create_GLORYS_025.m"
    rm -rf ALK_DIC_create_GLORYS_025.m
fi

# create new ALK_DIC_create_GLORYS_025.m
echo "create new ALK_DIC_create_GLORYS_025.m"
cp ALK_DIC_create_GLORYS_025_template.m ALK_DIC_create_GLORYS_025.m
sed -i "s/__STARTYEAR__/$START_YEAR/g" ALK_DIC_create_GLORYS_025.m
sed -i "s/__ENDYEAR__/$END_YEAR/g" ALK_DIC_create_GLORYS_025.m 
#
matlab232 -nodisplay -nosplash -nodesktop -r "run ALK_DIC_create_GLORYS_025; exit;"

# 
ncrcat ./outputs/DICAlk_ESPER_LIR_GLORYS_025_*.nc -O ./outputs/DICAlk_ESPER_LIR_GLORYS_NWA025_${START_YEAR}_${END_YEAR}.nc

#
echo "Done..."
