.. _BuildMOM6:

====================================
Build the MOM6-SIS2-COBALT
====================================

To build the MOM6-SIS2-COBALT, users will complete the following steps:

   #. :ref:`Install prerequisites <StackInfo>`
   #. :ref:`Clone the CEFI-regional-MOM6 from GitHub <DownloadMOM6>`
   #. :ref:`Set up the build environment and build the executables <BuildExecutables>`

.. _StackInfo:

Install the Prerequisite Softwares 
==========================================

.. note::

   **Conda warning**: Before you install anything or try to build the model, make sure to deactivate your `conda` environment because it could interfere with brew and the model build process.

Users on any sufficiently up-to-date machine with a UNIX-based operating system should be able to install the prerequisite software and build the MOM6-SIS2-COBALT. Users can follow the commands below to install the prerequisite software with admin access or ask their HPC helpdesks for any issues related to the installation of the prerequisite software.

.. code-block:: console

   # Linux system such as Ubuntu 
   sudo apt update
   sudo apt install make gfortran git git-lfs tcsh netcdf-bin libnetcdf-dev libnetcdff-dev openmpi-bin libopenmpi-dev

   # MacOS, install Homebrew from terminal and install the prerequisite software
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install make
   brew install gfortran
   brew install openmpi
   brew install netcdf
   brew install netcdf-fortran
   brew install wget
   brew install git
   brew install git-lfs

For **Windows users**, we recommend installing `WSL <https://learn.microsoft.com/en-us/windows/wsl/install>`__ (Windows Subsystem for Ubuntu and Linux), and following the above steps to install the prerequisite software. Alternatively users can opt for the Docker container approach. See :ref:`Container-Based Quick Start Guide <QuickstartC>` for more details.

After completing installation, continue to the :ref:`next section <DownloadMOM6>` to download the CEFI-regional-MOM6. 

.. _DownloadMOM6:

Download the CEFI-regional-MOM6 Code
======================================
The CEFI-regional-MOM6 source code is publicly available on GitHub. To download the code (including submodules), clone the **main** branch of the repository:

.. code-block:: console

   git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive 

The cloned repository contains files and sub-directories shown in :numref:`Table %s <FilesAndSubDirs>`. 

.. _FilesAndSubDirs:

.. list-table:: Files and Subdirectories of the *CEFI-regional-MOM6* Repository
   :widths: 20 50
   :header-rows: 1

   * - File/Directory Name
     - Description
   * - LICENSE.md 
     - A copy of the Gnu lesser general public license, version 3
   * - README.md
     - This file with basic pointers to more information
   * - src
     - Contains the source code for MOM6-SIS2-COBALT model 
   * - builds
     - Contains build script to build MOM6-SIS2-COBALT
   * - diagnostics
     - Contains scripts that can be utilized for analyzing model results after postprocessing
   * - exps
     - Contains 1D MOM6-SIS2-COBALT example and other CEFI regional configurations
   * - tools
     - Contains preprocessing scripts that can be used to generate model input files
   * - xmls
     - Contains FRE xml files designed for running the CEFI-regional-MOM6 workflow on Gaea   
   * - docs
     - Contains release notes, documentation, and User's Guide

.. _BuildExecutables:

Set Up the Environment and Build the Executables
=================================================== 

After download the source code, users can navigate to the ``builds`` directory and create a folder for your machine configurations:

.. code-block:: console

   cd CEFI-regional-MOM6/builds
   mkdir YOUR_MACHINE_DIRECTORY
   cd YOUR_MACHINE_DIRECTORY

The ``YOUR_MACHINE_DIRECTORY`` should contain two files: ``NAME_OF_YOUR_mk_FILE.env`` and ``NAME_OF_YOUR_mk_FILE.mk`` (e.g. gnu.env and gnu.mk or somthing similiar). The ``NAME_OF_YOUR_mk_FILE.env`` file is mainly used for the HPC system to allow you to ``module load`` necessary software to build the model. In most cases, if you already have gfortran (or intel compiler), mpi (openmpi or mpich), and netcdf installed on your system, the ``NAME_OF_YOUR_mk_FILE.env`` file can be left blank.

The NAME_OF_YOUR_mk_FILE.mk file may be different depends on your system configurations (e.g. Intel v.s. GNU compilers). We already have a few examples within the builds folder. Users can also find more general templates `here <https://github.com/NOAA-GFDL/mkmf/tree/af34a3f5845c5781101567e043e0dd3d93ff4145/templates>`__. Below are some recommended templates:

.. _mkmftempDescription:

.. table:: Recommended mkmf templates

   +------------------------+---------------------------------------------------------------------------------+
   | **Platform/Compiler**  | **Template**                                                                    |
   +========================+=================================================================================+
   | gaea (Intel)           | mkmf/templates/ncrc5-intel-classic.mk                                           |
   +------------------------+---------------------------------------------------------------------------------+
   | MacOS (GNU)            | CEFI-regional-MOM6/builds/MacOS/osx-gnu.mk                                      |
   +------------------------+---------------------------------------------------------------------------------+
   | Ubuntu (GNU)           | mkmf/templates/linux-ubuntu-trusty-gnu.mk                                       |
   +------------------------+---------------------------------------------------------------------------------+

Once the two files are created, use the following command to build the model (Make sure to use correct names that are consistent with both your machine folder and your mk/env files):  

.. code-block:: console

   cd CEFI-regional-MOM6/builds
   ./linux-build.bash -m YOUR_MACHINE_DIRECTORY -p NAME_OF_YOUR_mk_FILE -t repro -f mom6sis2

If the build completes successfully, you should be able to find the executable here: ``builds/build/YOUR_MACHINE_DIRECTORY-NAME_OF_YOUR_mk_FILE/ocean_ice/repro/MOM6SIS2``  

Run an Experiment
=====================

To test your ``MOM6SIS2``, first navigate to the ``exps`` folder: 

.. code-block:: console

   cd ../exps

Download the model input files:

.. code-block:: console

   wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz

Navigate to the 1-D example:

.. code-block:: console

   cd OM4.single_column.COBALT

Use the following command to run the 1-D example:    

.. code-block:: console
 
   mpirun -np 1 ../../builds/build/YOUR_MACHINE_DIRECTORY-NAME_OF_YOUR_mk_FILE/ocean_ice/repro/MOM6SIS2
