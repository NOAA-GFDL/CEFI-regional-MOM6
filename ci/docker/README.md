# Build base image
```console
mkdir work && cd work
git clone -b main git@github.com:NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/ci/docker
docker build -t 1d_mom6_cobalt:base .
```

# run docker container image in interactive mode 
```console
docker run --mount "type=bind,source=/Users/$USER/work,target=/work" -it 1d_mom6_cobalt:base bash --login
```

# Build MOM6-SIS2-cobalt and run 1D case within docker container
```console
cd /work/CEFI-regional-MOM6/builds
./linux-build.bash -m docker -p linux-gnu -t prod -f mom6sis2
cd ../exps
wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz
cd OM4.single_column.COBALT
mpirun -np 1 --allow-run-as-root ../../builds/build/docker-linux-gnu/ocean_ice/prod/MOM6SIS2
```
