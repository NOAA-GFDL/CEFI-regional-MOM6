"""
Sample usage:
 sbatch compute_tides_job.sh 
"""
import argparse
import numpy as np
import utide
import xarray



def open_grid_file(grid_file):
    grid = xarray.open_dataset(grid_file)
    # if grid_file is an ocean_hgrid file,
    # define the geolon and geolat coordinates
    # in ocean_static style 
    if 'ocean_hgrid' in grid_file:
        grid = xarray.Dataset({
            'geolon_c': grid['x'][0::2, 0::2].rename({'nxp': 'xq', 'nyp': 'yq'}),
            'geolat_c': grid['y'][0::2, 0::2].rename({'nxp': 'xq', 'nyp': 'yq'}),
            'geolon': grid['x'][1::2, 1::2].rename({'nxp': 'xh', 'nyp': 'yh'}),
            'geolat': grid['y'][1::2, 1::2].rename({'nxp': 'xh', 'nyp': 'yh'})
        })
    return grid


def run(grid_file, hourly_input, output, subsample):
    grid = open_grid_file(grid_file)
    ds = xarray.open_dataset(hourly_input)

    # Use ssh as the sea level if it is in the file,
    # or zos if not
    ssh_var = 'ssh' if 'ssh' in ds else 'zos'
    assert ssh_var is not None

    # Make sure time is in utide friendly format
    # (probably not needed any more)
    if not isinstance(ds['time'].values[0], np.datetime64):
        ds['time'] = ds['time'].to_index().to_datetimeindex()

    for v in ['geolat', 'geolon', 'geolat_c', 'geolon_c']:
        ds[v] = grid[v]

    # Skip the first month to reduce spin up noise
    region = ds.isel(time=slice(31*24, None))

    # Subsample space and time to reduce computational time
    if subsample > 1:
        region = ds.isel(yh=slice(None, None, subsample), xh=slice(None, None, subsample))

    times = region.time
    selected = [
        # these are included in the model
        'M2', 'S2', 'N2', 'K2', 'K1', 'O1', 'P1', 'Q1', 'MM', 'MF',
        # some important interactions of the components in the model
        'M4', 'M6', 'MK3', 'S4', 'MN4', 'MS4'
    ]

    def get_tides(arr, lat):
        if np.all(np.isnan(arr)):
            # over land (all nan), don't compute and
            # just return nans
            con = np.tile(np.nan, len(selected))
            res = xarray.DataArray(
                np.vstack((con, con)),
                coords=[['A', 'g'], selected],
                dims=['variable', 'constit']
            )
        else:
            cons = utide.solve(
                times, 
                arr,
                lat=lat, 
                nodal=True, # set to False if nodal modulation was turned off in model
                trend=False, 
                verbose=False,
                constit=selected,
                conf_int='none',
                phase='Greenwich'
            )

            res = xarray.DataArray(
                np.vstack((cons['A'], cons['g'])),
                coords=[['A', 'g'], cons['name']],
                dims=['variable', 'constit']
            ).sel(constit=selected)
        
        return res

    tides = xarray.apply_ufunc(
        get_tides, 
        region[ssh_var],
        region.geolat,
        input_core_dims=[['time'], []],
        output_core_dims=[['variable', 'constit']],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[np.float64],
        output_sizes={'variable': 2, 'constit': len(selected)}
    )

    tides['constit'] = selected
    tides['variable'] = ['A', 'g']

    final = xarray.merge(
        (tides.sel(variable='A').reset_coords('variable', drop=True).rename('A'), 
        tides.sel(variable='g').reset_coords('variable', drop=True).rename('g')
        )
    )

    for v in ['geolat', 'geolon', 'geolat_c', 'geolon_c']:
        final[v] = region[v]

    final.to_netcdf(output)
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grid_file', type=str, help='Model ocean_hgrid or ocean_static file')
    parser.add_argument('hourly_input', type=str, help='Hourly model output containing ssh or zos')
    parser.add_argument('output', type=str, help='File to write the tidal output to')
    parser.add_argument('subsample', type=int, default=1, help='Number of grid points to subsample by for speed. Set to 1 for no subsampling. Setting to 5 will take ~1 hour to run, and 10 will take ~minutes.')
    args = parser.parse_args()
    run(args.grid_file, args.hourly_input, args.output, args.subsample)
