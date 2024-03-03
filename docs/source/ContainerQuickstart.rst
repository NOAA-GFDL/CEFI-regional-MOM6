.. _QuickstartC:

====================================
Container-Based Quick Start Guide
====================================

This Container-Based Quick Start Guide will help users build and run the 1D case for the MOM6-SIS2-COBALT System using a `Singularity/Apptainer <https://apptainer.org/docs/user/1.2/introduction.html>`__ container. The :term:`container` approach provides a uniform enviroment in which to build and run the MOM6-SIS2-COBALT. Normally, the details of building and running the MOM6-COBALT vary from system to system due to the many possible combinations of operating systems, compilers, :term:`MPIs <MPI>`, and package versions available. Installation via container reduces this variability and allows for a smoother MOM6-SIS2-COBALT build experience. 

The basic "1D" case described here builds a MOM6-COBALT for the Bermuda Atlantic Time-series Study (BATS) with OM4 single column configuration as well as COBALTV3.0.

Prerequisites 
-------------------

Users must have either Docker (recommended for personal Windows/macOS systems) or Singularity/Apptainer (recommended for users working on Linux, NOAA Cloud, or HPC systems).

Install Docker on Windows/macOS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To build and run the MOM6-SIS2-COBALT using a Docker container, first install the software according to the `Docker Installation Guide for Windows <https://docs.docker.com/desktop/install/windows-install/>`__ or `Docker Installation Guide for macOS <https://docs.docker.com/desktop/install/mac-install/>`__. 

Install Singularity/Apptainer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   As of November 2021, the Linux-supported version of Singularity has been `renamed <https://apptainer.org/news/community-announcement-20211130/>`__ to *Apptainer*. Apptainer has maintained compatibility with Singularity, so ``singularity`` commands should work with either Singularity or Apptainer (see compatibility details `here <https://apptainer.org/docs/user/1.2/introduction.html>`__.)

To build and run the MOM6-COBALT using a Singularity/Apptainer container, first install the software according to the `Apptainer Installation Guide <https://apptainer.org/docs/admin/1.2/installation.html>`__. This will include the installation of all dependencies.

Build and run 1-D example using Docker 
-----------------------------------------
User can follow the following steps to build and run MOM6-SIS2-COBALT 1-D case within a Docker container.

.. code-block::

   #Assume user is under $HOME 
   docker pull clouden90/1d_mom6_cobalt:base #This will pull docker image to your local machine
   git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive #git clone CEFI-regional-MOM6 repo
   cd $HOME/CEFI-regional-MOM6/exps
   wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz
   cd $HOME
   docker run --rm -v $HOME:/work -it clouden90/1d_mom6_cobalt:v0.1 bash --login # run docker container interactively
   cd /work/CEFI-regional-MOM6/builds
   ./linux-build.bash -m docker -p linux-gnu -t repro -f mom6sis2 #build MOM6-SIS2-COBALT
   cd /work/CEFI-regional-MOM6/exps
   cd OM4.single_column.COBALT
   mpirun -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/repro/MOM6SIS2


Build and run 1-D example using Singularity/Apptainer container
-----------------------------------------
For users working on systems with limited disk space in their ``/home`` directory, it is recommended to set the ``SINGULARITY_CACHEDIR`` and ``SINGULARITY_TMPDIR`` environment variables to point to a location with adequate disk space. For example:

.. code-block:: 

   export SINGULARITY_CACHEDIR=/absolute/path/to/writable/directory/cache
   export SINGULARITY_TMPDIR=/absolute/path/to/writable/directory/tmp

where ``/absolute/path/to/writable/directory/`` refers to a writable directory (usually a project or user directory within ``/lustre``, ``/work``, ``/scratch``, or ``/glade`` on NOAA RDHPC systems). If the ``cache`` and ``tmp`` directories do not exist already, they must be created with a ``mkdir`` command.

Then User can follow the following steps to build and run MOM6-SIS2-COBALT 1-D case within a Singularity/Apptainer container.
.. code-block::

   #Assume user is under $HOME 
   cd $HOME 
   singularity pull 1d_mom6_cobalt.sif docker://clouden90/1d_mom6_cobalt:base #pull docker image and convert to sif
   git clone https://github.com/NOAA-GFDL/CEFI-regional-MOM6.git --recursive #git clone CEFI-regional-MOM6 repo 
   cd $HOME/CEFI-regional-MOM6/exps
   wget ftp.gfdl.noaa.gov:/pub/Yi-cheng.Teng/1d_datasets.tar.gz && tar -zxvf 1d_datasets.tar.gz && rm -rf 1d_datasets.tar.gz
   cd $HOME 
   singularity shell -B $HOME:/work -e $HOME/1d_mom6_cobalt.sif # start singularity/apptainer container interactively
   cd /work/CEFI-regional-MOM6/builds
   ./linux-build.bash -m docker -p linux-gnu -t repro -f mom6sis2 #build MOM6-SIS2-COBALT
   cd /work/CEFI-regional-MOM6/exps
   cd OM4.single_column.COBALT
   mpirun -np 1 ../../builds/build/docker-linux-gnu/ocean_ice/repro/MOM6SIS2
