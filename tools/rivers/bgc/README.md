## Example Scripts for BGC runoff generation 

This folder contains example scripts for BGC runoff file generation. Users can follow the following instructions to generate BGC runoff file:
```
# 1. First run write_glofas_ave.py to get climatological monthly runoff
./write_glofas_ave.py 

# 2. run mapriv_NEWS2_NWA12_GLOFAS.m to map Global NEWS nutrient data onto the MOM6 NWA grid 
matlab -nodisplay -nosplash -nodesktop -r "run mapriv_NEWS2_NWA12_GLOFAS"

# 3. run mapriv_combined_NWA12_GLOFAS to map USGS nutrient data onto the MOM6 NWA grid 
matlab -nodisplay -nosplash -nodesktop -r "mapriv_combined_NWA12_GLOFAS"

``` 

## Datasets for river chemistry 

Users can follow `mapriv_combined_NWA12_GLOFAS.m` to implement new datasets for the specific region they are interested in.
Below are some common dataset, users are also welcome to add thier datasets here. 

  - [RC4USCoast](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.nodc:0260455)
