# diagnostics
This folder provides scripts, that can be utilized for analyzing model results.
Please contact the code manager Yi-Cheng Teng (Contact: yi-cheng.teng@noaa.gov) if you have any queations.

## Prerequisite
The majority of the scripts are written in Python. One can follow the instructions (README.md under tools folder) to create a Python virtual environment on NOAA R&D HPCs or GFDL Analysis.

The Python scripts that read model data are written to take advantage of the `hsmget` command for faster reading and caching of data from the archive filesystem. When using GFDL Analysis, it is recommended to load the hsm module (`module load hsm/1.3.0`) before running any of the diagnostic scripts. 