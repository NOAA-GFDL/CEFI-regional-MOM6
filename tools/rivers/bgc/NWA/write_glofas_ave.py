#!/usr/bin/env python3
"""
This script generates climatological monthly runoff 
from the runoff files created by write_runoff_glofas.py
How to use:
./write_glofas_ave.py
"""
from scipy.io import savemat
import xarray


averages = []

for y in range(1993, 2020):
    print(y)
    ds = xarray.open_dataset(
        f'/work/acr/mom6/nwa12/glofas/glofas_runoff_{y}.nc',
        chunks=dict(time=100)
    )

    ave = (
        ds
        ['runoff']
        .sel(time=slice(f'{y}-01-01', f'{y}-12-31'))
        .groupby('time.month')
        .mean('time')
        .compute()
    )
    averages.append(ave)

all_average = xarray.concat(averages, dim='year').mean('year')
savemat(
    './glofas_runoff_mean.mat',
    {
        'lat_mod': ds.lat.values, 
        'lon_mod': ds.lon.values, 
        'area_mod': ds.area.values,
        'runoff': all_average.values
    }
)
