## tools

This folder contains tools (mainly written in Python) that can be used to generate initial conditions (ICs), boundary conditions (BCs), and other required inputs for regional MOM6 model runs.

Below we provide instruction for creating a Python virtual environment on NOAA R&D HPCs, specifically configured for the Gaea system. The process outlined here can generally be applied to other clusters within NOAA RDHPCs. The guide has been provided by Yi-Cheng Teng (Contact: yi-cheng.teng@noaa.gov).

## Install Conda Environment on Gaea

1. **Download Miniconda:**
   - Select or create a directory (e.g. `/lustre/f2/dev/YOUR_USER_NAME`) other than your home directory to download Miniconda to avoid space limit issues in the future.
   - Use the following command to download Miniconda:

   `wget -nH -m -nd https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
   
   This command will download a file named “Miniconda3-latest-Linux-x86_64.sh”.

2. **Install Miniconda:**

    Run the following command to install Miniconda:
    
     `bash Miniconda3-latest-Linux-x86_64.sh`
     
    Follow the displayed instructions to read and accept the license terms. You'll be prompted to enter “yes” to accept the terms. When     asked about the installation location, you can either accept the default location by pressing Enter or specify a different location     and then press Enter. Additionally, when prompted to initialize Conda in your shell profile, choose not to initialize by pressing       Enter (which is “no”).
    
 3. **Initialize Miniconda:**

    After installation, initialize the newly installed Miniconda. For Bash, use the command:
    
    `source /conda_directory/miniconda3/etc/profile.d/conda.sh`
    
    Note: Change `/conda_directory/` with miniconda3 path on your system.
    
  4. **Test the Installation:**

      Verify if Miniconda has been installed correctly by running the command:
    
     `conda info --envs`
   
      Your current environment will be highlighted with an asterisk (*).

      Additionally, to display a list of installed packages:

      `conda list`

       A list of installed packages should appear if the installation was successful.
    
  6.  **Activate and Deactivate Environments:**

      - To deactivate the current environment, use:
      
      `conda deactivate`

      - To activate the base environment, use:

      `conda activate base`
    
  ## Managing Environments in Conda/Mamba
  
  You can create separate environments for various applications to avoid conflicts between different package requirements. Here two methods are explained to create and manage environments: Conda and Mamba. Mamba, a faster alternative to Conda, excels in resolving dependencies but, being relatively new, might have more undiscovered bugs that could take longer to be identified.
  
  ### Using Conda
  
1. **Create a New Environment:**
   - Use the following command to create a new environment named e.g. project_name_env:

   `conda create --name project_name_env`
   
    This command will create an environment in miniconda3/envs/project_name_env.

   - If you want to create an Environment with Specific Python Version (e.g., Python 3.10.3), use:

    `conda create -n new_env_name python=3.10.3`
    
   Proceed by confirming the installation with `y` to install the required packages.
   
 2. **Activate the Environment:**
  
      Activate the newly created environment project_name_env using:
 
      `conda activate project_name_env`
      
      Once activated, the active environment will be indicated in your command prompt within parentheses or brackets, such as                   `(project_name_env) $`. 
      
      If not visible, check the active environment using: 
 
      `conda info --envs`
      
      The current environment is highlighted with an asterisk (*).
  
 3. **View Installed Packages in the Environment:**

      To display a list of all packages installed within a specific environment (e.g., project_name_env), use:

      `conda list`

4. **Install Packages:**

      Install required packages using either `pip install <package_name>` or `conda install <package_name>` within the activated environment.


5. **Deactivate and Delete an Environment:**

  - Ensure the environment is deactivated before removing it. Use the following command to deactivate:

    `conda deactivate`
    
  - To delete an environment (replace ENV_NAME with the name of the environment):

    `conda remove --name ENV_NAME --all`

  ### Using Mamba

Mamba is a drop-in replacement and uses the same commands and configuration options as conda. 
You can swap almost all commands between conda & mamba. 

1- **Install mamba**

   - Install mamba in the base environment:

      `conda install -n base -c conda-forge mamba`
   
   - Press `Y` when prompted 

2- **Initialize mamba:**

   - Initialize mamba after installation:
    `mamba init`

   - To apply these changes, close and then re-open your terminal window.

3- **Create a New Environment:**

   - Use the following command to create a new environment named e.g. project_name_env:

   `mamba create -n project_name_env`
   
   This command will create an environment in `miniconda3/envs/project_name_env`.

   - If you want to create an Environment with Specific Python Version (e.g., Python 3.10), use:

      `mamba create -n project_name_env python=3.10`
    
   Proceed by confirming the installation with `y` to install the required packages.

 4- **Activate the Environment:**
  
 Activate the newly created environment project_name_env using:
 
 `mamba activate project_name_env`
 
 Once activated, the active environment will be indicated in your command prompt within parentheses or brackets, such as       `(project_name_env) $`.   
 
 5- **Install Packages:**
 
 - Install required packages using `mamba install <package_name>` within the activated environment.

## Install the Prerequisite packages for regional-mom6-tools
Users can follow the steps below to install the requisite packages used by regional-mom6-tools.
```
mamba create -n setup python=3.10
mamba activate setup
mamba install -c conda-forge xarray dask netCDF4 h5py bottleneck matplotlib scipy pandas PyYAML cartopy xskillscore utide gsw colorcet cmcrameri xesmf
pip3 install git+https://github.com/raphaeldussin/HCtFlood.git
```
## Install Copernicus Marine Service toolbox CLI
If users experience issues with Copernicus Marine Service toolbox CLI (`copernicusmarine`), We recommend installing the Copernicus Marine package in a new, isolated Conda/Mamba environment. Users can use the `CEFI-regional-MOM6/tools/initial/copernicusmarine-env.yml` to install `copernicusmarine` in a new conda environment using the following command:
```
conda deactivate
cd tools
conda env create --file initial/copernicusmarine-env.yml
conda activate cmc
copernicusmarine login
username : YOUR Copernicus USERNAME
password : YOUR Copernicus PASSWORD
```
Then you can use the example script `CEFI-regional-MOM6/tools/initial/get_glorys_data.sh` to donwload the Glorys data for your desired local domain and time period. Always answer `Y` when asked for confirmation to overwrite credentials.
