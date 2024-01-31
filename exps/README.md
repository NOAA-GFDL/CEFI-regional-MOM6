#exps 
This folder contains example configurations to run MOM6-SIS2-cobalt 

| directory    | Purpose |
| --------------    | ------- |
| ```OM4.single_column.COBALT/```     | 1D MOM6-cobalt exmaple |
| ```NWA12.COBALT/```                 | NWA12 MOM6-SIS2-cobalt example |

# OM4.single_column.COBALT
Users are advised to refer to the Dockerfile located at [ci/docker/Dockerfile.ci](../ci/docker/Dockerfile.ci). This Dockerfile includes the necessary steps to compile the code, download required input files, and execute the example 1D test case.

# NWA12.COBALT
Users can follow the instructions below to run NWA12 example on Gaea C5.

```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc5.intel23 -t repro -f mom6sis2
cd ../exps
ln -fs /gpfs/f5/cefi/world-shared/datasets ./
cd NWA12.COBALT
sbatch run.sub 
```
If users do not have access to Gaea C5, the datasets for the `NWA12` case can be downloaded from [here](https://gfdl-med.s3.amazonaws.com/OceanBGC_dataset/nwa12_datasets.tar.gz).
