import numpy as np
from os import path
import xarray


# Directory containing the padded surface pressure and 2 m dewpoint.
# Also where the calculated 2 m specific humidity will be saved.  
WORK = '/work/acr/era5/padded/'

# Functions for humidity borrowed and adapted from MetPy

def mixing_ratio(partial_press, total_press, molecular_weight_ratio=0.622):
    return (molecular_weight_ratio * partial_press
                / (total_press - partial_press))


def specific_humidity_from_mixing_ratio(mr):
    return mr / (1 + mr)


def saturation_vapor_pressure(temperature):
    sat_pressure_0c = 6.112e2 # Pa
    return sat_pressure_0c * np.exp(17.67 * (temperature - 273.15) # K -> C
                                        / (temperature - 29.65))   # K -> C


def saturation_mixing_ratio(total_press, temperature):
    return mixing_ratio(saturation_vapor_pressure(temperature), total_press)


def process_year(y):
    pair = xarray.open_dataarray(path.join(WORK, f'ERA5_sp_{y}_padded.nc')) # Pa
    tdew = xarray.open_dataarray(path.join(WORK, f'ERA5_d2m_{y}_padded.nc')) # K

    smr = saturation_mixing_ratio(pair, tdew)
    sphum = specific_humidity_from_mixing_ratio(smr)

    sphum.name = 'sphum'
    sphum = sphum.to_dataset()

    fout = path.join(WORK, f'ERA5_sphum_{y}_padded.nc')

    # Remove all _FillValue
    all_vars = list(sphum.data_vars.keys()) + list(sphum.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}

    # Also fix the time encoding
    encodings['time'].update({'dtype':'float64', 'calendar': 'gregorian', 'units': 'hours since 1900-01-01 00:00:00'})

    sphum.to_netcdf(
        fout,
        format='NETCDF3_64BIT',
        engine='netcdf4',
        encoding=encodings,
        unlimited_dims=['time']
    )
    sphum.close()


if __name__ == '__main__':
    for y in range(1993, 2021):
        print(y)
        process_year(y)
