"""
Compare the 0-200 m average mesozooplankton biomass climatology between model and Observations from the COPEPOD dataset
How to use:
python zooplankton.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
import cartopy.crs as ccrs
import colorcet
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from string import ascii_lowercase
import xarray

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../physics'))
from plot_common import add_ticks, corners, open_var

PC = ccrs.PlateCarree()



def plot_zooplankton(pp_root, label):
    seasonal_obs = []
    for i, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        season_data = pd.read_csv(f'/net2/acr/copepod/copepod-2012__biomass-fields/data/copepod-2012__cmass-m{i+13}-qtr.csv', index_col=['Latitude', 'Longitude'])
        season_data = season_data['Total Carbon Mass (mg-C/m3)'].to_xarray()
        season_data['season'] = s
        seasonal_obs.append(season_data)
        
    seasonal_obs = xarray.concat(seasonal_obs, dim='season')
    seasonal_obs = seasonal_obs.rename({'Latitude': 'lat', 'Longitude': 'lon'})
    seasonal_obs *= 2.0 # correction for underestimation
    xcorner, ycorner = corners(seasonal_obs.lon, seasonal_obs.lat)

    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    depth = model_grid['deptho']

    mesozoo = open_var(pp_root, 'ocean_cobalt_tracers_int', 'mesozoo_200')
    mesozoo_climo = mesozoo.groupby('time.season').mean('time').load() * (106 / 16) * 12 * 1000 # mg C
    mesozoo_vol = mesozoo_climo / np.clip(depth, None, 200)

    norm = colors.LogNorm(vmin=1, vmax=200)
    cmap = colorcet.cm.CET_L9

    common = dict(cmap=cmap, norm=norm )

    f, axs = plt.subplots(4, 4, figsize=(12, 12), subplot_kw=dict(projection=PC))

    for col, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        # mom6
        for row in [0, 2]:
            p = axs[row, col].pcolormesh(
                model_grid.geolon_c, 
                model_grid.geolat_c, 
                mesozoo_vol.sel(season=s).squeeze(), 
                **common
            )
            i = row*4 + col
            axs[row, col].set_title(f'({ascii_lowercase[i]}) {s} model', fontsize=11)
        
        # copepod
        for row in [1, 3]:
            axs[row, col].pcolormesh(xcorner, ycorner, seasonal_obs.sel(season=s), **common)
            i = row*4 + col
            axs[row, col].set_title(f'({ascii_lowercase[i]}) {s} COPEPOD', fontsize=11)
            axs[row, col].coastlines('50m')
    
        yl = 1 if s == 'SON' else 0
        # top 2 
        for row in [0, 1]:
            add_ticks(axs[row, col], xticks=np.arange(-100, -31, 5), yticks=np.arange(0, 61, 5), xlabelinterval=1, ylabelinterval=yl, fontsize=7)
            axs[row, col].set_xlim(-82, -59)
            axs[row, col].set_ylim(25, 46)
        
        # bottom 2
        for row in [2, 3]:
            add_ticks(axs[row, col], xticks=np.arange(-100, -31, 5), yticks=np.arange(0, 61, 5), xlabelinterval=1, ylabelinterval=yl, fontsize=7)
            axs[row, col].set_xlim(-98.5, -79.5)
            axs[row, col].set_ylim(18, 33)
        
    
    f.subplots_adjust(bottom=0.23, wspace=0.1, hspace=.3)
    cbax = f.add_axes([0.3, 0.15, 0.4, 0.02])
    cb = f.colorbar(p, cax=cbax, orientation='horizontal', extend='max')
    cb.set_ticks([1, 2, 5, 10, 20, 50, 100, 200])
    cb.set_ticklabels([1, 2, 5, 10, 20, 50, 100, 200])
    cb.ax.set_title('0-200 m mesozooplankton biomass (mg C m$^{-3}$)')

    for ax in axs.flat:
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_facecolor('#999999')
        for s in ax.spines.values():
            s.set_visible(False)

    if label == '':            
        plt.savefig('figures/mesozoo.png', dpi=200, bbox_inches='tight')
    else:
        plt.savefig('figures/mesozoo.png', dpi=200, bbox_inches='tight')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_zooplankton(args.pp_root, args.label)
