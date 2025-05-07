#!/bin/bash -x

# Default configurations
machine_name="gaea"
platform="ncrc5.intel23"
target="repro"  # Options: repro, debug-openmp, prod, avx512, etc.
flavor="mom6sis2"  # Options: mom6sis2, fms1_mom6sis2, mom6solo

# Supported flavors and targets
VALID_FLAVORS=("mom6sis2" "fms1_mom6sis2" "mom6solo")
VALID_TARGETS=("repro" "debug" "prod")

usage() {
    echo "Usage: $0 -m <machine> -p <platform> -t <target> -f <flavor>"
    echo "  -m : Machine name (e.g., gaea)"
    echo "  -p : Platform (e.g., ncrc5.intel23)"
    echo "  -t : Target (valid: repro, debug, prod)"
    echo "  -f : Flavor (valid: mom6sis2, fms1_mom6sis2, mom6solo)"
    exit 1
}

# Parse command-line arguments
while getopts "m:p:t:f:h" Option; do
   case "$Option" in
      m) machine_name=${OPTARG};;
      p) platform=${OPTARG};;
      t) target=${OPTARG};;
      f) flavor=${OPTARG};;
      h) usage; exit 0;;
   esac
done

# Validate target and flavor
validate_input() {
    if [[ ! " ${VALID_FLAVORS[@]} " =~ " ${flavor} " ]]; then
        echo "❌ Invalid flavor: $flavor"
        echo "Valid options: ${VALID_FLAVORS[*]}"
        exit 1
    fi

    if [[ ! " ${VALID_TARGETS[@]} " =~ " ${target} " ]]; then
        echo "❌ Invalid target: $target"
        echo "Valid options: ${VALID_TARGETS[*]}"
        exit 1
    fi
}

# Get absolute path of root directory
rootdir=$(dirname "$0")
abs_rootdir=$(cd "$rootdir" && pwd)

# Load necessary modules
source $MODULESHOME/init/bash
source $rootdir/$machine_name/$platform.env

# Default Makeflags
makeflags="NETCDF=4"

# Update makeflags based on the target
update_makeflags() {
    if [[ $target =~ "repro" ]]; then
        makeflags="$makeflags REPRO=1"
    fi
    if [[ $target =~ "prod" ]]; then
        makeflags="$makeflags PROD=1"
    fi
    if [[ $target =~ "avx512" ]]; then
        makeflags="$makeflags PROD=1 AVX=512"
    fi
    if [[ $target =~ "debug" ]]; then
        makeflags="$makeflags DEBUG=1"
    fi
}

# Function to build libyaml
build_libyaml() {
    echo "Building libyaml..."
    local target_dir="$abs_rootdir/build/$machine_name-$platform/libyaml/$target"
    
    # Clean up existing build
    [[ -d $target_dir ]] && rm -rf $target_dir
    mkdir -p $target_dir
    
    # Build libyaml
    pushd $srcdir/libyaml
    $srcdir/libyaml/bootstrap
    $srcdir/libyaml/configure --prefix="$target_dir" --disable-shared
    make && make install
    if [ $? -ne 0 ]; then
        echo "Could not build the libyaml library!"
        exit 1
    fi
    popd
}

# Function to build FMS2 (for mom6sis2 flavor)
build_fms2() {
    echo "Building FMS2 library..."
    local shared_dir="build/$machine_name-$platform/shared2/$target"
    
    # Clean up and create directory
    mkdir -p $shared_dir
    pushd $shared_dir
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/FMS/{affinity,amip_interp,column_diagnostics,diag_integral,drifters,grid_utils,horiz_interp,memutils,sat_vapor_pres,topography,astronomy,constants,diag_manager,field_manager,include,monin_obukhov,platform,tracer_manager,axis_utils,coupler,fms,fms2_io,interpolator,mosaic,mosaic2,random_numbers,time_interp,tridiagonal,block_control,data_override,exchange,mpp,time_manager,string_utils,parser}/ $srcdir/FMS/libFMS.F90
    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../libyaml/$target/include" -p libfms.a -l "-L../../libyaml/$target/lib -lyaml $linker_options" -c "-Duse_libMPI -Duse_yaml -Duse_netCDF -DMAXFIELDMETHODS_=800" path_names
    make $makeflags libfms.a
    if [ $? -ne 0 ]; then
        echo "Could not build the FMS2 library!"
        exit 1
    fi
    popd
}

# Function to build FMS1 (for fms1_mom6sis2 flavor)
build_fms1() {
    echo "Building FMS1 library..."
    local shared_dir="build/$machine_name-$platform/shared1/$target"
    
    # Clean up and create directory
    mkdir -p $shared_dir
    pushd $shared_dir
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/FMS/{affinity,amip_interp,column_diagnostics,diag_integral,drifters,grid_utils,horiz_interp,memutils,sat_vapor_pres,topography,astronomy,constants,diag_manager,field_manager,include,monin_obukhov,platform,tracer_manager,axis_utils,coupler,fms,fms2_io,interpolator,mosaic,mosaic2,random_numbers,time_interp,tridiagonal,block_control,data_override,exchange,mpp,time_manager,string_utils,parser}/ $srcdir/FMS/libFMS.F90
    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -p libfms.a -c "-Duse_deprecated_io -Duse_libMPI -Duse_netCDF -DMAXFIELDMETHODS_=800" path_names
    make $makeflags libfms.a
    if [ $? -ne 0 ]; then
        echo "Could not build the FMS1 library!"
        exit 1
    fi
    popd
}

# Function to build MOM6 with FMS2 cap (for mom6sis2 flavor)
build_mom6_fms2() {
    echo "Building MOM6 with FMS2 cap..."
    local target_dir="build/$machine_name-$platform/ocean_ice/$target"
    
    # Clean up and create directory
    mkdir -p $target_dir
    pushd $target_dir
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/FMS_cap,config_src/external/ODA_hooks,config_src/external/database_comms,config_src/external/drifters,config_src/external/stochastic_physics,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}/} $srcdir/SIS2/{config_src/dynamic_symmetric,config_src/external/Icepack_interfaces,src} $srcdir/icebergs/src $srcdir/FMS/{coupler,include}/ $srcdir/{ocean_BGC/generic_tracers,ocean_BGC/mocsy/src}/ $srcdir/{atmos_null,ice_param,land_null,coupler/shared/,coupler/full/}/

    # Compiler and linker options
    compiler_options='-DINTERNAL_FILE_NML -DUSE_FMS2_IO -Duse_yaml -DMAX_FIELDS_=600 -DNOT_SET_AFFINITY -D_USE_MOM6_DIAG -D_USE_GENERIC_TRACER -DUSE_PRECISION=2 -D_USE_LEGACY_LAND_ -Duse_AM3_physics'
    linker_options=''
    if [[ "$target" =~ "stdpar" ]]; then
        compiler_options="$compiler_options -stdpar -Minfo=accel"
        linker_options="$linker_options -stdpar"
    fi

    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../shared2/$target -I../../libyaml/$target/include" -p MOM6SIS2 -l "-L../../shared2/$target -lfms -L../../libyaml/$target/lib -lyaml $linker_options" -c "$compiler_options" path_names
    make $makeflags MOM6SIS2
    if [ $? -ne 0 ]; then
        echo "Could not build MOM6 with FMS2!"
        exit 1
    fi
    popd
}

# Function to build MOM6 with FMS1 cap (for fms1_mom6sis2 flavor)
build_mom6_fms1() {
    echo "Building MOM6 with FMS1 cap..."
    local target_dir="build/$machine_name-$platform/fms1_ocean_ice/$target"  # Corrected the directory to ocean_ice
    
    # Clean up and create directory
    mkdir -p $target_dir
    pushd $target_dir
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS1,config_src/memory/dynamic_symmetric,config_src/drivers/FMS_cap,config_src/external/ODA_hooks,config_src/external/database_comms,config_src/external/drifters,config_src/external/stochastic_physics,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}/} $srcdir/SIS2/{config_src/dynamic_symmetric,config_src/external/Icepack_interfaces,src} $srcdir/icebergs/src $srcdir/FMS/{coupler,include}/ $srcdir/{ocean_BGC/generic_tracers,ocean_BGC/mocsy/src}/ $srcdir/{atmos_null,ice_param,land_null,coupler/shared/,coupler/full/}/

    # Compiler and linker options
    compiler_options='-DINTERNAL_FILE_NML -DUSE_FMS1_IO -Duse_yaml -DMAX_FIELDS_=600 -DNOT_SET_AFFINITY -D_USE_MOM6_DIAG -D_USE_GENERIC_TRACER -DUSE_PRECISION=2 -D_USE_LEGACY_LAND_ -Duse_AM3_physics'
    linker_options=''
    if [[ "$target" =~ "stdpar" ]]; then
        compiler_options="$compiler_options -stdpar -Minfo=accel"
        linker_options="$linker_options -stdpar"
    fi

    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../shared1/$target -I../../libyaml/$target/include" -p MOM6SIS2 -l "-L../../shared1/$target -lfms -L../../libyaml/$target/lib -lyaml $linker_options" -c "$compiler_options" path_names
    make $makeflags MOM6SIS2
    if [ $? -ne 0 ]; then
        echo "Could not build MOM6 with FMS1!"
        exit 1
    fi
    popd
}

# Function to build MOM6Solo (for mom6solo flavor)
build_mom6solo() {
    echo "Building MOM6Solo..."
    local target_dir="build/$machine_name-$platform/ocean_only/$target"
    
    # Clean up and create directory
    mkdir -p $target_dir
    pushd $target_dir
    rm -f path_names
    $srcdir/mkmf/bin/list_paths $srcdir/MOM6/{config_src/infra/FMS2,config_src/memory/dynamic_symmetric,config_src/drivers/solo_driver,config_src/external/GFDL_ocean_BGC,config_src/external/ODA_hooks,config_src/external/database_comms,config_src/external/drifters,config_src/external/stochastic_physics,pkg/GSW-Fortran/{modules,toolbox}/,src/{*,*/*}}/

    # Compiler and linker options
    compiler_options='-DUSE_FMS2_IO -Duse_yaml -DMAX_FIELDS_=600 -Duse_netCDF -DSPMD'
    linker_options=''
    if [[ "$target" =~ "stdpar" ]]; then
        compiler_options="$compiler_options -stdpar -Minfo=accel"
        linker_options="$linker_options -stdpar"
    fi

    $srcdir/mkmf/bin/mkmf -t $abs_rootdir/$machine_name/$platform.mk -o "-I../../shared2/$target -I../../libyaml/$target/include" -p MOM6 -l "-L../../shared2/$target -lfms -L../../libyaml/$target/lib -lyaml $linker_options" -c "$compiler_options" path_names
    make $makeflags MOM6
    if [ $? -ne 0 ]; then
        echo "Could not build MOM6Solo!"
        exit 1
    fi
    popd
}

# Main logic
validate_input

srcdir=$abs_rootdir/../src
update_makeflags
sed -i 's/static pid_t gettid(void)/pid_t gettid(void)/g' $srcdir/FMS/affinity/affinity.c

case "$flavor" in
    "mom6sis2" )
        build_libyaml
        build_fms2
        build_mom6_fms2
        ;;
    "fms1_mom6sis2" )
        echo "Building MOM6 with FMS1 cap"
        build_fms1
        build_mom6_fms1
        ;;
    "mom6solo" )
        echo "Building MOM6Solo"
        build_libyaml
        build_fms2
        build_mom6solo
        ;;
    * )
        echo "Invalid flavor specified."
        exit 1
        ;;
esac

echo "Build completed successfully!"
