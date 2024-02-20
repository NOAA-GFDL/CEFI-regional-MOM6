.. _Diags:

====================================
Analysis output
====================================

The ``CEFI-regional-MOM6/diagnostics`` folder contains python scripts that can be used to analyze modeled physical and biogeochemical results. 
Please contact the code manager `Yi-cheng.Teng <yi-cheng.teng@noaa.gov>`_ if you have any queations.

.. note::

   At this point, all the scripts require model outputs that are post-processed by FRE. Users with GFDL PPAN access should be able to use these scripts directly. We are still working on a containerized approach for the post-processing process and will update once it is available.


To run the diagnostics scripts, users can follow the steps below:

   #. :ref:`Prerequisite <Prerequisite>`
   #. :ref:`Diagnostics for Physical Components <Diagsphy>`
   #. :ref:`Diagnostics for Biogeochemical Components <Diagsbiogeo>`

.. _Prerequisite:

Prerequisite
==========================================

All the diagnostics scripts are written in Python. Users can follow this `instruction <https://github.com/NOAA-GFDL/CEFI-regional-MOM6/tree/feature/doc/tools#readme>`_ to create a `conda` environment to run these scripts.

.. _Diagsphy:


Diagnostics for Physical Components
==========================================

All the diagnostics scripts related to the physical components are located within ``CEFI-regional-MOM6/diagnostics/physics``. Users can check the header of each file to learn how to use these scripts. Make sure you create ``figures`` folder before running the scripts.

The :numref:`Table %s <Diagsphytable>` below provides short descriptions for scripts related to physical components

.. _Diagsphytable:

.. list-table:: Descriptions of diagnostics scripts for *Physical Components*
   :widths: 20 50
   :header-rows: 1

   * - File Name
     - Description
   * - sst_eval.py 
     - Compare model SST with 1993--2019 data from OISST and GLORYS
   * - sst_trends.py
     - Compare the model 2005-2019 SST trends from OISST and GLORYS
   * - sss_eval.py
     - Compare model SSS with 1993--2019 data from regional climatologies and GLORYS
   * - ssh_eval.py
     - Compare model SSH with 1993--2019 data from GLORYS
   * - mld_eval.py
     - Compare model MLD with climatologies from Holte et al. 2017 and de Boyer 2022     
   * - compute_tides_job.sh
     - Compare modeled tidal amplitude and phase with TPXO9 data
   * - NWA12/coldpool.py
     - Compare bottom temperature from the model and du Pontavice et al.(2022) in the cold-pool region averaged over June-September  
   * - NWA12/nechannel.py
     - Plot model-data comparison for Northeast Channel temperature and salinity
   * - NWA12/seaice.py
     - Compare monthly climatology of sea ice concentration from the model and a satellite observation dataset    
   * - NWA12/tbot_epu.py
     - Compare annual average bottom-temperature anomalies in four different northeast US ecological production units from model,
       reanalysis, and observed data
   * - NWA12/temp_profile.py
     - Compare model vertical profiles of seasonal temperature climatologies in four different northeast US ecological production units from Glorys data

.. _Diagsbiogeo:

Diagnostics for Biogeochemical Components
==========================================

All the diagnostics scripts related to the biogeochemical components are located within ``CEFI-regional-MOM6/diagnostics/biogeochemistry``. Users can check the header of each file to learn how to use these scripts. Make sure you create ``figures`` folder before running the scripts.

The :numref:`Table %s <Diagsbiogeotable>` below provides short descriptions for scripts related to biogeochemical components

.. _Diagsbiogeotable:

.. list-table:: Descriptions of diagnostics scripts for *biogeochemical Components*
   :widths: 20 50
   :header-rows: 1

   * - File Name
     - Description
   * - chl_eval.py
     - Compare model surface chla with data from occci-v6.0
   * - enso_chl.py
     - Compare Winter and spring surface chlorophyll a anomalies during El Niño years
   * - nutrients.py
     - Comparison of model seasonal mean surface phosphate and nitrate with the World Ocean Atlas data
   * - oa_metrics.py
     - Compare Mean surface alkalinity, dissolved inorganic carbon, and aragonite saturation statee between the model and the
       observation-derived climatology   
   * - zooplankton.py
     - Compare the 0-200 m average mesozooplankton biomass climatology between model and Observations from the COPEPOD dataset
   * - NWA12/hypoxic_area.py
     - Compare monthly climatologies of hypoxic area over the LA-TX Shelf between the model and geostatistical estimates from Matli et al. (2020) 
