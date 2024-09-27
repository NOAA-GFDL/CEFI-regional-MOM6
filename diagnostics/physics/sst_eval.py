"""
Compare model SST with 1993--2019 data from OISST and GLORYS.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python sst_eval.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c config.yaml
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import logging

from plot_common import annotate_skill, autoextend_colorbar, get_map_norm, open_var, load_config, process_oisst, process_glorys

# Configure logging for sst_eval
logger = logging.getLogger(__name__)
logging.basicConfig(filename="sst_eval.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_sst_eval(pp_root, config):
    
    model = open_var(pp_root, config['domain'], 'tos')
    model_grid = xarray.open_dataset( config['model_grid'] )
    target_grid = model_grid[config['rename_map'].keys()].rename(config['rename_map'])
    model_ave = model.mean('time').load()
    logger.info("MODEL_GRID: %s",model_grid)
    logger.info("MODEL_AVE: %s",model_ave)
    logger.info("Successfully opened model grid and took mean over time")

    # Verify that xh/yh are set as coordinates, then make sure model coordinates match grid data
    model_grid = model_grid.assign_coords( {'xh':model_grid.xh, 'yh':model_grid.yh } )
    model_ave = xarray.align(model_grid, model_ave,join='override')[1]

    glorys_rg, glorys_ave, glorys_lonc, glorys_latc = process_glorys(config, target_grid, 'thetao')
    delta_glorys = model_ave - glorys_rg
    logger.info("GLORYS_RG: %s",glorys_rg)
    logger.info("DELTA_GLORYS: %s",delta_glorys)

    mom_rg, oisst_ave, oisst_lonc, oisst_latc = process_oisst(config, target_grid, model_ave)
    delta_oisst = mom_rg - oisst_ave
    logger.info("OISST_AVE: %s",oisst_ave)
    logger.info("DELTA_OISST: %s",delta_oisst)

    fig = plt.figure(figsize=(config['fig_width'], config['fig_height']))

    # Set projection of each grid in the plot
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    grid = AxesGrid(fig, 111,
        axes_class=(GeoAxes, dict( projection = p )),
        nrows_ncols=(2, 3),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode='keep'
    )
    logger.info("Successfully created grid")

    # Discrete levels and colorbar for SST plots
    levels = np.arange(config['levels_min'], config['levels_max'], config['levels_step'])
    try:
        import cmcrameri.cm as cmc
    except ModuleNotFoundError:
        cmap = 'turbo'
    else:
        cmap = 'cmc.roma_r'
    cmap, norm = get_map_norm(cmap, levels=levels)

    # Discrete levels and colorbar for difference plots
    bias_levels = np.arange(config['bias_min'], config['bias_max'], config['bias_step'])
    bias_cmap, bias_norm = get_map_norm('coolwarm', levels=bias_levels)
    bias_common = dict(cmap=bias_cmap, norm=bias_norm)

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    # Model 
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ave, cmap=cmap, norm=norm, transform=proj)
    grid[0].set_title('(a) Model')
    cbar1 = grid.cbar_axes[0].colorbar(p0)
    cbar1.ax.set_xlabel('Mean SST (°C)')
    logger.info("Successfully plotted model data")

    # OISST
    grid[1].pcolormesh(oisst_lonc, oisst_latc, oisst_ave, cmap=cmap, norm=norm, transform=proj)
    grid[1].set_title('(b) OISST')
    logger.info("Successfully plotted oisst")

    # Model - OISST
    grid[2].pcolormesh(oisst_lonc, oisst_latc, delta_oisst, transform=proj,**bias_common)
    grid[2].set_title('(c) Model - OISST')
    annotate_skill(mom_rg, oisst_ave, grid[2], dim=['lat', 'lon'], x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])
    logger.info("Successfully plotted difference between model and oisst")

    # GLORYS
    p1 = grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_ave, cmap=cmap, norm=norm, transform=proj)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('Mean SST (°C)')
    logger.info("Successfully plotted glorys")

    # Model - GLORYS
    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_glorys, transform=proj, **bias_common)
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SST difference (°C)')
    cbar2.ax.set_xticks([-2, -1, 0, 1, 2])
    grid[5].set_title('(e) Model - GLORYS12')
    annotate_skill(model_ave, glorys_rg, grid[5], weights=model_grid.areacello, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])
    logger.info("Successfully plotted difference between glorys and model")

    for ax in grid:
        ax.set_extent([ config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max'] ], crs=proj )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for s in ax.spines.values():
            s.set_visible(False)
    logger.info("Successfully set extent of each axis")

    plt.savefig(config['figures_dir']+'sst_eval.png', dpi=300, bbox_inches='tight')
    logger.info("Successfully saved figure")


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', type=str, help='Path to postprocessed data (up to but not including /pp/)', required=True)
    parser.add_argument('-c','--config', type=str, help='Path to config.yaml file containing relevant paths for diagnostic scripts', required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    plot_sst_eval(args.pp_root, config)
