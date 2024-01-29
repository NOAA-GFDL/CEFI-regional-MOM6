#!/bin/bash -x                                     
machine_name="gaea" 
platform="intel18"
#machine_name="tiger" 
#platform="intel18"
#machine_name="googcp" 
#platform="intel19"
#machine_name = "ubuntu"
#platform     = "pgi18"                                             
#machine_name="ubuntu" 
#platform="gnu7"
#machine_name = "gfdl-ws" 
#platform     = "intel15"
#machine_name = "gfdl-ws"
#platform     = "gnu6" 
#machine_name = "theta"   
#platform     = "intel16"
#machine_name="lscsky50"
#platform="intel19up2_avx1" #"intel18_avx1" # "intel18up2_avx1" 
target="prod" #"debug-openmp"       
flavor="mom6solo" #"mom6solo

usage()
{
    echo "usage: linux-build.bash -m googcp -p intel19 -t prod -f mom6sis2"
}

# parse command-line arguments
while getopts "m:p:t:f:h" Option
do
   case "$Option" in
      m) machine_name=${OPTARG};;
      p) platform=${OPTARG} ;;
      t) target=${OPTARG} ;;
      f) flavor=${OPTARG} ;;
      h) usage ; exit ;;
   esac
done

rootdir=`dirname $0`
abs_rootdir=`cd $rootdir && pwd`


#load modules              
source $MODULESHOME/init/bash
source $rootdir/$machine_name/$platform.env
. $rootdir/$machine_name/$platform.env

makeflags="NETCDF=3"

if [[ "$target" =~ "openmp" ]] ; then 
   makeflags="$makeflags OPENMP=1" 
fi

if [[ "$target" =~ "openacc" ]] ; then 
   makeflags="$makeflags OPENACC=1" 
fi

if [[ $target =~ "repro" ]] ; then
   makeflags="$makeflags REPRO=1"
fi

if [[ $target =~ "prod" ]] ; then
   makeflags="$makeflags PROD=1"
fi

if [[ $target =~ "avx512" ]] ; then
   makeflags="$makeflags PROD=1 AVX=512"
fi

if [[ $target =~ "debug" ]] ; then
   makeflags="$makeflags DEBUG=1"
fi

srcdir=$abs_rootdir/../src

sed -i 's/static pid_t gettid(void)/pid_t gettid(void)/g' $srcdir/FMS/affinity/affinity.c

mkdir -p build/$machine_name-$platform/shared/$target
pushd build/$machine_name-$platform/shared/$target   
rm -f path_names                       
$srcdir/mkmf/bin/list_paths $srcdir/FMS/{affinity,amip_interp,column_diagnostics,diag_integral,drifters,horiz_interp,memutils,sat_vapor_pres,topography,astronomy,constants,diag_manager,field_manager,include,monin_obukhov,platform,tracer_manager,axis_utils,coupler,fms,fms2_io,interpolator,mosaic,mosaic2,random_numbers,time_interp,tridiagonal,block_control,data_override,exchange,mpp,time_manager,string_utils,parser}/ $srcdir/FMS/libFMS.F90
$srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -p libfms.a -c "-Duse_libMPI -Duse_netCDF -DMAXFIELDMETHODS_=800" path_names

make $makeflags libfms.a         

if [ $? -ne 0 ]; then
   echo "Could not build the FMS library!"
   exit 1
fi

popd

if [[ $flavor =~ "mom6sis2" ]] ; then
    mkdir -p build/$machine_name-$platform/ocean_ice/$target
    pushd build/$machine_name-$platform/ocean_ice/$target
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/FMS_cap,config_src/external/ODA_hooks,config_src/external/database_comms,config_src/external/drifters,config_src/external/stochastic_physics,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}/} $srcdir/SIS2/{config_src/dynamic_symmetric,config_src/external/Icepack_interfaces,src} $srcdir/icebergs/src $srcdir/FMS/{coupler,include}/ $srcdir/{ocean_BGC/generic_tracers,ocean_BGC/mocsy/src}/ $srcdir/{atmos_null,ice_param,land_null,coupler/shared/,coupler/full/}/


compiler_options='-DINTERNAL_FILE_NML -DMAX_FIELDS_=600 -DNOT_SET_AFFINITY -D_USE_MOM6_DIAG -D_USE_GENERIC_TRACER -DUSE_PRECISION=2 -D_USE_LEGACY_LAND_ -Duse_AM3_physics'
linker_options=''
if [[ "$target" =~ "stdpar" ]] ; then 
    compiler_options="$compiler_options -stdpar -Minfo=accel"
    linker_options="$linker_options -stdpar "
fi

    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../shared/$target" -p MOM6SIS2 -l "-L../../shared/$target -lfms $linker_options" -c "$compiler_options" path_names

if [[ "$target" =~ "cobaltACC" ]] ; then 
    sed -e 's/-c\(.*\)COBALT/-acc -ta=nvidia:managed -Minfo=accel -c \1COBALT/' -i Makefile
    sed -e 's/-lfms/-lfms -acc/' -i Makefile
fi

if [[ "$target" =~ "cobaltOMP" ]] ; then 
    sed -e 's/-c\(.*\)COBALT/-mp -c \1COBALT/' -i Makefile
fi

if [[ "$target" =~ "cobaltOMPGPU" ]] ; then 
    sed -e 's/-c\(.*\)COBALT/-mp=gpu -gpu=managed -Minfo=accel -c \1COBALT/' -i Makefile
    sed -e 's/-lfms/-lfms -mp=gpu -gpu=managed/' -i Makefile
fi

    make $makeflags MOM6SIS2

else 
    mkdir -p build/$machine_name-$platform/ocean_only/$target
    pushd build/$machine_name-$platform/ocean_only/$target
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external/GFDL_ocean_BGC,config_src/external/ODA_hooks,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}}/
    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../shared/$target" -p MOM6 -l "-L../../shared/$target -lfms" -c '-Duse_netCDF -DSPMD' path_names

    make $makeflags MOM6
fi
