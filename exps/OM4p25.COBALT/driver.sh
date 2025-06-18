#!/bin/bash

#SBATCH --nodes=5
#SBATCH --time=60
#SBATCH --job-name="OM4p25.COBALT"
#SBATCH --output=OM4p25.COBALT_o.%j
#SBATCH --error=OM4p25.COBALT_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
module load cray-mpich-abi
module unload cray-hdf5

echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

export img="/gpfs/f6/ira-cefi/world-shared/container/gaea_intel_2023.sif"

echo "SET MPICH_SMP_SINGLE_COPY_MODE"
export MPICH_SMP_SINGLE_COPY_MODE="NONE"

export APPTAINERENV_LD_LIBRARY_PATH=${CRAY_LD_LIBRARY_PATH}:${LD_LIBRARY_PATH}:/opt/cray/pe/lib64:/usr/lib64/libibverbs:/opt/cray/libfabric/1.20.1/lib64:/opt/cray/pals/1.4/lib:\$LD_LIBRARY_PATH

echo "SET APPTAINER_CONTAINLIBS"
export APPTAINER_CONTAINLIBS="/usr/lib64/libcxi.so,/usr/lib64/libcxi.so.1,/usr/lib64/libcxi.so.1.5.0,/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200,/usr/lib64/libnl-genl-3.so.200"

echo "SET APPTAINER_BIND"
export APPTAINER_BIND="/usr/share/libdrm,/var/spool/slurmd,/opt/cray,/opt/intel,${PWD},/etc/libibverbs.d,/usr/lib64/libibverbs,/usr/lib64/libnl3-200,${HOME}"

export FI_VERBS_PREFER_XRC=0

# Avoid job errors because of filesystem synchronization delays
#sync && sleep 1

srun --ntasks=900 --export=ALL apptainer exec --writable-tmpfs $img ./execrunscript.sh
#srun --ntasks=900 --cpus-per-task=1 --export=ALL ../../builds/build/gaea-ncrc6.intel23/ocean_ice/repro/MOM6SIS2 
