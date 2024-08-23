#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=30
#SBATCH --job-name="NWA12.CFC"
#SBATCH --output=NWA12.CFC_o.%j
#SBATCH --error=NWA12.CFC_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
ntasks1=128
ntasks2=64

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

#
rm -rf RESTART*

#
echo "Test started:  " `date`

#
echo "run 16x8 2hrs test ..."
ln -fs input.nml_2hr input.nml
ln -fs MOM_layout_16x8 MOM_layout
ln -fs MOM_layout_16x8 SIS_layout
srun -n ${ntasks1} ../../builds/build/gaea-ncrc6.intel23/ocean_ice/repro/MOM6SIS2 > out 2>err 
mv RESTART RESTART_2hrs

#
echo "run 16x8 1hrs test ..."
ln -fs input.nml_1hr input.nml
srun -n ${ntasks1} ../../builds/build/gaea-ncrc6.intel23/ocean_ice/repro/MOM6SIS2 > out2 2>err2
mv RESTART RESTART_1hrs

#
echo "link restart files ..."
pushd INPUT/
ln -fs ../RESTART_1hrs/* ./
popd

#
echo "run 8x8 1hrs rst test ..."
ln -fs input.nml_1hr_rst input.nml
ln -fs MOM_layout_8x8 MOM_layout
ln -fs MOM_layout_8x8 SIS_layout
srun -n ${ntasks2} ../../builds/build/gaea-ncrc6.intel23/ocean_ice/repro/MOM6SIS2 > out3 2>err3
mv RESTART RESTART_1hrs_rst

# Define the directories containing the files
module load nccmp
DIR1="RESTART_1hrs_rst/"
DIR2="RESTART_2hrs/"

if [ ! -d "$DIR1" ] || [ ! -d "$DIR2" ]; then
    echo "At least one of the restart directories does not exist."
    exit 1
fi

# Define the files to compare
FILES=("MOM.res.nc" "MOM.res_1.nc" "MOM.res_2.nc" "ocmip2_cfc_airsea_flux.res.nc" "ice_model.res.nc" "ice_ocmip2_cfc.res.nc")

# Iterate over the files
for FILE in "${FILES[@]}"; do
    # Compare the files using nccmp
    echo "Compare ${FILE}"
    nccmp -dfqS "${DIR1}${FILE}" "${DIR2}${FILE}" > /dev/null || { echo "Error: ${FILE} is not identical, please check! Exiting now..."; exit 1; }
done

#
echo "All restart files are identical, PASS"
echo "Test ended:  " `date`
