"""
1. Compare monthly climatology of sea ice concentration from the model and a satellite observation dataset
2. Time series of the extent of sea ice within the Gulf of St Lawrence during January, February, and March from the
model and the satellite observation dataset
How to use:
python seaice.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod/ 
"""
from calendar import month_name
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import colorcet
import json
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import pandas as pd
from scipy.io import loadmat
from shapely.geometry import Polygon, MultiPoint
from shapely.prepared import prep
from string import ascii_lowercase
import xarray
import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../'))
from plot_common import open_var, get_map_norm, save_figure

PC = ccrs.PlateCarree()


def plot_seaice(pp_root, label):
    obs_mat = loadmat('/work/mib/raw_data/NSIDC/NASATEAM_v1.1_2021/sic.mat')
    nt = len(obs_mat['time'].squeeze())
    ny, nx = obs_mat['x'].shape
    mask = obs_mat['ifXY'].astype('bool').reshape(-1, order='F')
    # Gymnastics to convert from 2D (time, space) with no missing data
    # to 3D (time, y, x) with masked missing data
    obs_ice = np.zeros((nt, ny*nx)) * np.nan
    nused = 0
    for i in range(len(mask)):
        if mask[i]:
            obs_ice[:, i] = obs_mat['data'][nused, :]
            nused += 1
    obs_ice = xarray.DataArray(
        obs_ice.reshape((nt, ny, nx), order='F'), 
        dims=['time', 'y', 'x'], 
        coords={
            'time': pd.date_range('1979-01', freq='1MS', periods=nt),
        }
    )
    # Same for ice area
    obs_area = np.zeros((ny*nx)) * np.nan
    nused = 0
    for i in range(len(mask)):
        if mask[i]:
            obs_area[i] = obs_mat['w'][nused, 0]
            nused += 1
    obs_area = xarray.DataArray(
        obs_area.reshape((ny, nx), order='F'), 
        dims=['y', 'x'], 
    )

    # Model climatology
    model_grid = xarray.open_dataset('../../data/geography/ocean_static.nc')
    conc = open_var(pp_root, 'ice_monthly', 'siconc')
    model_conc = conc.groupby('time.month').mean('time').load()

    # Observed climatology
    obs_conc = obs_ice.sel(time=slice('1993', '2019')).groupby('time.month').mean('time')

    axes_class = (GeoAxes, dict(projection=ccrs.PlateCarree(central_longitude=-75)))
    cmap, norm = get_map_norm('cet_CET_CBL3', np.arange(0, 101, 10), no_offset=True)

    fig = plt.figure(figsize=(10, 10))
    grid = AxesGrid(fig, 111,
        axes_class=axes_class,
        nrows_ncols=(5, 2),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )
    for i, m in enumerate([12, 1, 2, 3, 4]):
        month = month_name[m]
        ax = grid[i*2]
        p = ax.pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_conc.sel(month=m)*100, transform=PC, cmap=cmap, norm=norm)
        ax.set_title(f'({ascii_lowercase[i*2]}) Model {month}')
        
        ax = grid[i*2 +1]
        p = ax.pcolormesh(obs_mat['x'], obs_mat['y'], obs_conc.sel(month=m), transform=PC, cmap=cmap, norm=norm)
        ax.set_title(f'({ascii_lowercase[i*2+1]}) Observed {month}')
        
        if i <= 1:
            cbar= grid.cbar_axes[i].colorbar(p)
            cbar.ax.set_xlabel('Mean sea ice concentration (%)')

    for ax in grid:
        ax.set_extent([-74, -46, 43, 56])
        ax.set_facecolor('#cccccc')
        for s in ax.spines.values():
            s.set_visible(False)

    if label == '':
        plt.savefig('../figures/sea_ice_concentration.png', dpi=200, bbox_inches='tight')
    else:
        plt.savefig(f'../figures/sea_ice_concentration_{label}.png', dpi=200, bbox_inches='tight')

    # ---
    # Time series of extent within Gulf of St Lawrence

    with open('../../data/geography/gsl.json') as f:
        border = json.load(f)

    poly = Polygon(border['features'][0]['geometry']['coordinates'][0][0])
    polyp = prep(poly)
    xvals = model_grid.geolon.values.ravel()
    yvals = model_grid.geolat.values.ravel()
    model_points = MultiPoint([(x, y) for x, y in zip(xvals, yvals)])
    model_gsl_mask = np.fromiter((polyp.contains(p) for p in model_points.geoms), bool, count=len(model_points.geoms)).reshape(model_grid.geolon.shape)
    # Area where concentration > 15 %
    model_area = (conc > 0.15).rename({'yT': 'yh', 'xT': 'xh'}) * model_grid.areacello
    model_total = model_area.where(model_gsl_mask).sum(['yh', 'xh'])

    xvals = obs_mat['x'].ravel()
    yvals = obs_mat['y'].ravel()
    obs_points = MultiPoint([(x, y) for x, y in zip(xvals, yvals)])
    obs_gsl_mask = np.fromiter((polyp.contains(p) for p in obs_points.geoms), bool, count=len(obs_points.geoms)).reshape(obs_mat['x'].shape)
    obs_total = ((obs_ice > 15).where(obs_gsl_mask)*obs_area).sum(['y', 'x'])
    
    plot_df = pd.concat((model_total.to_series().resample('1MS').first(), obs_total.to_series()), axis=1, keys=['Model', 'Observed'])
    f, axs = plt.subplots(3, 1, figsize=(10, 8))
    f.subplots_adjust(hspace=0.35)
    for i, mon in enumerate([1, 2, 3]):
        month_df = plot_df.loc[plot_df.index.month == mon] / 1e6 # -> km^2
        corr = month_df.corr().loc['Model', 'Observed']
        axs[i].plot(month_df.index.year, month_df.Model, c='r', label='Model')
        axs[i].plot(month_df.index.year, month_df.Observed, c='k', label=f'Observed (r={corr:2.2f})')
        axs[i].set_xlim(1979, 2021)
        axs[i].set_ylim(0, 300000)
        axs[i].legend(loc='lower left', frameon=False, ncol=2)
        axs[i].set_title(f'({ascii_lowercase[i]}) {month_name[mon]} sea ice extent in Gulf of St. Lawrence') 
        axs[i].set_ylabel('Ice extent (km$^2$)')
    
    save_figure('gsl_extent', label=label, pdf=True, output_dir='../figures')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_seaice(args.pp_root, args.label)
