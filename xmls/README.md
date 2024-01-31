# xmls
This folder contains example XML files for the CEFI project that can be used by FRE for conducting regional MOM6-cobalt runs on Gaea C5 and running postprocessing/analysis on GFDL PPAN.

# Disclaimer
The provided XML files are primarily intended for users with access to NOAA Gaea C5 and GFDL PPAN platforms. We cannot guarantee the compatibility of these XML files with any other platforms. Users who wish to implement CEFI configurations on alternative platforms are encouraged to refer to the example configurations located under [exps/NWA12.COBALT](../exps/NWA12.COBALT) for guidance.

# Logging into Gaea
* `ssh -Y <First.Last>@gaea-rsa.princeton.rdhpcs.noaa.gov` (or `ssh -Y <First.Last>@gaea-rsa.boulder.rdhpcs.noaa.gov`)
```console
ssh -Y Yi-cheng.Teng@gaea-rsa.princeton.rdhpcs.noaa.gov
```
* Enter your pin and passcode from the RSA FOB. For example, if you pin was abcd1234 you would enter "abcd1234xxxxxx" where x's are the randomly generated numbers from the rsa fob.
* USer can use the following command to find the accounts/projects to which you belong (By default you should be under cefi project)
```console
sacctmgr show associations where user=$USER format=account%20,qos%50
             Account                                                QOS 
-------------------- -------------------------------------------------- 
                cefi                                           windfall 
                cefi           debug,interactive,normal,urgent,windfall 
                cefi                        interactive,normal,windfall 
```

# Working directory
Once user login, the default path would be your home directory: `/ncrc/home1|2/<First.Last>`. Each user has a 50 GB limit under their home folder. User should switch to `F5` to conduct their model runs.
F5 is a 50 PB General Parallel File System. F5 will not be swept. Any project jobs will be blocked if the project is significantly over quota.
* Directory Hierarchy
```
/gpfs/f5/<project>/scratch/$USER
/gpfs/f5/<project>/proj-shared
/gpfs/f5/<project>/world-shared
```
* switch to Short-term user folder: `/gpfs/f5/<project>/scratch/$USER`
```console
cd /gpfs/f5/cefi/scratch/Yi-cheng.Teng
```

# load modules
This step involves loading the necessary modules required for running the FRE XML.
```console
module use -a /ncrc/home2/fms/local/modulefiles
module load fre/bronx-21
module load git
```
# git clone CEFI-regional-MOM6
```console
git clone -b main https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git
```

# compile and build CEFI MOM6-SIS2-COBALT
```console
cd CEFI-regional-MOM6/xmls/NWA12
fremake -x CEFI_NWA12_cobalt.xml -p ncrc5.intel22 -t prod MOM6_SIS2_GENERIC_4P_compile_symm
```
The above step will git clone the source codes and prepare makefiles under `/gpfs/f5/cefi/scratch/<First.Last>/fre/cefi/NWA12/MOM6_SIS2_GENERIC_4P_compile_symm`.
Once its done, user can submit a job for compiling/building MOM6-SIS2-COBALT:
```console
sleep 1; sbatch /gpfs/f5/cefi/scratch/Yi-cheng.Teng/fre/cefi/NWA12/MOM6_SIS2_GENERIC_4P_compile_symm/ncrc5.intel22-prod/exec/compile_MOM6_SIS2_GENERIC_4P_compile_symm.csh
```
User can check /gpfs/f5/cefi/scratch/<First.Last>/fre/cefi/NWA12/MOM6_SIS2_GENERIC_4P_compile_symm/ncrc5.intel22-prod/exec/compile_MOM6_SIS2_GENERIC_4P_compile_symm.csh.oJOB_ID to monitor the progress.
If the job is completed successfully, you should be able to find the executable file:
```console
ls -l -h /gpfs/f5/cefi/scratch/Yi-cheng.Teng/fre/cefi/NWA12/MOM6_SIS2_GENERIC_4P_compile_symm/ncrc5.intel22-prod/exec/fms_MOM6_SIS2_GENERIC_4P_compile_symm.x
```
# conduct 30-year hindcast simulation in NWA12 domain:
The total length of the model simulation, in years, is controlled by the following parameter in the XML file:
`<property name="PROD_SIMTIME" value="30"/>`
Users can change this value to their desired simulated length. To conduct simulation, first do `frerun`:
```console
frerun -x CEFI_NWA12_cobalt.xml -p ncrc5.intel22 -t prod CEFI_NWA12_COBALT_V1 
```
Once the aboe step is done, it will create a job script `/gpfs/f5/cefi/scratch/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/ncrc5.intel22-prod/scripts/run/CEFI_NWA12_COBALT_V1`.
To submit the simulation, simply type:
```console
sleep 1; sbatch /gpfs/f5/cefi/scratch/Yi-cheng.Teng/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/ncrc5.intel22-prod/scripts/run/CEFI_NWA12_COBALT_V1
```
You can keep montioring the job progress by checking the stdout file `/gpfs/f5/cefi/scratch/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/ncrc5.intel22-prod/stdout/run/CEFI_NWA12_COBALT_V1.oJOB_ID`
In our example XML, it will conduct a 30-year simulation at a yearly interval. Every time it finishes a 1-year simulation, the XML workflow will automatically wrap up model outputs, restarts, clean up working folders, transfer this data to the PPAN archive, and submit a new job for the next year's simulation. You can find model outputs either on Gaea:
```console
ls /gpfs/f5/cefi/scratch/Yi-cheng.Teng/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/ncrc5.intel22-prod/archive
ascii  history  restart
```
or on GFDL PPAN (`ssh -Y <First.Last>@analysis-rsa.princeton.rdhpcs.noaa.gov`)
```console
ls /archive/Yi-cheng.Teng/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/
ascii  history  restart
```
where `ascii` contains model ASCII outputs (e.g., log files), `history` contains model diagnostic outputs, and `restart` contains model restart files, respectively.

# Post-Processing
The example XML contains a post-processing step to process 5-year and 30-year model history files, making them ready for analysis. By default, the FRE should conduct this step automatically on GFDL PPAN, and users should not have to do anything. In case you receive a system-generated email mentioning that your post-processing step failed, you can run this step manually on GFDL PPAN (`ssh -Y <First.Last>@analysis-rsa.princeton.rdhpcs.noaa.gov`; assuming the model data has been transferred to the GFDL PPAN without issues):
```console
module purge
module load fre/bronx-21
frepp -t 2022 -s -d /archive/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/history/ -x CEFI_NWA12_cobalt.xml -p gfdl.ncrc5-intel22 -T prod CEFI_NWA12_COBALT_V1 
```
This will allow you to manually run the `PP` step and generate a pp folder `/archive/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/pp`

# Run analysis after the postprocessing on GFDL PPAN:
Once you have your pp files (e.g. `/archive/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/pp`), you can run additional step to generate plots for analysis in NWA12 (the analysis scripts can be found in regional-mom6-xml/NWA12/analysis. Make sure you have a copy of the analysis scripts on 'GFDL PPAN' (e.g. use gcp to copy files from gaea to GFDL PPAN), and ensure that the analysis folder and your XML are in the same directory):
```console
module purge
module load fre/bronx-21
frepp -t 2022 -A -R -O ./results/CEFI_NWA12_COBALT_V1 -c ocean_monthly -d /archive/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/history/ -x CEFI_NWA12_cobalt.xml -p gfdl.ncrc5-intel22 -T prod CEFI_NWA12_COBALT_V1 
sbatch --chdir $HOME ./results/CEFI_NWA12_COBALT_V1/cefi_physics_monthly.csh.1993-2022
frepp -t 2022 -A -R -O ./results/CEFI_NWA12_COBALT_V1 -c ocean_cobalt_sfc -d /archive/<First.Last>/fre/cefi/NWA12/CEFI_NWA12_COBALT_V1/gfdl.ncrc5-intel22-prod/history/ -x CEFI_NWA12_cobalt.xml -p gfdl.ncrc5-intel22 -T prod CEFI_NWA12_COBALT_V1 
sbatch --chdir $HOME results/CEFI_NWA12_COBALT_V1/cefi_bgc_monthly.csh.1993-2022
```
You can find the analysis results under `$HOME/results/CEFI_NWA12_COBALT_V1/analysis/CEFI-regional-MOM6/diagnostics/physics/figures` and `$HOME/results/analysis/CEFI_NWA12_COBALT_V1/CEFI-regional-MOM6/diagnostics/biogeochemistry/figures`.


# Some useful docs for Gaea C5 (NOAA account is required for the first two docs)
* [Gaeadocs](https://gaeadocs.rdhpcs.noaa.gov/wiki/index.php?title=Welcome_to_Gaeadocs)
* [F5 Onboarding Guide](https://docs.google.com/document/d/1Z8YnZHaaWAWuyNfVGorrupBxtadOY04c4RL2Y2svZos/edit)
