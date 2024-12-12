# sbatch_mom6_obc_generation
Example scripts for pre-processing NEP5k GLORYS files for use as OBCs 

**Preliminary steps:**

I have spatially-subset GLORYS files in my archive directory that I use for this generation step. If starting from the GLORYS files on uda, I sugest adding an a dmget and ncks step to the "submit_python_make_obc_day.sh" script so as to reduce the input cost that would come from working with the entire global GLORYS domain. 

For filling using CDO, I've included the following scripts: 

  a. Bash script: submit_batch_glorys_fill
  - iterates the years and months of GLORYS and submits an SBATCH for each month worth of GLORYS files using Andrew C. Ross' script
    
  b. Bash script: fill_glorys.sh 
  - uses CDO to fill in missing values
  - **NOTE:** you could potenitally point to the global glorys uda directory here and add the spatial subsetting step. Maybe add it to the ncks -4 -L 5 bit?
  - **NOTE:** This takes a long time - you could discritize further and submit SBATCH job for each individual day. 

**OBC generation steps:**

1. Bash script: submit_batch_obc_day
  - Iterates over each day in a given year (includes leap year criteria to catch Feb. 29's) and submits shell script that runs the write_glorys_boundary.py file
   
    a. Bash script: submit_python_make_obc_day.sh
      -    contains SBATCH information (e.g., constraints, partition, time) **NOTE:** make sure to make the time long enough - this sometimes goes long on lower memory nodes like an002
      -    loads environmental needs like nco, gcp, conda environment (note - needs to be on analysis partition to read conda environments on NET)
      -    submits python command for write_glorys_boundary.py on slurm-allocated node

    b. Python script: write_glorys_boundary.py
      -    Original script can be found in the [CEFI-regional-MOM6/tools/boundary/](https://github.com/NOAA-GFDL/CEFI-regional-MOM6/tree/main/tools) repository
      -    Update script to indicate locations of:
           - The CEFI-regional-MOM6/tools/boundary/ directory (contains the boundary.py script) on your local machine 
           - The GLORYS files being remapped
           - The the ocean_hgrid.nc
      -    Update script to indicate the open boundaries for your specific domain (e.g., north, south, east, and/or west)
              
      -    **NOTE:** I've edited this example script to accept the output directory since it is running on a tmp node and needs to be directed as to where you want it to end up
   
2. This spawns a lot of jobs (#years*#days-in-year). Use the **squeue -u $USER** functionality to track the status of the jobs. Once the jobs are complete, I use the following to finalize pre processing (**NOTE:**  these steps do not currently require sbatch; might be useful for the concatenation step):

   a. Bash script: concatenate_obc_files.sh
     -    iterates over each year, variable, and segment, and concatenates all obcs for a given year; also modifies some of the attributes
     -    **NOTE:** this script removes the original obc files after concatenation 
   
   b. Bash script: copy_original_obcs
     -    copies pre-capped obc files to archive to have copy if there's any issue with the capping
   
   c. Bash script: cap_obcs
     -    takes the first and last time slice from each year and concatenates to the prior/following year, respectively, to make sure the full year being intergrated by MOM6 is covered in the given year of input files; for the first year (i.e., 1993), the time is set to midnight of Jan 1 using the edit_first_time.py script
     -    Python script: edit_first_time.py: changes time of 1993 first time slice to Jan 1 of 1993
     -    **NOTE:** Supposedly, we can now specify multiple input files for the atmosphere (not sure about obcs...) in the xml so we might be able to skip the time capping/ padding in the future and just allow the xml to handle reading in the years that bookend the year being integrated.
   



   
