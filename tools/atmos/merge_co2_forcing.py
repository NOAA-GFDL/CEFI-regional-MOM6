import xarray
import numpy as np
import pandas as pd


def overwrite_time(ds, starts, ends):
    """
    For a monthly dataset containing time and time_bnds,
    given an array starts containing len(ds.time) first days of the month
    and another matching array containing ends of the month/first days of the next month,
    overwrite time to be in the middle of the month,
    and use the starts and ends as the time bounds.
    """
    delta = ends - starts
    middles = starts + (delta / 2)
    ds['time'] = middles
    ds['time_bnds'] = (('time', 'bnds'), np.column_stack((starts, ends)))
    return ds


def main():
    # Historical forcing:
    hist = xarray.open_dataset(
        '/work/acr/input4mips/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_CMIP_UoM-CMIP-1-2-0_gr-0p5x360deg_000001-201412.nc',
        decode_times=False
    )

    # Slice to just the last 1200 times (= 100 years). Otherwise,
    # the times extend to 0000-01-01, which causes problems with xarray
    hist = hist.isel(time=slice(-1200, None))

    # Also rename the bnds variable to match the scenario dataset
    hist = hist.rename({'bound': 'bnds'})

    # Recreate the times in the dataset. It ends in Dec 2014 and is monthly.
    starts = pd.date_range(end='2014-12-01', periods=len(hist['time']), freq='1MS')
    ends = pd.date_range(end='2015-01-01', periods=len(hist['time']), freq='1MS')
    hist = overwrite_time(hist, starts, ends)

    # Scenario (ssp245) forcing:
    scenario = (
        xarray.open_dataset('/work/acr/input4mips/mole-fraction-of-carbon-dioxide-in-air_input4MIPs_GHGConcentrations_ScenarioMIP_UoM-MESSAGE-GLOBIOM-ssp245-1-2-1_gr-0p5x360deg_201501-250012.nc', decode_times=False)
        .isel(time=slice(0, 12*50)) # Select just first 50 years
    )

    # For the scenario, we know it starts in Jan 2015
    starts = pd.date_range(start='2015-01-01', periods=len(scenario['time']), freq='1MS')
    ends = pd.date_range(start='2015-02-01', periods=len(scenario['time']), freq='1MS')
    scenario = overwrite_time(scenario, starts, ends)

    # Bring the two together
    combined = xarray.merge([hist, scenario])

    # Add longitude coordinates to make sure FMS can read it. The actual data get repeated across longitude.
    combined['mole_fraction_of_carbon_dioxide_in_air'] = combined['mole_fraction_of_carbon_dioxide_in_air'].expand_dims({'lon': 5}, axis=-1)
    combined['lon'] = np.arange(-60.0, 301.0, 90.0)
    combined['lon'].attrs['axis'] = 'X'

    # Set how the data will be written out
    encodings = {k: {'_FillValue': 1.0e20} for k in list(combined.variables.keys())}
    encodings['time'].update({'dtype':'float64', 'calendar': 'gregorian', 'units': 'hours since 1915-01-01'})
    encodings['time_bnds'].update({'dtype':'float64', 'calendar': 'gregorian', 'units': 'hours since 1915-01-01'})
    encodings['lon'].update({'dtype':'float64'})

    combined.to_netcdf('mole_fraction_of_co2_extended_ssp245_v2.nc', encoding=encodings, unlimited_dims='time')


if __name__ == '__main__':
    main()
