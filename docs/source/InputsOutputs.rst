.. _InputsOutputs:

*****************************************************
Data: Input, Model Configuration, and Output Files
*****************************************************

This chapter describes the input and model configuration files needed for executing the MOM6-SIS2-COBALT model.

=============
Input files
=============

There are four types of files needed to execute a run: 

   #. Static datasets (*fix* files containing climatological information)
   #. Grid Description files      
   #. Files that depend on time such as initial/boundary conditions 
   #. Model configuration files (such as namelists)

.. _fix-files:   

------------------------------------
Static Datasets (i.e., *fix files*)
------------------------------------

The static input files for regional MOM6-SIS2-COBALT configurations are listed and described in :numref:`Table %s <FixFiles>`. The script used to generate this file is shown in parentheses.

.. _FixFiles:

.. list-table:: *Fix files containing climatological information *
   :widths: 40 50
   :header-rows: 1

   * - Filename
     - Description
   * - seawifs-clim-1997-2010.nwa12.nc
     - climatological chlorophyll concentration
   * - bgc_woa.nc
     - climatological open boundary conditions for bgc tracers such as no3, po4, sio4, and o2 (tools/boundary/write_bgc_boundary.py)  
   * - bgc_cobalt.nc
     - climatological open boundary conditions for bgc tracers not are not included in bgc_woa.nc or bgc_esper_1993_2022.nc (tools/boundary/write_bgc_boundary.py) 
   * - tz_00*.nc
     - open boundary conditions for tidal amplitude for each tidal constituent (tools/boundary/write_tpxo_boundary.py)
   * - tu_00*.nc
     - open boundary conditions for tidal current for each tidal constituent (tools/boundary/write_tpxo_boundary.py) 

.. _grid-files:  

------------------------------------
Grid Description files
------------------------------------

The input files containing grid information for regional MOM6-SIS2-COBALT configurations are listed and described in :numref:`Table %s <GridFiles>`.

.. _GridFiles:

.. list-table:: *Input files containing grid information for regional MOM6-SIS2-COBALT configurations*
   :widths: 40 50
   :header-rows: 1

   * - Filename
     - Description
   * - ocean_hgrid.nc
     - horizonal grid information       
   * - ocean_mosaic.nc
     - specify horizonal starting and ending points index
   * - ocean_topog.nc
     - ocean topography
   * - ocean_mask.nc
     - land/sea mask
   * - land_mask.nc
     - land fraction at T-cell centers
   * - vgrid_75_2m.nc
     - vertical coordinate level thickness
   * - diag_dz.nc
     - specify target depth for diag outputs
   * - grid_spec.nc
     - Contains information on the mosaic grid
   * - ****_mosaic_tile1X****_mosaic_tile1.nc
     - grid files for the FMS coupler  
