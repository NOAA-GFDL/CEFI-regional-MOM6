# NEP Diagnostics
This repo contains Jupyter Notebooks used to generate Figures 1-25 from the paper "A regional physical-biogeochemical ocean model for marine resource applications in the Northeast Pacific (MOM6-COBALT-NEP10k v1.0)", submitted to GMD.

## Python Notebooks

Most notebooks are written in python, and can be run using the MED maintained python environement. If you run the noteboooks PPAN, you can access this environment by running:
```
module load miniforge
conda activate /nbhome/role.medgrp/.conda/envs/medpy311
```
Otherwise, feel free to install this environment on your system using this [yaml file](https://github.com/NOAA-CEFI-Regional-Ocean-Modeling/MEDpy/blob/main/med_py311.yml).

## R Notebook
The notebooks `Figure_19_20/Calculate_Coldpool_Areas.ipynb` is written in R, and makes use of the R libraries `coldpool` and `akgfmaps`. We are currently experiencing issues integrating these libraries with conda, so we do not have an environment available to run that notebook. If you would like to run the code there, feel free to copy it into an R file and run that directly until we can provide a solution that integrates with Jupyter.
