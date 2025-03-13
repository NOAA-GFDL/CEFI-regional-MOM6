# Running Containerized Model Outside of FRE

## Introduction

This directory contains scripts to run the `CEFI_NWA12_COBALT_V1` experiment in a container outside of the `FRE` workflow. Since these scripts do not benefit from the years of development that have gone into `FRE`, it lacks several features and makes several assumptions: 

1.) You will have to stage all the necessary input files to the `INPUT/` directory yourself, using the same naming scheme as `CEFI_NWA12_cobalt.xml`. All input files are available on gaea, and the `run_model.sh` script will stage annual `ERA5` and `GloFAS` runoff forcings for you if you provide a path to a directory where these files are located. You will have to manually move the other files your self. If on gaea , or a system with access to gaea, you can stage the necesarray inputs from C5 with the following commands:
```
cp /gpfs/f5/cefi/world-shared/datasets/container_input/NWA/INPUT ./INPUT
ln -s INPUT/ocean_topog.nc INPUT/topog.nc
```
or from c6 using the following command
```
cp /gpfs/f6/ira-cefi/world-shared/datasets/container_input/NWA/INPUT ./INPUT
ln -s INPUT/ocean_topog.nc INPUT/topog.nc
```

2.) Model output will not be staged to another system at the end of each model year. When a year of simulation is complete, `run_model.sh` will simply tar together all output files and move them to a folder in `OUTPUT` named after the start date of that particular run. If the `mppnccombine` tool is available in your `path`, `run_model.sh` will try to combine outputs from different ranks before tarring the files togeter. 

## Requirements
This workflow uses a containerized environment to compile and run the model. As such, to run the workflow as-is, you will need access to a system that has both `podman` and `apptainer/singularity` available. Since `podman` is a drop in replacement for `docker`, the `compile_model.sh` script should still work if you replace `podman` with `docker`, though this has not been tested. Similarly, if you do not have access to `apptainer/singularity`, you may be able to skip the `apptainer build` step and replace `apptainer exec` with `docker exec` in `run_model.sh`, although this has not been tested either. 

Running the model requires either `Intel MPI` or `MPICH`. The environment file in `/envs/container-gaea.env` uses `lmod` to load `MPICH` for you and sets environment variables that `apptainer` needs. If running on a system other than gaea, you will need to create an environment file that sets the relevant variables and loads the relevant `MPI` implementation for you. 

**IMPORTANT**: If running on a system other than gaea, be sure to edit the variables `era5_dir`, `glofas_dir`, and `env_file` to point to direcotories containing annual `ERA5` and `GloFAS` runoff data, as well as your environment file, before running the workflow. 
**IMPORTANT**: We have encountered some issues building the container on some gaea nodes. So far, the model had compiled successfully on the following nodes:
```
gaea56
```
Please use one of these nodes to create the container until all compilation issues are resolved

## Running the workflow.

After staging all files to the `INPUT` directory, compile the model by calling `compile_model.sh`:
```
./compile_model.sh
```
This will create a `CEFI_NWA12_COBALT_V1.sif` file containing the model executable. Note that this process can take about an hour to complete. Once you have the `.sif` file, and have set all of the relevant variables at the top of the `run_model.sh` script, run the following command to run the model for `n` years:
```
sbatch ./run_model.sh n
```
The model output from each siumulation year will be available in `OUTPUT/YYYY0101` for year `YYYY`, while the `stdout` and `stderr` from the run will be available in `OUTPUT/stdout`. 
