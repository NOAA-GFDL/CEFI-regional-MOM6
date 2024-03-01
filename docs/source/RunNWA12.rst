.. _RunNWA12:

====================================
Run the MOM6-COBALT-NWA12 example
====================================

This chapter guides users without Gaea access on how to run the MOM6-COBALT-NWA12 example. It assumes that users have already :ref:`built the MOM6-SIS2-COBALT <BuildMOM6>` successfully. If users have access to Gaea, we recommend using the FRE workflow (XML file and instructions can be found `here <https://github.com/NOAA-GFDL/CEFI-regional-MOM6/tree/feature/doc/xmls>`__).


.. _NWA12COBALT:

MOM6-COBALT-NWA12 v1.0 example
==========================================

This example provides users with an opportunity to become familiar with the model configurations. This example closely follows the recent publication by :cite:t:`RossEtAl2023` (2023). Users interested in detailed physical and biogeochemical model configurations should refer to this publication.

.. _DownloadData:

Download the model input dataset
======================================

The dataset for the MOM6-COBALT-NWA12 (retrospective run from year 1993) is publicly available. Follow the steps below to download the dataset:

.. code-block:: console

   cd CEFI-regional-MOM6/exps
   wget https://gfdl-med.s3.amazonaws.com/OceanBGC_dataset/nwa12_datasets.tar.gz
   tar -zxvf nwa12_datasets.tar.gz

This dataset contains all the necessary model input files (e.g. grid files, ICs, BCs, atmospheric forcings, river dischages, BGC fluxes from atmosphere). Most of these input files can be generated using the tools under ``CEFI-regional/MOM6/tools``. Please be aware that this dataset is quite large (51 GB), so please be patient while downloading it.

Users interested in the model inputs, outputs, and configurations should refer to :ref:`Data: Input, Model Configuration, and Output Files <InputsOutputs>`.

After downloading the dataset, continue to the :ref:`next section <RunNWA12EXP>` to run the NWA12 example. 

.. _RunNWA12EXP:

Run NWA12 Experiment
=====================

To run the NWA12 example, first navigate to the ``exps/NWA12.COBALT`` folder: 

.. code-block:: console

   cd ../exps/NWA12.COBALT
   cp ./../builds/build/YOUR_MACHINE_DIRECTORY-NAME_OF_YOUR_mk_FILE/ocean_ice/repro/MOM6SIS2 .

Use the following command to run the NWA-12 example on Gaea using SLURM:   

.. code-block:: console

   sbatch run.sub

Users may need to modify the run script according to their HPC machine configurations. The default configuration uses 1646 CPU cores to run the NWA12 example. If users want to change it to their desired number of CPU cores (e.g., 20x20 = 400 cores), they can modify both ``MOM_layout`` and ``SIS_layout`` by removing the mask_table and editing the LAYOUT:   

.. code-block:: console

   #override IO_LAYOUT = 1,1
   #override LAYOUT    = 20,20

Also, please ensure to modify your run script according to the changes in the model layout.

Users can also use the `FRE-NCtools <https://github.com/NOAA-GFDL/FRE-NCtools>`__ to create their own mask_table to avoid wasting a lot of computational resources. The command for a 20x20 mask would be like the following:

.. code-block:: console

   check_mask --grid_file ocean_mosaic.nc --ocean_topog ocean_topog.nc --layout 20,20
