#exps 
This folder contains example configurations to run MOM6-SIS2-cobalt 

| directory    | Purpose |
| --------------    | ------- |
| ```OM4.single_column.COBALT/```     | 1D MOM6-cobalt exmaple |
| ```NEP.COBALTv2/```                 | NEP10 MOM6-SIS2-cobaltv2 example |

# OM4.single_column.COBALT
Users are advised to refer to the Dockerfile located at [ci/docker/Dockerfile.ci](../ci/docker/Dockerfile.ci). This Dockerfile includes the necessary steps to compile the code, download required input files, and execute the example 1D test case.

# NEP.COBALTv2
Users can follow the instructions below to run NEP10.COBALTv2 example on Gaea C5.

```console
git clone -b esm4.1_dFe_fert https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive
cd CEFI-regional-MOM6/builds; ./linux-build.bash -m gaea -p ncrc5.intel23 -t repro -f mom6sis2
cd ../exps
wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/nep10.cobaltv2_datasets.tar.gz
tar -zxvf nep10.cobaltv2_datasets.tar.gz 
cd NEP.COBALTv2
sbatch driver.sh 
```
