"""
Compare Winter and spring surface chlorophyll a anomalies during El Niño years 
How to use:
python enso_chl.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import colorcet
from matplotlib.colors import SymLogNorm
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import pandas as pd
import xarray
import xesmf
import xskillscore

PC = ccrs.PlateCarree()

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../physics'))
from plot_common import add_ticks, corners, open_var, save_figure


def get_score(m, o, weight, metric=xskillscore.spearman_r):
    x = m.sel(xh=slice(-99, -70), yh=slice(18, 40))
    y = o.sel(xh=slice(-99, -70), yh=slice(18, 40))
    w = weight.sel(xh=slice(-99, -70), yh=slice(18, 40))
    score = float(metric(x, y, dim=['yh', 'xh'], skipna=True, weights=w))
    return score


def plot_enso_chl(pp_root, label):
    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    model = open_var(pp_root, 'ocean_cobalt_omip_sfc', 'chlos') * 1e6 # mg/m3
    model_seasonal = model.sel(time=slice('1997-09-01', '2019-11-30')).resample(time='1Q-NOV').mean('time')
    model_anom = model_seasonal.groupby('time.month') - model_seasonal.groupby('time.month').mean('time')

    # https://www.cpc.ncep.noaa.gov/data/indices/
    # Seasonal ERSSTv5 (centered base periods) "Oceanic Niño Index" or the 3-month running average in Niño 3.4 (5oNorth-5oSouth) (170-120oWest))
    oni = pd.read_csv('../data/climate/oni.ascii.txt', sep='\s+')

    pos_years = []
    neg_years = []
    for y in range(1997, 2019):
        winter = oni.loc[((oni.YR==y) & (oni.SEAS=='NDJ')), :]
        spring = oni.loc[(oni.YR==(y+1)) & (oni.SEAS=='MAM'), :]
        if float(winter.ANOM) > 0.5:
            if float(spring.ANOM) > 0:
                pos_years.append(y+1)
        elif float(winter.ANOM) < -0.5:
            if float(spring.ANOM) < 0:
                neg_years.append(y+1)

    print(pos_years)
    print(neg_years)

    model_winter_pos = model_anom.sel(time=((model_anom['time.month']==2) & (model_anom['time.year'].isin(pos_years))))
    model_winter_neg = model_anom.sel(time=((model_anom['time.month']==2) & (model_anom['time.year'].isin(neg_years))))
    model_spring_pos = model_anom.sel(time=((model_anom['time.month']==5) & (model_anom['time.year'].isin(pos_years))))
    model_spring_neg = model_anom.sel(time=((model_anom['time.month']==5) & (model_anom['time.year'].isin(neg_years))))

    satellite = xarray.open_mfdataset('/work/acr/occci-v6.0/monthly/*.nc').chlor_a
    satellite = satellite.sel(time=slice('1997-09-01', '2019-11-30'))
    satellite_seasonal = satellite.resample(time='1Q-NOV').mean('time')
    satellite_anom = satellite_seasonal.groupby('time.month') - satellite_seasonal.groupby('time.month').mean('time')
    sat_winter_pos = satellite_anom.sel(time=((satellite_anom['time.month']==2) & (satellite_anom['time.year'].isin(pos_years))))
    sat_winter_neg = satellite_anom.sel(time=((satellite_anom['time.month']==2) & (satellite_anom['time.year'].isin(neg_years))))
    sat_winter_pos = sat_winter_pos.load()
    sat_winter_neg = sat_winter_neg.load()

    sat_spring_pos = satellite_anom.sel(time=((satellite_anom['time.month']==5) & (satellite_anom['time.year'].isin(pos_years))))
    sat_spring_neg = satellite_anom.sel(time=((satellite_anom['time.month']==5) & (satellite_anom['time.year'].isin(neg_years))))
    sat_spring_pos = sat_spring_pos.load()
    sat_spring_neg = sat_spring_neg.load()

    sat_lonc, sat_latc = corners(satellite.lon, satellite.lat)

    satellite_grid = {
        'lon': satellite.lon, 
        'lat': satellite.lat,
        'lon_b': sat_lonc,
        'lat_b': sat_latc
    }

    model_grid2 = {
        'lon': model_grid.geolon,
        'lat': model_grid.geolat,
        'lon_b': model_grid.geolon_c,
        'lat_b': model_grid.geolat_c
    }
    oc_to_mom = xesmf.Regridder(satellite_grid, model_grid2, method='conservative_normed')

    weight = model_grid.areacello
    met = xskillscore.spearman_r

    common = dict(cmap='BrBG', norm=SymLogNorm(0.1, linscale=.5, vmin=-.8, vmax=.8))
    ticks = np.arange(-.8, .81, .1)
    label_ticks = ['-0.8', '-0.1', '0', '0.1', '0.8']

    fig = plt.figure(figsize=(8, 10))
    nrows, ncols = 4, 2
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(nrows, ncols),
        axes_class = (GeoAxes, dict(projection=PC)),
        axes_pad=0.33,
        cbar_location='bottom',
        cbar_mode='single',
        cbar_pad=0.3,
        cbar_size='10%',
        label_mode=''
    )

    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_winter_pos.mean('time'), **common)
    grid[0].set_title('(a) Model DJF El Niño')

    p1 = grid[1].pcolormesh(sat_lonc, sat_latc, sat_winter_pos.mean('time'), **common)
    grid[1].set_title('(b) OC-CCI DJF El Niño')

    score = get_score(model_winter_pos.mean('time'), oc_to_mom(sat_winter_pos.mean('time')), weight, metric=met)
    grid[1].text(-97, 37, f'rho: {score:2.2f}')

    p0 = grid[2].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_spring_pos.mean('time'), **common)
    grid[2].set_title('(c) Model MAM El Niño')

    p1 = grid[3].pcolormesh(sat_lonc, sat_latc, sat_spring_pos.mean('time'), **common)
    grid[3].set_title('(d) OC-CCI MAM El Niño')
    score = get_score(model_spring_pos.mean('time'), oc_to_mom(sat_spring_pos.mean('time')), weight, metric=met)
    grid[3].text(-97, 37, f'rho: {score:2.2f}')

    grid[4].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_winter_neg.mean('time'), **common)
    grid[4].set_title(r'(e) Model DJF La Niña')

    grid[5].pcolormesh(sat_lonc, sat_latc, sat_winter_neg.mean('time'), **common)
    grid[5].set_title('(f) OC-CCI DJF La Niña')
    score = get_score(model_winter_neg.mean('time'), oc_to_mom(sat_winter_neg.mean('time')), weight, metric=met)
    grid[5].text(-97, 37, f'rho: {score:2.2f}')

    grid[6].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_spring_neg.mean('time'), **common)
    grid[6].set_title(r'(g) Model MAM La Niña')

    grid[7].pcolormesh(sat_lonc, sat_latc, sat_spring_neg.mean('time'), **common)
    grid[7].set_title('(h) OC-CCI MAM La Niña')
    score = get_score(model_spring_neg.mean('time'), oc_to_mom(sat_spring_neg.mean('time')), weight, metric=met)
    grid[7].text(-97, 37, f'rho: {score:2.2f}')

    for ax in grid.cbar_axes:
        cbar = ax.colorbar(p0, extend='both')
        cbar.ax.set_xlabel('Surface chl a\nanom. (mg m$^{-3}$)')
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f'{t:1.1f}' if f'{t:1.1f}' in label_ticks else '' for t in ticks])

    for i, ax in enumerate(grid):
        xl = yl = 0
        if i >= nrows * ncols - 2:
            xl = 1
        if (i - 1) % 2 == 0:
            yl = 1
        add_ticks(ax, xticks=np.arange(-100, -31, 5), yticks=np.arange(0, 61, 5), xlabelinterval=xl, ylabelinterval=yl, fontsize=9)
        ax.set_xlim(-99, -70)
        ax.set_ylim(18, 40)
        ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)
    
    save_figure('enso_chl_log', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_enso_chl(args.pp_root, args.label)
