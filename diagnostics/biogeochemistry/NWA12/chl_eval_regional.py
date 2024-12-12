"""
Compare model surface chla with data from occci-v6.0 over a subset of the NWA domain
How to use:
python chl_eval_regional.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c ../config.yaml
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
import logging
from pathlib import Path
import sys

# Add physics/plot_common to path in order to access tools located there
diag_dir = Path.cwd().parent.parent
sys.path.append( str( diag_dir.joinpath('physics') ) )
from plot_common import add_ticks, autoextend_colorbar, corners, annotate_skill, open_var, save_figure, load_config

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="chl_eval_regional.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_chl_regional(pp_root, label, config, dev):
    model_grid = xarray.open_dataset( "../../data/geography/ocean_static.nc" )
    model = open_var(pp_root, 'ocean_cobalt_omip_sfc', 'chlos') * 1e6 # kg m-3 -> mg m-3
    if dev:
        print('Using any available model data')
        model = model.sel(time=slice('1993-12-01', None)).isel(time=slice(None, -1))
    else:
        model = model.sel(time=slice(config['chl_start'], config['chl_end']))
    model_climo = model.groupby('time.season').mean('time')

    # Verify that xh/yh are set as coordinates, then make sure model coordinates match grid data
    model_grid = model_grid.assign_coords( {'xh':model_grid.xh, 'yh':model_grid.yh } )
    model_climo = xarray.align(model_grid, model_climo,join='override')[1]

    logger.info("MODEL_GRID: %s",model_grid)
    logger.info("MODEL_CLIMO: %s",model_climo)
    logger.info("Successfully opened model grid and calculated climotology")
    
    # Load pre-computed climatology, also using 1997-09-01 to 2019-11-30
    satellite = xarray.open_dataset( config['chl_satellite'] ).chlor_a
    # Flip to right side up.
    # satellite = satellite.isel(lat=slice(None, None, -1))
    log_model = np.log10(np.maximum(model_climo, 1e-14))
    log_sat = np.log10(satellite)
    logger.info("SATELITE: %s",satellite)
    logger.info("Successfully opened model grid and calculated climotology")
    
    sat_lonc, sat_latc = corners(log_sat.lon, log_sat.lat)
    sat_grid = {'lon': log_sat.lon, 'lat': log_sat.lat, 'lon_b': sat_lonc, 'lat_b': sat_latc}
    target_grid = {'lon': model_grid.geolon, 'lat': model_grid.geolat, 'lon_b': model_grid.geolon_c, 'lat_b': model_grid.geolat_c}
    sat_to_model = xesmf.Regridder(sat_grid, target_grid,method='conservative_normed', unmapped_to_nan=True)
    sat_rg = sat_to_model(log_sat)
    delta = model_climo - np.power(10, sat_rg)
    logger.info("SAT_RG: %s",sat_rg)
    logger.info("DELTA: %s",sat_rg)
    logger.info("Successfully regridded satellite data")

    PC = ccrs.PlateCarree()
        
    # Regional zooms
    common = dict(cmap=colorcet.cm.CET_L16, norm=colors.LogNorm(vmin=0.125, vmax=8) )
    f, axs = plt.subplots(4, 4, subplot_kw = dict(projection = PC), figsize=(10, 10))
    logger.info("Finished creating color meshes, now modifying visuals")
    for i, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        # Model plots
        p = axs[0, i].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_climo.sel(season=s), **common)
        axs[2, i].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_climo.sel(season=s), **common)
        axs[0, i].set_title(f'({ascii_lowercase[i]}) {s} Model')
        axs[2, i].set_title(f'({ascii_lowercase[i+8]}) {s} Model')

        # Satellite NE US
        sat_region = satellite.sel(season=s).sel(lat=slice(60, 20), lon=slice(-90, -50))
        r_lonc, r_latc = corners(sat_region.lon, sat_region.lat)
        axs[1, i].pcolormesh(r_lonc, r_latc, sat_region, **common)
        axs[1, i].set_title(f'({ascii_lowercase[i+4]}) {s} OC-CCI')
        axs[1, i].add_patch(patches.Rectangle((-79.9, 45.1), 12.5, 8.2, alpha=0.4, facecolor='white', edgecolor='k', lw=1))
        sub = (model_grid.geolon >= -80) & (model_grid.geolon <= -53) & (model_grid.geolat >= 33) & (model_grid.geolat <= 53)
        # n\(xh=slice(-80, -53), yh=slice(33, 53))
        annotate_skill(
            log_model.sel(season=s).where(sub), 
            sat_rg.sel(season=s).where(sub), 
            axs[1, i], dim=['yh', 'xh'], 
            weights=model_grid.areacello.where(sub).fillna(0), 
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
        sub = (model_grid.geolon >= -99) & (model_grid.geolon <= -79) & (model_grid.geolat >= 18) & (model_grid.geolat <= 34.1)
        annotate_skill(
            log_model.sel(season=s).where(sub), 
            sat_rg.sel(season=s).where(sub), 
            axs[3, i], dim=['yh', 'xh'], 
            weights=model_grid.areacello.where(sub).fillna(0), 
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
    logger.info("Saving figure")
    save_figure('regional_chl', label=label, output_dir = "../figures")


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-c', '--config', help='Path to config file', required = True)
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    parser.add_argument('-d', '--dev', help='Use any available model data', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    plot_chl_regional(args.pp_root, args.label, config, args.dev)
