This tool can be use to build the executable for the model. If you have Gaea C5 access, try the following command directly. Otherwise please check [Build CEFI-regional-MOM6](#build-cefi-regional-mom6) for detailed instructions.

On machine gaea for platform c5 with intel23 compiler:
```console
./linux-build.bash -m gaea -p ncrc5.intel23 -t prod -f mom6sis2
```
This assumes that the files build/gaea/ncrc5.intel23.env and build/gaea/ncrc5.intel23.mk exist.
-  build/gaea/ncrc5.intel23.env contains all the necessary environment variables and modules
that must be loaded before a build / run on that machine
-  build/gaea/ncrc5.intel23.mk  contains the compile instructions for the particular compiler and machine

# Quick Start Guide

**Conda warning**: before you install anything or try to build the model, make sure to deactivate your `conda` environment because it could interfere with brew and the model build process.
conda deactivate.

## Prerequisites
**For PC users:** 
- Install WSL (Windows Subsystem for Ubuntu and Linux):  [link](https://learn.microsoft.com/en-us/windows/wsl/install) and install the following softwares:
```console
sudo apt update
sudo apt install make gfortran git tcsh netcdf-bin libnetcdf-dev libnetcdff-dev openmpi-bin libopenmpi-dev
```
- Container approach: Docker container is available for Window10 or 11: [link]([https://docs.docker.com/desktop/install/windows-install/#:~:text=To%20run%20Windows%20containers%2C%20you,you%20to%20run%20Linux%20containers.&text=Docker%20only%20supports%20Docker%20Desktop,still%20within%20Microsoft's%20servicing%20timeline%20](https://docs.docker.com/desktop/install/windows-install/#:~:text=To%20run%20Windows%20containers%2C%20you,you%20to%20run%20Linux%20containers.&text=Docker%20only%20supports%20Docker%20Desktop,still%20within%20Microsoft's%20servicing%20timeline%20.)https://docs.docker.com/desktop/install/windows-install/#:~:text=To%20run%20Windows%20containers%2C%20you,you%20to%20run%20Linux%20containers.&text=Docker%20only%20supports%20Docker%20Desktop,still%20within%20Microsoft's%20servicing%20timeline%20.)
  Then follow the instruction [here](../ci/docker/README.md) to build the model.

**For MacOS users:** 
- Install HomeBrew: [link](https://brew.sh/) and install the following software from terminal:
```console
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install make
brew install gfortran
brew install openmpi
brew install netcdf
brew install netcdf-fortran
brew install wget
```

## Build CEFI-regional-MOM6:
- After `git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive` navigate to the `builds` directory: `cd CEFI-regional-MOM6\builds`
- mkdir `YOUR_MACHINE_DIRECTORY`: This should be the name of your system, e.g, mac-m1. Then `cd YOUR_MACHINE_DIRECTORY`
- you will need two files: `NAME_OF_YOUR_mk_FILE.env` and `NAME_OF_YOUR_mk_FILE.mk` in this folder (e.g. gnu.env and gnu.mk or somthing similiar).
- The `NAME_OF_YOUR_mk_FILE.env` file is mainly used for the HPC system to allow you to load necessary software to build the model. In most cases, if you already have gfortran, mpi (openmpi or mpich), and netcdf installed on your system, the `***.env` file can be left blank.
- The `NAME_OF_YOUR_mk_FILE.mk` file may be different depends on your system configurations (e.g. Intel v.s. GNU compilers). We already have a few examples within the `builds` folder. Users can also find more general templates [here](https://github.com/NOAA-GFDL/mkmf/tree/af34a3f5845c5781101567e043e0dd3d93ff4145/templates). Below are some recommended templates:

| Platform          | Template |
| --------------    | ------- |
| ```gaea```        | ncrc5-intel-classic.mk |
| ```Ubuntu```      | linux-ubuntu-trusty-gnu.mk |
| ```MacOS```       | osx-gnu.mk |

- Use the following command to build the model (Make sure to use correct names that are consistent with both your machine folder and your mk/env files.):
```console
./linux-build.bash -m YOUR_MACHINE_DIRECTORY -p NAME_OF_YOUR_mk_FILE -t repro -f mom6sis2
```
- If the build completes successfully, you should be able to find the executable here: `builds/build/YOUR_MACHINE_DIRECTORY-NAME_OF_YOUR_mk_FILE/ocean_ice/repro/MOM6SIS2`

## Test run: 1-D MOM6-COBALT
- To test your `MOM6SIS2`, first navigate to the `exps` folder: `cd ../exps`
- Download the model input files: `wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz`
- navigate to the 1-D example: `cd OM4.single_column.COBALT`
- USe the following command to run the 1-D example: `mpirun -np 1 ../../builds/build/YOUR_MACHINE_DIRECTORY-NAME_OF_YOUR_mk_FILE/ocean_ice/repro/MOM6SIS2`
