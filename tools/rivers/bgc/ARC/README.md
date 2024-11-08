## Example Scripts for ARC BGC runoff generation 

This folder contains example scripts for ARC BGC runoff file generation. Users can follow the following instructions to generate BGC runoff file:

1: Generate a monthly climatology of the river inputs on the model grid
using `make_discharge_climatology.m`.  This routine creates a monthly climatology
from the model's freshwater forcing.  For example, the default uses GLOFAS/HILL
forcing files created by Kate Hedstrom on 5/11/2023.  All you need to do to
regenerate files (or create new ones) is update the file path.  The file creates
a matlab file (`*.mat`) with the discharge climatology.  This is used in the
assignment of rivers to discharge points.
```
matlab232 -nodisplay -nosplash -nodesktop -r "run('make_discharge_climatology_arctic.m');exit;"
```

2: Use `mapriv_NEWS2.m` to create a river nutrient input file based on the
GlobalNEWS2 estimates (Mayorga et al., 2010).  GlobalNEWS contains a 
database of global rivers with empirically-derived nutrient inputs.  GlobalNEWS
does not, however, have DIC or alkalinity so it cannot be used to provide forcing for
carbon cycling.  Also, while globalNEWS is quite skilfull globally, it can 
have significant regional biases.  Nonetheless, the routine provides a good
way to identify major rivers in the region, and the comprehensive nutrient
estimates that it provides will eventually be used to fill in gaps in river
forcing drawn from direct observations.

More details about the mapping algorithm can be found below (and in the code). 
The first time through, I would recommend setting `inspect_map1` to `y`.
This allows you to step through the mapping of each river and assess its 
quality and properties.  I have also found that applying a minimum discharge
of 100 m3 sec-1 helps avoid erroneous mapping of very small rivers onto
large discharges.  The assignment algorithm was designed to be relatively
insensitive to such instances, but care should still be taken. 

The required inputs are the discharge climatology (from step 1) and a copy
of the globalNEWS data.
```
matlab232 -nodisplay -nosplash -nodesktop -r "run('mapriv_NEWS2.m');exit;"
```

3: Gather/Process direct river measurements: The next step is to get as many
direct measurements as you can.

 - [RC4USCoast](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.nodc:0260455)
```
mkdir -p Data/RC4USCoast 
cd Data/RC4USCoast 
wget https://www.ncei.noaa.gov/archive/archive-management-system/OAS/bin/prd/jquery/download/260455.3.3.tar.gz
tar -xzf 260455.3.3.tar.gz --wildcards --strip-components=4 -C . "*/data/0-data/*.nc"
```

 - [GLORICH](https://www.geo.uni-hamburg.de/en/geologie/forschung/aquatische-geochemie/glorich.html)
```
cd Data/GLORICH
wget https://store.pangaea.de/Publications/HartmannJens-etal_2019/Glorich_V01_CSV_plus_Shapefiles_2019_05_24.zip 
unzip Glorich_V01_CSV_plus_Shapefiles_2019_05_24.zip
matlab232 -nodisplay -nosplash -nodesktop -r "run('Arctic_GLORICH_Process.m');exit;"
```

 - [ArcticGro](https://arcticgreatrivers.org/data/)
```
# A copy of this dataset is provided in the Data directory.
# You may want to download your own to ensure
# that it is up-to-date.
cd Data/ArcticGro
matlab232 -nodisplay -nosplash -nodesktop -r "run('ArcticGro_Process.m');exit;"
```
4: run `mapriv_combined_Arctic` to create river nutrient and carbon input
estimates based on available observation, while using GlobalNEWS to fill in
some gaps. 
```
cp /archive/ynt//woa_sst_climo.nc ./Data/
matlab232 -nodisplay -nosplash -nodesktop -r "run('mapriv_combined_Arctic.m');exit;"
```
As was the case for globalNEWS2, I recommend running these with "inspect_map = 'y'" until
you are satisfied with the results.  You can just "click through" each river mapping and 
confirm its properties.  The routine will then produce numerous final plots for analysis
and quality control, before generating the netcdf for use with MOM6.

Note: River oxygen levels are set at saturating levels at temperatures provided by the 
World Ocean Atlas Climatology.
___________________________________________________________________________________________

## RIVER MAPPING ALGORITHM: 
Rivers are first filtered to isolate those within the domain and
above a user specified flow threshold.  The rationale for this threshold is to minimize the 
risk of inadvertantly mapping very small rivers onto large freshwater flows.  Small rivers
tend to have more volatile nutrient concentrations, so such mistakes can have large consequences.
To further reduce this risk, rivers are then sorted by size from smallest to largest.  Model
outflow points nearest to each river are accumulated until the the value closest to the observed
flow is reached.  These points are assigned the concentration for that river.  If a larger river
subsequently claims those points, the larger river is given precedence.  The concentrations of
any model discharge points left unassigned after all estimates have been cycled through
are assigned using a nearest neighbor algorithm.

## Note: 
One must specify the fraction of particulate phosphorus that is bioavailable (generally between
10-30%, Froelich, Kinetic control of dissolved phosphate in natural rivers and estuaries: A primer
on the phosphate buffer mechanism, Limnology and Oceanography), and the fraction of dissolved organic
inputs that fall into labile, semi-labile and semi-refractory pools.  This is set by default to 30%, 35%,
and 35%.  This is consistent with the range of bio-availability suggested by Weigner et al. (2006),
Bio-availability of dissolved organic nitrogen and carbon from 9 rivers in the eastern US, Aquatic
Microbial Ecology.

## VISUALIZATION AND QUALITY CONTROL: 
The routines include a y/n toggle option for inspecting the
mapping of each river as it is done.  If "inspect_map" is set to 'y', a graphical map of the
model discharge point assigned to each river is presented, along with the outflow and nutrient
characteristics of the river.  This can be useful for identifying rivers that may require some
manual editing to ensure the outflow is assigned to the right place.  A section for such manual
edits is provided in the code.  The visualization pauses until the user presses any key.  It 
then moves onto the next river.  Once all the rivers have been mapped and interpolation completed,
the routine always produces a series of domain-wide plots to evaluate the overall results.
