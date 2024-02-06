# build singularity image
```console
mkdir work && cd work
git clone -b main git@github.com:NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/ci/singularity
singularity build --fakeroot 1d_mom6_cobalt.sif ./build_1d_mom6_cobalt.def
```

# Run the singularity container image in interactive mode
```console
singularity shell --fakeroot -B /home/$USER/work:/work -e 1d_mom6_cobalt.sif 
```
# Build MOM6-SIS2-cobalt and run 1D case within singularity container
```console
Singularity> cd /work/CEFI-regional-MOM6/builds
Singularity> ./linux-build.bash -m docker -p linux-gnu -t prod -f mom6sis2
Singularity> cd ../exps
Singularity> wget https://gfdl-med.s3.amazonaws.com/OceanBGC_dataset/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tat.gz
Singularity> cd OM4.single_column.COBALT
Singularity> mpirun -np 1 --allow-run-as-root ../../builds/build/docker-linux-gnu/ocean_ice/prod/MOM6SIS2
```
