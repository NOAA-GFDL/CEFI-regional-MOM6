import numpy as np
import xarray
import xesmf

from cefi_kit.grids import hgrid_to_xesmf, mom_center_area

from HCtFlood import kara as flood

hgrid = xarray.open_dataset('../../datasets/grid/ocean_hgrid.nc')
mom_grid = hgrid_to_xesmf(hgrid)
mom_area = mom_center_area(hgrid.area)

# https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/ocn/mom/tx0.25v1/
seawifs = xarray.open_dataset(
    '../../datasets/opacity/seawifs-clim-1997-2010.1440x1080.v20180328.nc',
    decode_times=False
)

flooded = flood.flood_kara(seawifs['chlor_a'], xdim='i', ydim='j').drop('z').squeeze()

seawifs_grid = {
    'lon': seawifs.lon,
    'lat': seawifs.lat,
    'lon_b': seawifs.lon_crnr,
    'lat_b': seawifs.lat_crnr
}

seawifs_to_mom = xesmf.Regridder(seawifs_grid, mom_grid, method='conservative', reuse_weights=False)
regridded = seawifs_to_mom(flooded)
regridded_named = regridded.rename('chlor_a')
ds = regridded_named.to_dataset().transpose('time', 'nyp', 'nxp').rename({'nxp': 'xh', 'nyp': 'yh'})
ds['area'] = (('yh', 'xh'), mom_area.values)
ds['lon_crnr'] = (('yq', 'xq'), mom_grid['lon_b'].values)
ds['lat_crnr'] = (('yq', 'xq'), mom_grid['lat_b'].values)
ds['xh'] = (('xh'), np.arange(len(ds['xh']), dtype=np.int32))
ds['yh'] = (('yh'), np.arange(len(ds['yh']), dtype=np.int32))
ds['xh'].attrs['cartesian_axis'] = 'X'
ds['yh'].attrs['cartesian_axis'] = 'Y'

all_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
encodings = {v: {'_FillValue': None} for v in all_vars}

ds.to_netcdf(
    './seawifs-clim-1997-2010.nwa12.nc',
    encoding=encodings,
    format='NETCDF3_64BIT',
    unlimited_dims='time'
)
