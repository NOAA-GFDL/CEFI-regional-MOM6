#How to build MOM6-SIS2-cobalt on Mac

## Install Homebrew
```console
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
export HOMEBREW_ROOT=/opt/homebrew
export PATH=$HOMEBREW_ROOT/bin:$PATH
```
## Install Prerequisite packages
```console
brew install gcc \
gfortran \
openmpi \
netcdf \
netcdf-fortran \
autoconf \
automake \
git \
git-lfs \
wget

git lfs install
```

## Change default gcc
```console
cd /opt/homebrew/bin
ln -s g++-13 g++
ln -s gcc-13 gcc
```
Then open a new terminal window

## Install FRE-NCtools for grid generation
```console
mkdir work && cd work
git clone https://github.com/NOAA-GFDL/FRE-NCtools.git
autoreconf -i
mkdir build && cd build
../configure --prefix=/Users/$USER/work/FRE-NCtools/build
make
make install
```
The tools will be located at `/Users/$USER/work/FRE-NCtools/build/bin`

## compile CEFI MOM6-SIS2-cobalt and run 1-D example
```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds
./linux-build.bash -m macOS -p osx-gnu -t repro -f mom6sis2
cd ../exps
wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz
cd OM4.single_column.COBALT
mpirun -np 1 ../../builds/build/macOS-osx-gnu/ocean_ice/repro/MOM6SIS2 
