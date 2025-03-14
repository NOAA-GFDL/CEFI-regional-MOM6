# Author: Tom Robinson
FROM intel/hpckit:2024.2.1-0-devel-ubuntu22.04 as builder
############ Set up build environment ############
## Clone spack
RUN mkdir -p /opt && cd /opt && git clone -b v0.22.2 https://github.com/spack/spack.git
# What we want to install and how we want to install it
# is specified in a manifest file (spack.yaml)
RUN mkdir -p /opt/spack-environment && \
set -o noclobber \
&&  (echo spack: \
&&   echo '  mirrors:'\
&&   echo '    E4S: https://cache.e4s.io/noaa'\
&&   echo '  definitions:' \
&&   echo '  - packages_builtin:' \
&&   echo '    - bacio%oneapi@2024.2.1' \
&&   echo '    - hdf5@1.14.3%oneapi@2024.2.1' \
&&   echo '    - ip%oneapi@2024.2.1' \
&&   echo '    - libyaml@0.2.5%oneapi@2024.2.1' \
&&   echo '    - nccmp@1.9.1.0%oneapi@2024.2.1' \
&&   echo '    - netcdf-c@4.9.2%oneapi@2024.2.1' \
&&   echo '    - netcdf-fortran@4.6.1%oneapi@2024.2.1' \
&&   echo '    - sp@2.3.3%oneapi@2024.2.1' \
&&   echo '    - w3emc@2.11.0' \
&&   echo '    - w3nco@2.4.1' \
&&   echo '    - zlib%oneapi@2024.2.1' \
&&   echo '    - zlib-ng@2.1.4%oneapi@2024.2.1' \
&&   echo '  packages:' \
&&   echo '    intel-oneapi-mpi:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: intel-oneapi-mpi@2021.10.0' \
&&   echo '        path: /opt/intel/oneapi/mpi/2021.10.0' \
&&   echo '    mpi:' \
&&   echo '      require: intel-oneapi-mpi' \
&&   echo '    hdf5:' \
&&   echo '      variants: +fortran+hl+szip' \
&&   echo '    netcdf-c:' \
&&   echo '      variants: +dap' \
&&   echo '    pango:' \
&&   echo '      variants: +X' \
&&   echo '    all:' \
&&   echo '      target: [x86_64]' \
&&   echo '      providers:' \
&&   echo '        zlib-api: [zlib-ng+compat, zlib]' \
&&   echo '      compiler: [oneapi]' \
&&   echo '  specs:' \
&&   echo '  - matrix:' \
&&   echo '    - [$packages_builtin]' \
&&   echo '  concretizer:' \
&&   echo '    unify: True' \
&&   echo '  config:' \
&&   echo '    install_tree: /opt/software' \
&&   echo '  view: /opt/views/view') > /opt/spack-environment/spack.yaml
# Install the software, remove unnecessary deps
RUN . /opt/spack/share/spack/setup-env.sh && cd /opt/spack-environment && spack compiler add && spack --verbose env activate . && spack --verbose install --fail-fast && spack gc -y
## Set environment variables
ENV LD_LIBRARY_PATH /opt/views/view/lib:$LD_LIBRARY_PATH
ENV LIBRARY_PATH /opt/views/view/lib:$LIBRARY_PATH
ENV PATH $PATH:/opt/views/view/bin
############ Set up build ############
## Set up code checkout
RUN export GIT_TERMINAL_PROMPT=0 && \
   mkdir -p /apps/mom6_sis2_generic_4p_compile_symm_yaml/src && \
   cd  /apps/mom6_sis2_generic_4p_compile_symm_yaml/src && \
   git clone --recursive --jobs=4 https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git -b main mom6
## Clone mkmf
RUN cd /apps \ 
 && git clone --recursive https://github.com/NOAA-GFDL/mkmf \
 && cp mkmf/bin/* /usr/local/bin 
## Create the build directory
RUN mkdir -p /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec
## Use mkmf to create the Makefiles for the componenets
## Make makefile for FMS
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \ 
 && mkdir -p $bld_dir/FMS \ 
 && echo "Making makefile for FMS" \
 && list_paths -l -o $bld_dir/FMS/pathnames_FMS $src_dir/mom6/src/FMS  \
 && cd $bld_dir/FMS \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libFMS.a -t $mkmf_template -c " -DINTERNAL_FILE_NML -g -Duse_libMPI -Duse_netCDF -Duse_yaml  -DMAXFIELDMETHODS_=600" -I${src_dir}/mom6/src/FMS/fms2_io/include -I${src_dir}/mom6/src/FMS/include -I${src_dir}/mom6/src/FMS/mpp/include $bld_dir/FMS/pathnames_FMS
## Make makefile for MOM6
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \
 && mkdir -p $bld_dir/mom6 \
 && echo "Making makefile for MOM6" \
 && list_paths -l -o $bld_dir/mom6/pathnames_mom6 $src_dir/mom6/src/MOM6/config_src/memory/dynamic_symmetric $src_dir/mom6/src/MOM6/config_src/drivers/FMS_cap $src_dir/mom6/src/MOM6/src/*/ $src_dir/mom6/src/MOM6/src/*/*/ $src_dir/mom6/src/MOM6/config_src/external/ODA_hooks $src_dir/mom6/src/MOM6/config_src/external/stochastic_physics $src_dir/mom6/src/MOM6/config_src/external/drifters $src_dir/mom6/src/MOM6/config_src/external/database_comms $src_dir/mom6/src/ocean_BGC/generic_tracers $src_dir/mom6/src/ocean_BGC/mocsy/src $src_dir/mom6/src/MOM6/pkg/GSW-Fortran/modules $src_dir/mom6/src/MOM6/pkg/GSW-Fortran/toolbox $src_dir/mom6/src/MOM6/config_src/infra/FMS2  \
 && cd $bld_dir/mom6 \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libmom6.a -t $mkmf_template -c "-DINTERNAL_FILE_NML -g -DINTERNAL_FILE_NML -DMAX_FIELDS_=600 -DUSE_FMS2_IO -DNOT_SET_AFFINITY -D_USE_MOM6_DIAG -D_USE_GENERIC_TRACER  -DUSE_PRECISION=2 " -o "-I$bld_dir/FMS " -I${src_dir}/mom6/src/FMS/fms2_io/include -I${src_dir}/mom6/src/FMS/include -I${src_dir}/mom6/src/FMS/mpp/include -I${src_dir}/mom6/src/MOM6/pkg/CVMix-src/include $bld_dir/mom6/pathnames_mom6
## Make makefile for SIS2
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \
 && mkdir -p $bld_dir/sis2 \
 && echo "Creating make file for SIS2" \
 && list_paths -l -o $bld_dir/sis2/pathnames_sis2 $src_dir/mom6/src/SIS2/config_src/dynamic_symmetric $src_dir/mom6/src/SIS2/config_src/external/Icepack_interfaces $src_dir/mom6/src/SIS2/src $src_dir/mom6/src/icebergs/src $src_dir/mom6/src/ice_param  \
 && cd $bld_dir/sis2 \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libsis2.a -t $mkmf_template -c "-DINTERNAL_FILE_NML -g -DUSE_FMS2_IO" -o "-I$bld_dir/FMS -I$bld_dir/mom6 " -I${src_dir}/mom6/src/FMS/fms2_io/include -I${src_dir}/mom6/src/FMS/include -I${src_dir}/mom6/src/FMS/mpp/include -I${src_dir}/mom6/src/MOM6/pkg/CVMix-src/include -I${src_dir}/mom6/src/MOM6/src/framework $bld_dir/sis2/pathnames_sis2
## Make makefile for Null Land Model
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \
 && mkdir -p $bld_dir/land_null \
 && list_paths -l -o $bld_dir/land_null/pathnames_land_null $src_dir/mom6/src/land_null  \
 && echo "Making makefile for Land model" \
 && cd $bld_dir/land_null \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libland_null.a -t $mkmf_template -c "" -o "-I$bld_dir/FMS "  $bld_dir/land_null/pathnames_land_null
## Make makefile for Null Atmosphere Model
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \
 && mkdir -p $bld_dir/atmos_null \
 && echo "Making makefile for Atmoshphere model" \
 && list_paths -l -o $bld_dir/atmos_null/pathnames_atmos_null $src_dir/mom6/src/atmos_null  \
 && cd $bld_dir/atmos_null \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libatmos_null.a -t $mkmf_template -c "-DINTERNAL_FILE_NML -g" -o "-I$bld_dir/FMS " -I${src_dir}/mom6/src/FMS/fms2_io/include -I${src_dir}/mom6/src/FMS/include -I${src_dir}/mom6/src/FMS/mpp/include -I${src_dir}/mom6/src/MOM6/pkg/CVMix-src/include $bld_dir/atmos_null/pathnames_atmos_null
## Make makefile for coupler
RUN bld_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && src_dir=/apps/mom6_sis2_generic_4p_compile_symm_yaml/src \
 && mkmf_template=/apps/mkmf/templates/hpcme-intel24.mk \
 && mkdir -p $bld_dir/coupler \
 && echo "Making makefile for coupler" \
 && list_paths -l -o $bld_dir/coupler/pathnames_coupler $src_dir/mom6/src/coupler/shared $src_dir/mom6/src/coupler/full  \
 && cd $bld_dir/coupler \
 && mkmf -m Makefile -a $src_dir -b $bld_dir -p libcoupler.a -t $mkmf_template -c "-DINTERNAL_FILE_NML -g -DUSE_FMS2_IO -D_USE_LEGACY_LAND_ -Duse_AM3_physics" -o "-I$bld_dir/FMS -I$bld_dir/mom6 -I$bld_dir/sis2 -I$bld_dir/land_null -I$bld_dir/atmos_null " -I${src_dir}/mom6/src/FMS/fms2_io/include -I${src_dir}/mom6/src/FMS/include -I${src_dir}/mom6/src/FMS/mpp/include -I${src_dir}/mom6/src/MOM6/pkg/CVMix-src/include $bld_dir/coupler/pathnames_coupler
## Create the main Makefile
RUN mkdir -p /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && cd /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec \
 && set -o noclobber \
 &&  (echo  SRCROOT = /apps/mom6_sis2_generic_4p_compile_symm_yaml/src/ \
 &&   echo 'BUILDROOT = /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec/' \
 &&   echo 'MK_TEMPLATE = /apps/mkmf/templates/hpcme-intel24.mk' \
 &&   echo 'include $(MK_TEMPLATE)' \
 &&   echo 'mom6_sis2_generic_4p_compile_symm_yaml.x:  coupler/libcoupler.a sis2/libsis2.a mom6/libmom6.a land_null/libland_null.a atmos_null/libatmos_null.a FMS/libFMS.a ' \
 &&   echo '\t$(LD) $^ $(LDFLAGS) -o $@ $(STATIC_LIBS)' \
 &&   echo 'coupler/libcoupler.a:  FMS/libFMS.a mom6/libmom6.a sis2/libsis2.a land_null/libland_null.a atmos_null/libatmos_null.a  FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=coupler $(@F)' \
 &&   echo 'sis2/libsis2.a:  FMS/libFMS.a mom6/libmom6.a  FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=sis2 $(@F)' \
 &&   echo 'mom6/libmom6.a:  FMS/libFMS.a  FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=mom6 $(@F)' \
 &&   echo 'land_null/libland_null.a:  FMS/libFMS.a  FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=land_null $(@F)' \
 &&   echo 'atmos_null/libatmos_null.a:  FMS/libFMS.a  FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=atmos_null $(@F)' \
 &&   echo 'FMS/libFMS.a:   FORCE' \
 &&   echo '\t$(MAKE) SRCROOT=$(SRCROOT) BUILDROOT=$(BUILDROOT) MK_TEMPLATE=$(MK_TEMPLATE) --directory=FMS $(@F)' \
 &&   echo 'FORCE:' \
 &&   echo '') > /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec/Makefile
## Use make to build the model
RUN  cd /apps/mom6_sis2_generic_4p_compile_symm_yaml/exec && make -j 4 PROD=on
############ Create the final stage of the container build ############
FROM intel/oneapi-runtime:2024.2.1-0-devel-ubuntu22.04 as final
## copy libs and executable from builder
COPY --from=builder /opt/software /opt/software
COPY --from=builder /opt/views /opt/views
# This will include the code and all of the build from the builder stage
COPY --from=builder /apps/mom6_sis2_generic_4p_compile_symm_yaml /apps/mom6_sis2_generic_4p_compile_symm_yaml
## Set up the run time environment
ENV LD_LIBRARY_PATH /opt/views/view/lib:$LD_LIBRARY_PATH
ENV LIBRARY_PATH /opt/views/view/lib:$LIBRARY_PATH
ENV PATH /opt/views/view/bin:/apps/mom6_sis2_generic_4p_compile_symm_yaml/exec:$PATH
ENTRYPOINT ["/bin/bash"]
