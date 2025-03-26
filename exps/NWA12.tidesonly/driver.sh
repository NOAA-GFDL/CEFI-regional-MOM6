#!/bin/bash
#SBATCH --nodes=1
#SBATCH --time=60
#SBATCH --job-name="NWA12.tidesonly"
#SBATCH --output=NWA12.tidesonly_o.%j
#SBATCH --error=NWA12.tidesonly_e.%j
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c6
#SBATCH --account=ira-cefi

#
ntasks1=4

#
echo "Test started:  " `date`

module load cray-mpich-abi
module unload cray-hdf5

#
echo "link datasets ..."
pushd ../
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
popd

export img="/gpfs/f6/ira-cefi/world-shared/container/cefi_mom6_intel_2024.2.1.sif"
export MPICH_SMP_SINGLE_COPY_MODE="NONE" # Cray MPICH setting, more info here: https://cpe.ext.hpe.com/docs/latest/mpt/mpich/intro_mpi.html#smp-environment-variables
export APPTAINERENV_LD_LIBRARY_PATH="${CRAY_LD_LIBRARY_PATH}:\${LD_LIBRARY_PATH}:/opt/cray/pe/lib64:/usr/lib64/libibverbs:/opt/cray/libfabric/1.20.1/lib64:/opt/cray/pals/1.4/lib"
export APPTAINER_CONTAINLIBS="/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libcxi.so.1,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200"
export APPTAINER_BIND="/usr/share/libdrm,/var/spool/slurmd,/opt/cray,/opt/intel,/etc/libibverbs.d,/usr/lib64/libibverbs,/usr/lib64/libnl3-200"
export SINGULARITY_SHELL=/bin/bash

#
echo "run tidesonly test ..."
srun --ntasks ${ntasks1} --export=ALL singularity exec -B /gpfs -B /ncrc/home2/Yi-cheng.Teng:/ncrc/home2/Yi-cheng.Teng "${img}" ../../builds/build/docker-linux-intel/ocean_only/repro/MOM6

echo "Test ended:  " `date`
