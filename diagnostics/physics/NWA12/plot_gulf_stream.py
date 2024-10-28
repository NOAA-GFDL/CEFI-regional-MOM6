"""
Plot of the Gulf Stream position and index,
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python plot_gulf_stream.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
import xarray
import xesmf
import pandas as pd
import numpy as np
import cartopy.feature as feature
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

# Need to append physics dir to path to access plot common
import sys
sys.path.append("..")
from plot_common import open_var, add_ticks, save_figure

def compute_gs(ssh, data_grid=None):
    lons = np.arange(360-72, 360-51.9, 1)
    lats = np.arange(36, 42, 0.1)
    target_grid = {'lat': lats, 'lon': lons}

    if data_grid is None:
        data_grid = {'lat': ssh.lat, 'lon': ssh.lon}

    ssh_to_grid = xesmf.Regridder(
        data_grid,
        target_grid,
        method='bilinear'
    )

    # Interpolate the SSH data onto the index grid.
    regridded = ssh_to_grid(ssh)

    # Find anomalies relative to the calendar month mean SSH over the full model run.
    anom = regridded.groupby('time.month') - regridded.groupby('time.month').mean('time')

    # For each longitude point, the Gulf Stream is located at the latitude with the maximum SSH anomaly variance.
    stdev = anom.std('time')
    amax = stdev.argmax('lat').compute()
    gs_points = stdev.lat.isel(lat=amax).compute()

    # The index is the mean latitude of the Gulf Stream, divided by the standard deviation of the mean latitude of the Gulf Stream.
    index = ((anom.isel(lat=amax).mean('lon')) / anom.isel(lat=amax).mean('lon').std('time')).compute()

    # Move times to the beginning of the month to match observations.
    monthly_index = index.to_pandas().resample('1MS').first()
    return monthly_index, gs_points

def plot_gulf_stream(pp_root, label):

    # Load Natural Earth Shapefiles
    _LAND_50M = feature.NaturalEarthFeature(
        'physical', 'land', '50m',
        edgecolor='face',
        facecolor='#999999'
    )

    # Get model grid
    model_grid = xarray.open_dataset(  '../../data/geography/ocean_static.nc' )

    # Get model thetao data TODO: maki this comment better
    model_thetao = open_var(pp_root, 'ocean_monthly_z', 'thetao')

    if '01_l' in model_thetao.coords:
        model_thetao = model_thetao.rename({'01_l': 'z_l'})

    model_t200 = model_thetao.interp(z_l=200).mean('time')

    # Ideally would use SSH, but some diag_tables only saved zos
    try:
        model_ssh = open_var(pp_root, 'ocean_monthly', 'ssh')
    except:
        print('Using zos')
        model_ssh = open_var(pp_root, 'ocean_monthly', 'zos')
        
    model_ssh_index, model_ssh_points = compute_gs(
        model_ssh,
        data_grid=model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'})
    )
    
    # Get Glorys data
    glorys_t200 = xarray.open_dataarray('../../data/diagnostics/glorys_T200.nc')
    
    # Get satellite points
    #satellite_ssh_index, satellite_ssh_points = compute_gs(satellite['adt'])
    #satellite_ssh_points.to_netcdf('../data/obs/satellite_ssh_points.nc')
    #satellite_ssh_index.to_pickle('../data/obs/satellite_ssh_index.pkl')
    #read pre-calculate satellite_ssh_index and points
    satellite_ssh_points = xarray.open_dataset('../../data/obs/satellite_ssh_points.nc')
    satellite_ssh_index = pd.read_pickle('../../data/obs/satellite_ssh_index.pkl')
    satellite_rolled = satellite_ssh_index.rolling(25, center=True, min_periods=25).mean().dropna()

    #satellite = xarray.open_mfdataset([f'/net2/acr/altimetry/SEALEVEL_GLO_PHY_L4_MY_008_047/adt_{y}_{m:02d}.nc' for y in range(1993, 2020) for m in range(1, 13)])
    #satellite = satellite.rename({'longitude': 'lon', 'latitude': 'lat'})
    #satellite = satellite.resample(time='1MS').mean('time')

    # Get rolling averages and correlations
    model_rolled = model_ssh_index.rolling(25, center=True, min_periods=25).mean().dropna()
    corr = pd.concat((model_ssh_index, satellite_ssh_index), axis=1).corr().iloc[0, 1]
    corr_rolled = pd.concat((model_rolled, satellite_rolled), axis=1).corr().iloc[0, 1]

    # Plot of Gulf Stream position and index based on SSH,
    # plus position based on T200.
    fig = plt.figure(figsize=(10, 6), tight_layout=True)
    gs = gridspec.GridSpec(2, 2, hspace=.25)

    # Set projection of input data files so that data is correctly tranformed when plotting
    proj = ccrs.PlateCarree()

    ax = fig.add_subplot(gs[0, 0], projection = proj)
    ax.add_feature(_LAND_50M)
    ax.contour(model_grid.geolon, model_grid.geolat, model_t200, levels=[15], colors='r')
    ax.contour(glorys_t200.longitude, glorys_t200.latitude, glorys_t200, levels=[15], colors='k')
    add_ticks(ax, xlabelinterval=5)
    ax.set_extent([-82, -50, 25, 41])
    ax.set_title('(a) Gulf Stream position based on T200')
    custom_lines = [Line2D([0], [0], color=c, lw=2) for c in ['r', 'k']]
    ax.legend(custom_lines, ['Model', 'GLORYS12'], loc='lower right', frameon=False)

    ax = fig.add_subplot(gs[0, 1], projection = proj)
    ax.add_feature(_LAND_50M)
    ax.plot(model_ssh_points.lon-360, model_ssh_points, c='r')
    ax.plot(satellite_ssh_points.lon-360, satellite_ssh_points['__xarray_dataarray_variable__'], c='k')
    add_ticks(ax, xlabelinterval=5)
    ax.set_extent([-82, -50, 25, 41])
    ax.set_title('(b) Gulf Stream position based on SSH variance')
    ax.legend(custom_lines, ['Model', 'Altimetry'], loc='lower right', frameon=False)

    ax = fig.add_subplot(gs[1, :])
    model_ssh_index.plot(ax=ax, c='#ffbbbb', label='Model')
    satellite_ssh_index.plot(ax=ax, c='#bbbbbb', label=f'Altimetry (r={corr:2.2f})')
    model_rolled.plot(ax=ax, c='r', label='Model rolling mean')
    satellite_rolled.plot(ax=ax, c='k', label=f'Altimetry rolling mean (r={corr_rolled:2.2f})')
    ax.set_title('(c) Gulf Stream index based on SSH variance')
    ax.set_xlabel('')
    ax.set_ylim(-3, 3)
    ax.set_ylabel('Index (positive north)')
    ax.legend(ncol=4, loc='lower right', frameon=False, fontsize=8)

    # default to saving figures in current dir instead of dedicated figures dir
    save_figure('gulfstream_eval', label=label, pdf=True, output_dir='../figures/')

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_gulf_stream(args.pp_root, args.label)
