"""
Compare model surface chla with data from occci-v6.0.
How to use:
python chl_eval.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import colorcet
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf
import matplotlib.colors as colors
from string import ascii_lowercase

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../physics'))
from plot_common import add_ticks, autoextend_colorbar, corners, annotate_skill, open_var, save_figure

PC = ccrs.PlateCarree()


def plot_chl(pp_root, label, dev):
    mom_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    model = open_var(pp_root, 'ocean_cobalt_omip_sfc', 'chlos') * 1e6 # kg m-3 -> mg m-3
    if dev:
        print('Using any available model data')
        model = model.sel(time=slice('1993-12-01', None)).isel(time=slice(None, -1))
    else:
        model = model.sel(time=slice('1997-09-01', '2019-11-30'))
    model_climo = model.groupby('time.season').mean('time')

    # Load pre-computed climatology, also using 1997-09-01 to 2019-11-30
    satellite = xarray.open_dataset('/work/acr/occci-v6.0/oc-cci_chl_19970901_20191130_climo.nc').chlor_a
    # Flip to right side up.
    # satellite = satellite.isel(lat=slice(None, None, -1))
    log_model = np.log10(np.maximum(model_climo, 1e-14))
    log_sat = np.log10(satellite)

    sat_lonc, sat_latc = corners(log_sat.lon, log_sat.lat)
    sat_grid = {'lon': log_sat.lon, 'lat': log_sat.lat, 'lon_b': sat_lonc, 'lat_b': sat_latc}
    model_grid = {'lon': mom_grid.geolon, 'lat': mom_grid.geolat, 'lon_b': mom_grid.geolon_c, 'lat_b': mom_grid.geolat_c}
    sat_to_model = xesmf.Regridder(sat_grid, model_grid,method='conservative_normed', unmapped_to_nan=True)
    sat_rg = sat_to_model(log_sat)
    delta = model_climo - np.power(10, sat_rg)

    # Full domain, including difference

    common = dict(cmap=colorcet.cm.CET_L16, norm=colors.LogNorm(vmin=0.125, vmax=8) )
    delta_common = dict(cmap='BrBG', norm=colors.SymLogNorm(.1, linscale=.1, vmin=-4, vmax=4))
    ticks = [-4, -2, -1, -0.5, -0.1, 0, 0.1, 0.5, 1, 2, 4]
    label_ticks = ['-4', '-2', '-0.5', '0', '0.5', '2', '4']
    fig = plt.figure(figsize=(8, 10))
    nrows, ncols = 4, 3
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(nrows, ncols),
        axes_class = (GeoAxes, dict(projection=PC)),
        axes_pad=0.33,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.3,
        cbar_size='10%',
        label_mode=''
    )

    for i, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        left = i * ncols
        # Model
        pleft = grid[left].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_climo.sel(season=s), **common)
        grid[left].set_title(f'({ascii_lowercase[left]}) {s} Model')
        # OC-CCI
        pmid = satellite.sel(season=s).plot(ax=grid[left+1], add_colorbar=False, **common)
        grid[left+1].set_title(f'({ascii_lowercase[left+1]}) {s} OC-CCI')
        # Difference
        pdiff = grid[left+2].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, delta.sel(season=s), **delta_common)
        annotate_skill(log_model.sel(season=s), sat_rg.sel(season=s), grid[left+2], dim=['yh', 'xh'], weights=mom_grid.areacello, fontsize=8)
        grid[left+2].set_title(f'({ascii_lowercase[left+2]}) {s} Model - OC-CCI')
        
    for ax in grid:
        ax.set_facecolor('#bbbbbb')
        ax.set_extent([-99, -35, 4, 55])
        for s in ax.spines.values():
            s.set_visible(False)
    
    # chl value color bars
    cbarleft = grid.cbar_axes[0].colorbar(pleft)
    cbarmid = grid.cbar_axes[1].colorbar(pmid, extend='max')
    for cbar in [cbarleft, cbarmid]:
        cbar.ax.set_xlabel('Surface chl (mg / m$^3$)')
        cbar.set_ticks([0.25, 0.5, 1, 2, 4, 8])
        cbar.set_ticklabels([0.25, 0.5, 1, 2, 4, 8])

    # difference color bar
    cbar = autoextend_colorbar(grid.cbar_axes[2], pdiff)
    cbar.ax.set_xlabel('Difference. (mg m$^{-3}$)')
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([t if str(t) in label_ticks else '' for t in ticks])
    save_figure('domain_chl', label=label)

    # Regional zooms

    f, axs = plt.subplots(4, 4, subplot_kw=dict(projection=PC), figsize=(10, 10))
    for i, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        # Model plots
        p = axs[0, i].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_climo.sel(season=s), **common)
        axs[2, i].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_climo.sel(season=s), **common)
        axs[0, i].set_title(f'({ascii_lowercase[i]}) {s} Model')
        axs[2, i].set_title(f'({ascii_lowercase[i+8]}) {s} Model')

        # Satellite NE US
        sat_region = satellite.sel(season=s).sel(lat=slice(60, 20), lon=slice(-90, -50))
        r_lonc, r_latc = corners(sat_region.lon, sat_region.lat)
        axs[1, i].pcolormesh(r_lonc, r_latc, sat_region, **common)
        axs[1, i].set_title(f'({ascii_lowercase[i+4]}) {s} OC-CCI')
        axs[1, i].add_patch(patches.Rectangle((-79.9, 45.1), 12.5, 8.2, alpha=0.4, facecolor='white', edgecolor='k', lw=1))
        sub = (mom_grid.geolon >= -80) & (mom_grid.geolon <= -53) & (mom_grid.geolat >= 33) & (mom_grid.geolat <= 53)
        # n\(xh=slice(-80, -53), yh=slice(33, 53))
        annotate_skill(
            log_model.sel(season=s).where(sub), 
            sat_rg.sel(season=s).where(sub), 
            axs[1, i], dim=['yh', 'xh'], 
            weights=mom_grid.areacello.where(sub).fillna(0), 
            fontsize=8,
            x0=-79.5,
            y0=51.4,
            yint=2
        )

        # Satellite GOMEX
        sat_region = satellite.sel(season=s).sel(lat=slice(35, 5), lon=slice(-100, -70))
        r_lonc, r_latc = corners(sat_region.lon, sat_region.lat)
        axs[3, i].pcolormesh(r_lonc, r_latc, sat_region, **common)
        axs[3, i].set_title(f'({ascii_lowercase[i+12]}) {s} OC-CCI')
        axs[3, i].add_patch(patches.Rectangle((-98.9, 30.7), 18, 3.4, alpha=0.4, facecolor='white', edgecolor='k', lw=1))
        sub = (mom_grid.geolon >= -99) & (mom_grid.geolon <= -79) & (mom_grid.geolat >= 18) & (mom_grid.geolat <= 34.1)
        annotate_skill(
            log_model.sel(season=s).where(sub), 
            sat_rg.sel(season=s).where(sub), 
            axs[3, i], dim=['yh', 'xh'], 
            weights=mom_grid.areacello.where(sub).fillna(0), 
            fontsize=8,
            x0=-98.5,
            y0=32.5,
            yint=1.5,
            xint=8,
            cols=2
        )

    nrow, ncol = axs.shape
    for i, ax in enumerate(axs.flat):
        yl = 0
        xl = 1
        if (i + 1) % ncol  == 0:
            yl = 1
        add_ticks(ax, xticks=np.arange(-100, -31, 5), yticks=np.arange(0, 61, 5), xlabelinterval=xl, ylabelinterval=yl, fontsize=7)
        
    for ax in axs.flat[0:8]:
        ax.set_extent([-80, -53, 33, 53])
        ax.set_facecolor('#bbbbbb')

    for ax in axs.flat[8:]:
        ax.set_extent([-99, -79, 18, 34.1])
        ax.set_facecolor('#bbbbbb')

    f.subplots_adjust(bottom=0.23, wspace=0.25, hspace=.35)
    cbax = f.add_axes([0.3, 0.18, 0.4, 0.01])
    cbar = f.colorbar(p, cax=cbax, orientation='horizontal', extend='max')
    cbar.ax.set_xlabel('Surface chl (mg / m$^3$)')
    cbar.set_ticks([0.25, 0.5, 1, 2, 4, 8])
    cbar.set_ticklabels([0.25, 0.5, 1, 2, 4, 8])
    save_figure('regional_chl', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    parser.add_argument('-d', '--dev', help='Use any available model data', action='store_true')
    args = parser.parse_args()
    plot_chl(args.pp_root, args.label, args.dev)
