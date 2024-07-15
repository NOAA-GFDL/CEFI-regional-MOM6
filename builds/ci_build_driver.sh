#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="MOM6SIS2_ci_build"
#SBATCH --output=MOM6SIS2_ci_build_o.%j
#SBATCH --error=MOM6SIS2_ci_build_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
[ -d "build" ] && rm -rf build

#
echo "Build MOM6SIS2-COBALT for CI testing started:  " `date`

#
machine_name="gaea" 
platform="ncrc5.intel23"
target="repro"
flavor="fms1_mom6sis2"

FMSlib_PATH="/gpfs/f5/cefi/scratch/Yi-cheng.Teng/github/FMS/2024.02_FMS1"
rootdir=$(pwd)
abs_rootdir=$rootdir

echo $abs_rootdir

#load modules              
source $MODULESHOME/init/bash
source $rootdir/$machine_name/$platform.env
. $rootdir/$machine_name/$platform.env

makeflags="NETCDF=3"

if [[ $target =~ "repro" ]] ; then
   makeflags="$makeflags REPRO=1"
fi

srcdir=$abs_rootdir/../src

#
sed -i 's/static pid_t gettid(void)/pid_t gettid(void)/g' $srcdir/FMS/affinity/affinity.c

#
if [[ $flavor == "fms1_mom6sis2" ]] ; then
    echo "build mom6sis2 with FMS1 cap" 	

    mkdir -p build/$machine_name-$platform/ocean_ice/$target
    pushd build/$machine_name-$platform/ocean_ice/$target
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS1,config_src/memory/dynamic_symmetric,config_src/drivers/FMS_cap,config_src/external/ODA_hooks,config_src/external/database_comms,config_src/external/drifters,config_src/external/stochastic_physics,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}/} $srcdir/SIS2/{config_src/dynamic_symmetric,config_src/external/Icepack_interfaces,src} $srcdir/icebergs/src $srcdir/FMS/{coupler,include}/ $srcdir/{ocean_BGC/generic_tracers,ocean_BGC/mocsy/src}/ $srcdir/{atmos_null,ice_param,land_null,coupler/shared/,coupler/full/}/

   compiler_options='-DINTERNAL_FILE_NML -DMAX_FIELDS_=600 -DNOT_SET_AFFINITY -Duse_deprecated_io -D_USE_MOM6_DIAG -D_USE_GENERIC_TRACER -DUSE_PRECISION=2 -D_USE_LEGACY_LAND_ -Duse_AM3_physics'

   $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I${FMSlib_PATH}/shared/$target" -p MOM6SIS2 -l "-L${FMSlib_PATH}/shared/$target -lfms" -c "$compiler_options" path_names

   make $makeflags MOM6SIS2 

fi


#
echo "Build MOM6SIS2-COBALT for CI testing ended:  " `date`
