# FRE yamls

The latest version of the FMS Runtime Environment uses yamls instead of xmls to execute the FRE workflow. This folder contains experiment, compile, and platform yamls that can be used with the latest version of `fre` to compile and post process the `CEFI_NWA12_Cobalt_V1` experiment. The compiled experiment can then be run in conjuction with `fre/bronx-23` and the existing xmls in the `xml/NWA12` directory. 

The following sections assume that you are compiling and running experiments on Gaea C5, and then conducting postprocessing on GFDL's PPAN system. The `platforms.yaml` does support compilation on C6, but `bronx-23` does not support containerized runs on C6 - baremetal runs, however, are supported on C6.

Full documentation for `Fre/2025.01` is available [here](https://noaa-gfdl.github.io/fre-cli/usage.html)

## Compile the Experiment. 

Begin by loading the appropriate modules on Gaea C5: 
```
module use -a /ncrc/home2/fms/local/modulefiles
module load fre/2025.01
```

`fre/2025.01` supports both containerized compilation and bare-metal compilation, with very similar steps for both targets. 

### Baremetal Compilation 

Run the following command to create the script that will be used to checkout the model components, and optionally run the script by passing in the --execute flag.
If you don't provide the --execute flag, be sure to run the script printed at the end of this command manually.
```
fre make create-checkout -y CEFI_NWA12_cobalt.yaml -p ncrc5.intel23 -t prod --execute
```

Create the Makefile for the experiment: 
```
fre make create-makefile -y CEFI_NWA12_cobalt.yaml -p ncrc5.intel23 -t prod
```

Create the script that actually compiles the experiment, and optionally run the script by passing in the --execute flag
```
fre make create-compile -y CEFI_NWA12_cobalt.yaml -p ncrc5.intel23 -t prod --execute
```

### Containerized Compilation

Compiling the experiment into a container is a similar process. The only changes are 1.) passing in the -npc flag during the checkout step to prevent parallel checkouts, 2.) changing you platform to `hpcme.2023` and 3.) creating a Dockerfile and container creation script instead of a compilation script. Note that the Dockerfile will compile the model within the container as part of the build process.

```
fre make create-checkout -y CEFI_NWA12_cobalt.yaml -p hpcme.2023 -t prod -npc
fre make create-makefile -y CEFI_NWA12_cobalt.yaml -p hpcme.2023 -t prod
fre make create-dockerfile -y CEFI_NWA12_cobalt.yaml -p hpcme.2023 -t prod --execute
```

## Running the Experiment

`fre/2025.01` does not currently support running experiments with yamls, so in order to run the compiled experiment in fre, you will have to use the existing xmls along with `fre/bronx`. Make sure the `FRE_STEM` set in the xml matches the `FRE_STEM` set in the experiment yaml.

**NOTE**: Since capitilized names are not allowed in Dockerfiles, the current compile yaml names the compilation experiment `mom6_sis2_generic_4p_compile_symm_yaml` instead of `MOM6_SIS2_GENERIC_4P_compile_symm_yaml` like the xml. As a result, `fre` will print a warning that it cannot find your executable when you run `frerun`, and will eventually fail if you submit the job.

To get around this, change the path set in the `executable` variable within the runscript printed by `frerun` to point to the exectable located in `${FRE_STEM}/mom6_sis2_generic_4p_compile_symm_yaml/exec` instead.

### Baremetal Run

Baremetal experiments can be run using the same run [instructions](https://github.com/NOAA-GFDL/CEFI-regional-MOM6/tree/main/xmls) available in the xmls directory. Be sure to load the modules described in that page before running `frerun`. 

### Containerized Run
Current xmls can be used for containerized runs, as well, so long as the following changes are made: 

1.) Run `module load fre/bronx-23` and change the `FRE_VERSION` property of the xml to `bronx-23`.
2.) Right below the `<experiment name="CEFI_NWA12_COBALT_V1" inherit="MOM6_SIS2_GENERIC_4P_compile_symm">` tag, add a tag with a path to your `.sif` singularity image file: 
    ```
    <container file="path/to/container/"/>
    ```

With these changes, you should be able to run the experiment by calling `frerun` with an extra `--container` flag
```
frerun -x CEFI_NWA12_cobalt.xml -p ncrc5.intel23 -t prod CEFI_NWA12_COBALT_V1 --container
```


## Postprocessing the Experiment
Like `fre make`, postprocessing is split into several subcommands to improve modularity. On PPAN, load the appropriate module: 
```
module load fre/2025.01
```

Checkout the git repo containing postprocessing scripts and related files with the folowing command:
```
fre pp checkout -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod
```

Combine your main yaml and experiment yamls into a single yaml, then set up the cylc-src dir with the configure-yaml command:
```
fre yamltools combine-yamls -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod -y CEFI_NWA12_cobalt.yaml --use pp
fre pp configure-yaml -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod -y CEFI_NWA12_cobalt.yaml
```

`fre/2025.01` does not automatically create the pp dir for you, so you will have to mkdir this first to pass the validator:
```
mkdir /archive/$USER/fre/cefi/NWA/2024_06/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel23-prod/pp
```

(OPTIONAL, BUT RECOMMENDED): Create a list of available tar files within your history tar archives to allow fre to catch a wider variety of errors
```
tar -tf /archive/$USER/fre/cefi/NWA/2024_06/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel23-prod/history/19930101.nc.tar | grep -v tile[2-6] | sort > /home/$USER/cylc-src/CEFI_NWA12_COBALT_V1__gfdl.ncrc5-intel23__prod/history-manifest
```
  
Validate that all configuration files are correct
```
fre pp validate -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod
```

Create the cylc-run directory containing the final version of configuration files, scripts, and output directories
```
fre pp install -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod
```

Run post processing
```
fre pp run -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod
```

To monitor the status of each post processing step, run the following command:
```
fre pp status -e CEFI_NWA12_COBALT_V1 -p gfdl.ncrc5-intel23 -t prod
```
