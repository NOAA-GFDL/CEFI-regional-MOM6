"""
Compare model surface chla with data from occci-v6.0.
How to use:
python chl_eval.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c config.yaml
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

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.getcwd())
sys.path.append(os.path.join(script_dir, 'physics'))
from plot_common import add_ticks, autoextend_colorbar, corners, annotate_skill, open_var, save_figure, load_config

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="chl_eval.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_chl(pp_root, label, config, dev):
    model_grid = xarray.open_dataset( config['model_grid'] )
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
    log_sat = np.log10(np.maximum(satellite,1e-14))
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

    # Plot full domain, including difference

    # Set projection of each grid in the plot
    # For now, we will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    common = dict(cmap=colorcet.cm.CET_L16, norm=colors.LogNorm(vmin=0.125, vmax=8) )
    delta_common = dict(cmap='BrBG', norm=colors.SymLogNorm(.1, linscale=.1, vmin=-4, vmax=4))
    ticks = config['chl_ticks']
    label_ticks = config['chl_ticks_labels']
    fig = plt.figure(figsize=(8, 10))
    nrows, ncols = 4, 3
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(nrows, ncols),
        axes_class = (GeoAxes, dict( projection = p)),
        axes_pad=0.33,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.3,
        cbar_size='10%',
        label_mode='keep'
    )
    logger.info("Successfully created grid")

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, we will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    common['transform'] = proj
    delta_common['transform'] = proj
    
    # Set args to annotate skill
    skill_args = dict( x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'] )

    logger.info("Plotting model, OC-CCI, and difference data for 4 seasons")
    for i, s in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
        left = i * ncols
        # Model
        pleft = grid[left].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_climo.sel(season=s), **common)
        grid[left].set_title(f'({ascii_lowercase[left]}) {s} Model')
        # OC-CCI
        pmid = satellite.sel(season=s).plot(ax=grid[left+1], add_colorbar=False, **common)
        grid[left+1].set_title(f'({ascii_lowercase[left+1]}) {s} OC-CCI')
        # Difference
        pdiff = grid[left+2].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta.sel(season=s), **delta_common)
        annotate_skill(log_model.sel(season=s), sat_rg.sel(season=s), grid[left+2], weights=model_grid.areacello, fontsize=8, **skill_args)
        grid[left+2].set_title(f'({ascii_lowercase[left+2]}) {s} Model - OC-CCI')

    logger.info("Finished creating color meshes, now modifying visuals")
    for ax in grid:
        ax.set_facecolor('#bbbbbb')
        ax.set_extent( [config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max']] , crs = proj)
        for s in ax.spines.values():
            s.set_visible(False)

    # chl value color bars
    cbarleft = grid.cbar_axes[0].colorbar(pleft)
    cbarmid = grid.cbar_axes[1].colorbar(pmid, extend='max')
    for cbar in [cbarleft, cbarmid]:
        cbar.ax.set_xlabel('Surface chl (mg / m$^3$)')
        cbar.set_ticks( config['chl_cbar_ticks'] )
        cbar.set_ticklabels( config['chl_cbar_ticks'] )

    # difference color bar
    cbar = autoextend_colorbar(grid.cbar_axes[2], pdiff)
    cbar.ax.set_xlabel('Difference. (mg m$^{-3}$)')
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([t if str(t) in label_ticks else '' for t in ticks])
    logger.info("Saving figure")
    save_figure('domain_chl', label=label)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-c', '--config', help='Path to config file', required = True)
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    parser.add_argument('-d', '--dev', help='Use any available model data', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    plot_chl(args.pp_root, args.label, config, args.dev)
