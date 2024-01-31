# CEFI-regional-MOM6
This repository contains pre/post-processing tools and CEFI regional-MOM6 configurations for running regional-MOM6 OBGC simulations.
The development branch of the CEFI-regional-MOM6 is continually evolving as the system undergoes open development. The main branch represents a snapshot of this continuously evolving system.
Users are welcome to use the [discussions board](https://github.com/NOAA-GFDL/CEFI-regional-MOM6/discussions) to ask questions related to the model or the tools.

## What files are what

| File/directory    | Purpose |
| --------------    | ------- |
| ```LICENSE.md```  | A copy of the Gnu lesser general public license, version 3. |
| ```README.md```   | This file with basic pointers to more information. |
| ```src/```        | Contains the source code for CEFI-regional-MOM6 |
| ```builds/```     | Contains build script to build MOM6-SIS2-cobalt |
| ```diagnostics/```| Contains python scripts that can be utilized for analyzing model results after postprocessing. See [diagnostics/README.md](diagnostics/README.md) |
| ```exps/```       | Contains 1D mom6-cobalt exmaple and NWA12 configurtions. See [exps/README.md](exps/README.md) |
| ```tools/```      | Contains tools that can be used to generate initial conditions (ICs), boundary conditions (BCs), and other required inputs for MOM6-SIS2-cobalt model runs.  See [tools/README.md](tools/README.md) |
| ```xmls/```       | Contains FRE xml files designed for running the CEFI-regional-MOM6 workflow on NOAA Gaea C5. See [xmls/README.md](xmls/README.md) |

## Quick Start Guide
To learn how to compile/build MOM6-SIS2-cobalt and run an example regional test case, refer to [builds/README](builds/README) and [exps/README.md](exps/README.md).
Users who are interested in model inputs generation can check [tools/README.md](tools/README.md). 

## Disclaimer
The United States Department of Commerce (DOC) GitHub project code is provided on an 'as is' basis and the user assumes responsibility for its use. The DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

This project code is made available through GitHub but is managed by NOAA-GFDL at [https://www.gfdl.noaa.gov](https://www.gfdl.noaa.gov).
