# exps 
This folder contains example configurations to run MOM6-SIS2-cobalt 

| directory    | Purpose |
| --------------    | ------- |
| ```OM4.single_column.COBALT/```     | 1D MOM6-cobalt exmaple |
| ```OM4p25.COBALT/```                | OM4 0.25deg MOM6-cobalt v3 exmaple |
| ```dumbbell/```                     | dumbbell exmaple |
| ```NWA12.COBALT/```                 | NWA12 MOM6-SIS2-cobalt example |
| ```NEP10.COBALT/```                 | NEP10 MOM6-SIS2-cobalt example |


# OM4.single_column.COBALT
Users are advised to refer to the Dockerfile located at [ci/docker/Dockerfile.ci](../ci/docker/Dockerfile.ci). This Dockerfile includes the necessary steps to compile the code, download required input files, and execute the example 1D test case.

Users can also test the 1D case without using the container approach, please follow [this tutorial](https://cefi-regional-mom6.readthedocs.io/en/latest/BuildMOM6.html). The example dataset for the 1D case can be downloaded from `ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_ci_datasets.tar.gz`.

Users can follow the instructions below to run 1D example on Gaea C5:

```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc5.intel23 -t debug -f mom6sis2
cd ../exps
ln -fs /gpfs/f5/cefi/world-shared/datasets ./
cd OM4.single_column.COBALT
sbatch run.sub
```
# OM4p25.COBALT
Users can follow the instructions below to run OM4 0.25 COBALTv3 example on Gaea C6.
```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc6.intel23 -t repro -f mom6sis2
cd ../exps
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
cd OM4p25.COBALT
sbatch driver.sh
```
If users do not have access to Gaea C6, the datasets for the `OM4p25.COBALT` case be downloaded from `ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/OM4_datasets/OM4_025.JRA.tar.gz`.

# NWA12.COBALT
Users can follow the instructions below to run NWA12 example on Gaea C6.

```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc6.intel23 -t repro -f mom6sis2
cd ../exps
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
cd NWA12.COBALT
sbatch run.sub 
```
If users do not have access to Gaea C6, the datasets for the `NWA12` case be downloaded from `ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/nwa12_datasets.tar.gz`.

# NEP10.COBALT
Users can follow the instructions below to run NEP10 example on Gaea C6.

```console
git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc6.intel23 -t repro -f mom6sis2
cd ../exps
ln -fs /gpfs/f6/ira-cefi/world-shared/datasets ./
cd NEP10.COBALT
sbatch run.sub
```
If users do not have access to Gaea C6, the datasets for the `NEP10` case be downloaded from `ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/nep10_datasets.tar.gz`.
