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
   * - esm4_*.nc
     - Atmospheric BGC fluxes from ESM4 simulation

.. _grid-files:  

------------------------------------
Grid Description files
------------------------------------

The input files containing grid information for regional MOM6-SIS2-COBALT configurations are listed and described in :numref:`Table %s <GridFiles>`.
Users are referred to this `link <https://github.com/jsimkins2/nwa25/blob/main/misc/gridgen/nwa12_grid_generation.ipynb>`__ for more details on how to create grid files for their domain of interest.

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
   * - \*\*\*\*\_mosaic\_tile1X\*\*\*\*\_mosaic\_tile1.nc 
     - grid files for the FMS coupler 

.. _td-files:  

------------------------------------
Time-dependent files
------------------------------------

The time-dependent files such as ICs, BCs or atmos forcings for regional MOM6-SIS2-COBALT configurations are listed and described in :numref:`Table %s <TdFiles>`.
The script used to generate this file is shown in parentheses.

.. _TdFiles:

.. list-table:: *Time-dependent files for regional MOM6-SIS2-COBALT configurations*
   :widths: 40 50
   :header-rows: 1

   * - Filename
     - Description
   * - glorys_ic_1993-01-01.nc
     - ocean physical initial conditions from Glorys (tools/initial/write_glorys_initial.py)   
   * - NWA12_COBALT_2023_10_spinup_2003.nc
     - ocean biogeochemical initial conditions (tools/initial/write_bgc_initial.py)    
   * - so_*.nc, thetao_*.nc, zos_*.nc, uv_*.nc 
     - Open boundary conditions for physical variables (tools/boundary/write_glorys_boundary.py)   
   * - bgc_esper_1993_2022.nc
     - Open boundary conditions for ALK and DIC (tools/boundary/write_bgc_boundary.py; Prerequisite: tools/boundary/esper/run_esper.sh)    
   * - ERA5_*.nc
     - atmos forcings from ERA5 (tools/atmos)
   * - glofas_runoff_****.nc
     - River runoff from GloFAS data (tools/rivers/write_runoff_glofas.py)    
   * - RiverNutrients_Integrated_NWA12_GLOFAS_RC4US1990to2022_2023_04_v2.nc
     - Biogeochemical tracer concentrations for river runoff 
   * - mole_fraction_of_co2_extended_ssp245.nc
     - mole fraction of carbon dioxide in atmos


.. _model_configureFile:

---------------------------
Model_configure files
---------------------------

The model configuration files for regional MOM6-SIS2-COBALT configurations are listed and described in :numref:`Table %s <ModelConfig>`.

.. _ModelConfig:

.. list-table:: *Model configuration files*
   :widths: 40 50
   :header-rows: 1

   * - Filename
     - Description
   * - input.nml
     - Fortran namelist file containing parameters that control model run.
   * - MOM_input
     - This input file provides the adjustable run-time parameters for MOM6
   * - MOM_override
     - Override MOM6 run-time parameters 
   * - MOM_layout
     - Control MOM6 model's layout
   * - SIS_input
     - This input file provides the adjustable run-time parameters for SIS2
   * - SIS_override
     - Override SIS2 run-time parameters 
   * - SIS_layout
     - Control SIS2 model's layout
   * - field_table
     - An ASCII table that is used to register tracer fields
   * - diag_table
     - An ASCII table that is used to control model outputs
   * - data_table
     - An ASCII file that is used to control external data forcing fields, such as surface forcings or river runoff

The best practice when configuring a new simulation or tuning parameters is to make all changes in the MOM_override or SIS_override files. Not all parameters need to be specified within MOM_input, if no value is given the default will be used. See the MOM_parameter_doc file described in the next section to find the default value of the parameter. When using the MOM_override file to set a parameter which is not defined in the MOM_input file, it can be set as ``PARAMETER = Value`` within the MOM_override file. To override a parameter that is specified within the MOM_input file, the prefix ``#override`` must be included, so an overridden value would be specified as ``#override PARAMETER = Value``. Only one parameter per line should be specified within the override file. MOM and SIS input and override files follow the same formatting guidelines. 

The data_table is commonly formatted by specifying each of the fields in the order listed below, with a new line for each entry.

| ``gridname``: The component of the model this data applies to. eg. `atm` `ocn` `lnd` `ice`.
| ``fieldname_code``: The field name according to the model component. eg. `salt`
| ``fieldname_file``: The name of the field within the source file.
| ``file_name``: Path to the source file.
| ``interpol_method``: Interpolation method eg. `bilinear`
| ``factor``: A scalar by which to multiply the field ahead of passing it onto the model. This is a quick way to do unit conversions for example.

Example Format:

.. code-block:: console

   "ATM", "t_bot",  "t2m", "./INPUT/2t_ERA5.nc", "bilinear", 1.0


Users can also set a constant value by entering empty quotes for ``fieldname_file`` and ``file_name`` and setting ``interpol_method`` to ``none``. Below is an example of setting a constant atmospheric oxygen value:

.. code-block:: console

   "ATM", "o2_flux_pcair_atm",  "",       "",                           "none",      0.214

=============
Outputs
=============    

Model output is controlled via the FMS diag_manager using the ``diag_table``. 

The diag_table file has three kinds of section: Title, File and Field. The title section is mandatory and always the first. There can be multiple file and field sections typically either in pairs or grouped in to all files and all fields, but always with the file section preceding the corresponding field section.

.. _TitleSec:

---------------------------
Title Section
---------------------------

The first two lines are mandatory and comprise a line with a title and a line with six integers defining a base date against which time will be referenced.

.. code-block:: console

   "My  ocean-only  test  case"
   1900  1  1  0  0  0

.. _FileSec:

---------------------------
File Section
---------------------------

This section defines an arbitrary number of files that will be created. Each file is limited to a single rate of either sampling or time-averaging.

.. code-block:: console
   
   "file_name",  output_freq,  "output_freq_units",  file_format,  "time_axis_units",  "time_axis_name"

These file section entries are described in :numref:`Table %s <FileDescription>`.   

.. _FileDescription:

.. list-table:: *Description of the variables used to define the files written to the output files.*
   :widths: 40 50 
   :header-rows: 1

   * - Field Entry
     - Description
   * - file_name
     - The name of the file that contains diagnostics at the given frequency (excluding the “.nc” extension).
   * - output_freq
     - The period between records in ``file_name``, if positive. Special values of 0 mean write every time step and -1 write only at the end of the run.
   * - output_freq_units
     - The units in which ``output_freq`` is given. Valid values are “years”, “months”, “days”, “hours”, “minutes” or “seconds”.
   * - file_format
     - Always set to 1, meaning netcdf.
   * - time_axis_units
     - The units to use for the time-axis in the file. Valid values are “years”, “months”, “days”, “hours”, “minutes” or “seconds”.
   * - time_axis_name
     - The name of the time-axis (usually “Time”).


.. _FieldeSec:

---------------------------
Field Section
---------------------------


A line in the field section of the ``diag_table`` file contains eight variables with the following format:

.. code-block:: console

   "module_name", "field_name", "output_name", "file_name", "time_sampling", "reduction_method", "regional_section", packing

These field section entries are described in :numref:`Table %s <FieldDescription>`.

.. _FieldDescription:

.. list-table:: *Description of the eight variables used to define the fields written to the output files.*
   :widths: 16 24 55
   :header-rows: 1

   * - Field Entry
     - Variable Type
     - Description
   * - module_name
     - CHARACTER(len=128)
     - Module that contains the field_name variable.  (e.g. dynamic, gfs_phys, gfs_sfc)
   * - field_name
     - CHARACTER(len=128)
     - The name of the variable as registered in the model.
   * - output_name
     - CHARACTER(len=128)
     - Name of the field as written in file_name.
   * - file_name
     - CHARACTER(len=128)
     - Name of the file where the field is to be written.
   * - time_sampling
     - CHARACTER(len=50)
     - Currently not used.  Please use the string "all".
   * - reduction_method
     - CHARACTER(len=50)
     - "none” means sample or snapshot. “average” or “mean” performs a time-average. “min” or “max” diagnose the minium or maxium over each time period.       
   * - regional_section
     - CHARACTER(len=50)
     - “none” means global output. A string of six space separated numbers, “lon_min lon_max lat_min lat_max vert_min vert_max”, limits the diagnostic to a region.
   * - packing
     - INTEGER
     - Fortran number KIND of the data written.  Valid values:  1=double precision, 2=float, 4=packed 16-bit integers, 8=packed 1-byte (not tested).

A brief example of the diag_table is shown below. 

.. code-block:: console

   CEFI_NWA12_COBALT_V1
   1993 1 1 0 0 0
   # MOM6 ocean diagnostics files
   "ocean_daily",            1, "days",   1, "days", "time"
   "ocean_month_snap",       1, "months", 1, "days", "time"
   "ocean_month",            1, "months", 1, "days", "time"
   "ocean_month_z",          1, "months", 1, "days", "time"
   "ocean_annual",          12, "months", 1, "days", "time"
   "ocean_annual_z",        12, "months", 1, "days", "time"
   "ocean_static",          -1, "months", 1, "days", "time" # ocean_static is a protected name. Do not change this line.
   # -----------------------------------------------------------------------------------------
   "ocean_model_z", "volcello",     "volcello",         "ocean_annual_z",      "all", "mean", "none",2 # Cell measure for 3d data
   "ocean_model_z", "volcello",     "volcello",         "ocean_month_z",       "all", "mean", "none",2 # Cell measure for 3d data
   "ocean_model",   "volcello",     "volcello",         "ocean_annual",        "all", "mean", "none",2 # Cell measure for 3d data
   "ocean_model",   "pbo",          "pbo",              "ocean_annual",        "all", "mean", "none",2
   "ocean_model",   "pbo",          "pbo",              "ocean_month",         "all", "mean", "none",2
   "ocean_model",   "masscello",    "masscello",        "ocean_annual",        "all", "mean", "none",2
   "ocean_model",   "ssh",          "ssh",              "ocean_annual",        "all", "mean", "none",2
   "ocean_model",   "zos",          "zos",              "ocean_month",         "all", "mean", "none",2
   "ocean_model",   "ssh",          "ssh",              "ocean_month",         "all", "mean", "none",2
   "ocean_model",   "ssh",          "ssh",              "ocean_daily",         "all", "mean", "none",2

.. _ParameterFiles:

---------------------------
Parameter Files
---------------------------

In additon to model output, MOM6 also records runtime parameters used during the model intialization. Each parameter_doc file includes different information. 

.. list-table:: *Parameter Doc Files*
   :widths: 40 50
   :header-rows: 1

   * - Filename
     - Description
   * - MOM_parameter_doc.all
     - The values of all run-time parameters for MOM6 and their defaults
   * - MOM_parameter_doc.short
     - The values of only run-time parameters for MOM6 that differ from their defaults
   * - MOM_parameter_doc.debugging
     - The values of only run-time parameters used for debugging MOM6 
   * - MOM_parameter_doc.layout
     - The values of only run-time parameters that control MOM6 model's layout
   * - SIS_parameter_doc.all
     - The values of all run-time parameters for SIS2 and their defaults
   * - SIS_parameter_doc.short
     - The values of only run-time parameters for SIS2 that differ from their defaults
   * - SIS_parameter_doc.debugging
     - The values of only run-time parameters used for debugging SIS2 
   * - SIS_parameter_doc.layout
     - The values of only run-time parameters that control SIS2 model's layout

To easily see how experiments differ, the MOM_parameter_doc files can be compared. These files include short descriptions of what parameters control, their default, and different options. 


