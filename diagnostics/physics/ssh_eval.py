"""
Compare model SSH with 1993--2019 data from GLORYS.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python ssh_eval.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c config.yaml
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import xarray
import xesmf
import numpy as np
import logging

from plot_common import autoextend_colorbar, corners, get_map_norm, open_var, add_ticks, annotate_skill, save_figure, load_config

# Configure logging for ssh_eval
logger = logging.getLogger(__name__)
logging.basicConfig(filename="ssh_eval.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_ssh_eval(pp_root, config, label):
    # Ideally would use SSH, but some diag_tables only saved zos
    try:
        model_ssh = open_var(pp_root, 'ocean_monthly', 'ssh')
    except:
        print('Using zos')
        model_ssh = open_var(pp_root, 'ocean_monthly', 'zos')
        
    model_grid = xarray.open_dataset( config['model_grid'] )
    model_ssh_ave = model_ssh.mean('time')
    logger.info("MODEL_GRID: %s",model_grid)
    logger.info("MODEL_SSH_AVE: %s",model_ssh_ave)
    logger.info("Successfully opened model grid and took mean over time")

    # Verify that xh/yh are set as coordinates, then make sure model coordinates match grid data
    model_grid = model_grid.assign_coords( {'xh':model_grid.xh, 'yh':model_grid.yh } )
    model_ssh_ave = xarray.align(model_grid, model_ssh_ave,join='override')[1]

    glorys_zos = xarray.open_mfdataset( config['glorys_zos'] ).zos
    glorys_zos = glorys_zos.rename({'latitude': 'lat', 'longitude': 'lon'})
    glorys_zos_ave = glorys_zos.mean('time').load()
    glorys_lonc, glorys_latc = corners(glorys_zos.lon, glorys_zos.lat)
    logger.info("GLORYS_ZOS_AVE: %s",glorys_zos_ave)

    # Set projection of each grid in the plot
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    # Plot of time-mean SSH.
    fig = plt.figure(figsize=(6, 8))
    grid = AxesGrid(fig, 111,
        nrows_ncols=(2, 1),
        axes_class = ( GeoAxes, dict( projection = p ) ),
        axes_pad=0.55,
        cbar_location='right',
        cbar_mode='edge',
        cbar_pad=0.5,
        cbar_size='5%',
        label_mode='keep'
    )
    logger.info("Successfully created grid")

    levels = np.arange( config['ssh_levels_min'], config['ssh_levels_max'], config['ssh_levels_step'])
    try:
        import colorcet
    except ModuleNotFoundError:
        cm = 'rainbow'
    else:
        cm = 'cet_CET_L8'
    cmap, norm = get_map_norm(cm, levels=levels)

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    target_grid = model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'})
    glorys_to_mom = xesmf.Regridder(glorys_zos_ave, target_grid, method='bilinear', unmapped_to_nan=True)
    glorys_rg = glorys_to_mom(glorys_zos_ave)

    # TODO: Find more robust solution for model_grids using [-180,180] coordinates
    mod_mask = ( (model_grid.geolon >= (config['lon']['west'] - 360.0))
                & (model_grid.geolon <= (config['lon']['east'] - 360.0))
                & (model_grid.geolat >= config['lat']['south'])
                & (model_grid.geolat <= config['lat']['north'])
               )

    # MODEL
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ssh_ave, cmap=cmap, norm=norm, transform = proj )
    cbar = autoextend_colorbar(grid.cbar_axes[0], p0)
    cbar.ax.set_title('SSH (m)', fontsize=10)
    grid[0].set_title('(a) Model mean SSH')
    logger.info("Successfully plotted model data")

    # GLORYS
    p1 = grid[1].pcolormesh(glorys_lonc, glorys_latc, glorys_zos_ave, cmap=cmap, norm=norm, transform = proj )
    cbar = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar.ax.set_title('SSH (m)', fontsize=10)
    grid[1].set_title('(b) GLORYS12 mean SSH')
    annotate_skill(
        model_ssh_ave.where(mod_mask),
        glorys_rg.where(mod_mask),
        grid[1],
        weights=model_grid.areacello.where(mod_mask).fillna(0),
        fontsize=8,
        x0=config['text_x'],
        y0=config['text_y'],
        xint=config['text_xint'],
        plot_lat=config['plot_lat']
    )
    logger.info("Successfully plotted glorys")

    for ax in grid:
            # The set_xticks function called by add_ticks does not currently support non-rectangular projections.
            # Until support is added, simply skip function if non-rectangular projection is used. Assume
            # NorthPolarStereo will be the only non-rectangular projection inputted
            if config['projection_grid'] != 'NorthPolarStereo':
                add_ticks(ax, xlabelinterval=2, ylabelinterval=2,
                          xticks=np.arange( config['lon']['west'], config['lon']['east'], 5 ),
                          yticks=np.arange( config['lat']['south'], config['lat']['north'], 5 ),
                          projection = proj
                         )
            else:
                logger.warning("WARNING: Cannot set tick marks in non-rectangular projection. Will not call add_ticks")

            ax.set_extent([ config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max'] ], crs=proj )
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_facecolor('#bbbbbb')
            for s in ax.spines.values():
                s.set_visible(False)

    save_figure('mean_ssh_eval', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-c','--config', help='Path to config.yaml file', required = True)
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    config = load_config( args.config )
    plot_ssh_eval(args.pp_root, config, args.label)
