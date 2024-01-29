"""
Compare bottom temperature from the model and du Pontavice et al. (2022) in the cold-pool region averaged over June-September
How to use:
python coldpool.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray
import xesmf
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cmcrameri.cm as cmc

PC = ccrs.PlateCarree()

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../'))
from plot_common import add_ticks, annotate_skill, autoextend_colorbar, corners, get_map_norm, open_var, save_figure

def plot_coldpool(pp_root, label):
    model = open_var(pp_root, 'ocean_monthly', 'tob')
    model_grid = xarray.open_dataset('../../data/geography/ocean_static.nc')    
    hubert = xarray.open_dataarray('/net2/acr/hubert_bottom_temp/daily_bottom_temp_neus_1959_2019.nc')
    mom_to_hubert = xesmf.Regridder(
        model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}),
        hubert,
        method='bilinear'
    )
    interpolated_depth = mom_to_hubert(model_grid.deptho)

    # Use this period for climatology
    ymin = int(model['time.year'].min())
    ymax = int(model['time.year'].max())

    # June-Sep average for each year
    hubert_ave = hubert.sel(day=slice(152, 273), year=slice(1972, 2019)).mean('day')

    # Long-term June-Sep average
    hubert_climo = hubert_ave.mean('year')

    # Create mask where long-term average and coordinates meet criteria
    hubert_mask = ((hubert_climo < 10) & (interpolated_depth < 200) & (interpolated_depth > 20) & (hubert_climo.lat >= 38) & (hubert_climo.lat <= 41.5) & 
    (hubert_climo.lon > -75) & (hubert_climo.lon < -68.5) & (hubert_climo > 6))
    # Slice off the NE corner
    hubert_mask = hubert_mask.where((hubert_mask.lat <= 41) | (hubert_mask.lon < -70)).fillna(0)

    # Use a climatology that matches the model time period
    hubert_matching_climo = hubert_ave.sel(year=slice(ymin, ymax)).mean('year')
    hubert_cpi = (hubert_ave - hubert_matching_climo).where(hubert_mask).mean(['lat', 'lon'])
    
    # Interpolate model bottom temperature to Hubert's grid
    tbot_rg = mom_to_hubert(model)

    # Model June-Sep average for each year
    ave = tbot_rg.sel(time=np.logical_and(tbot_rg['time.month'] >= 6, tbot_rg['time.month'] <= 9)).resample(time='1AS').mean('time')

    # Long-term June-Sep average
    ltm = ave.mean('time')

    # Model cold pool index
    cpi = (ave - ltm).where(hubert_mask).mean(['lat', 'lon']).load()
    cpi['time'] = cpi['time.year']

    # Subtract model - obs over cold pool mask region
    delta = ltm.where(hubert_matching_climo.notnull()) - hubert_matching_climo

    fig = plt.figure(figsize=(10, 8), tight_layout=True)
    gs = gridspec.GridSpec(2, 3, hspace=.2)
    
    lonc, latc = corners(ltm.lon, ltm.lat)
    levels = np.arange(4, 26.1, 2)
    cmap, norm = get_map_norm('cmc.roma_r', levels, no_offset=True)
    common = dict(cmap=cmap, norm=norm)
    bias_levels = np.arange(-4, 4.1, 1)
    bias_cmap, bias_norm = get_map_norm('coolwarm', bias_levels, no_offset=True)

    ax = fig.add_subplot(gs[0, 0], projection=PC)
    p = ax.pcolormesh(lonc, latc, ltm.where(hubert_matching_climo.notnull()), **common)
    add_ticks(ax)
    ax.set_extent([-76, -68, 35, 42])
    ax.set_title('(a) Model')
    cbar = autoextend_colorbar(plt, p, orientation='horizontal', label='Bottom temp. (°C)', pad=0.13)

    ax = fig.add_subplot(gs[0, 1], projection=PC)
    p = ax.pcolormesh(lonc, latc, hubert_matching_climo, **common)
    add_ticks(ax)
    ax.set_extent([-76, -68, 35, 42])
    ax.set_title('(b) du Pontavice et al.')
    cbar = autoextend_colorbar(plt, p, orientation='horizontal', label='Bottom temp. (°C)', pad=0.13)

    ax = fig.add_subplot(gs[0, 2], projection=PC)
    p = ax.pcolormesh(lonc, latc, delta, cmap=bias_cmap, norm=bias_norm)
    cbar = autoextend_colorbar(plt, p, orientation='horizontal', label='Difference (°C)',  pad=0.13)
    add_ticks(ax)
    ax.set_extent([-76, -68, 35, 42])
    ax.set_title('(c) Model - du Pontavice')
    annotate_skill(
        ltm.where(hubert_matching_climo.notnull()), 
        hubert_matching_climo, 
        ax, 
        dim=['lat', 'lon'], 
        fontsize=8,
        x0=-72,
        y0=37,
        yint=0.5
    ) # weights

    ax = fig.add_subplot(gs[1, :])
    cpi.plot(ax=ax, c='r', label='Model')
    hubert_cpi.plot(ax=ax, c='k', label='du Pontavice et al.')
    ax.set_xlim(1970, 2020)
    ax.set_ylim(-3, 2)
    ax.set_xlabel('')
    ax.set_ylabel('Cold pool index (°C)')
    ax.set_title('(d) June-September cold pool index')
    ax.legend(frameon=False)
    r = pd.concat([cpi.to_series(), hubert_cpi.to_series()], axis=1, keys=['model', 'obs']).corr().loc['model', 'obs']
    ax.annotate(f'Corr: {r:2.2f}', (2013, -2.5))

    save_figure('coldpool_eval', label=label, pdf=True, output_dir='../figures')

    hubert_cpi.name = 'coldpool_index'
    cpi.name = 'coldpool_index'
    hubert_cpi.to_netcdf('../figures/obs_coldpool_index.nc')
    if label == '':
        cpi.to_netcdf(f'../figures/model_coldpool_index.nc')
    else:
        cpi.to_netcdf(f'../figures/{label}_coldpool_index.nc')



if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_coldpool(args.pp_root, args.label)
