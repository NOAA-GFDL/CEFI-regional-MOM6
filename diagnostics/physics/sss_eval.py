"""
Compare model SSS with 1993--2019 data from regional climatologies and GLORYS.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python sss_eval.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c config.yaml
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import os
import xarray
import xesmf
import logging

from plot_common import annotate_skill, autoextend_colorbar, get_map_norm, open_var, load_config, process_glorys, combine_regional_climatologies, center_to_outer

# Configure logging for sst_eval
logger = logging.getLogger(__name__)
logging.basicConfig(filename="sss_eval.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_sss_eval(pp_root,config):
    model = open_var(pp_root, config['domain'], 'sos')
    model_grid = xarray.open_dataset( config['model_grid'] )
    target_grid = model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'})
    model_ave = model.mean('time').load()

    # Verify that xh/yh are set as coordinates, then make sure model coordinates match grid data
    model_grid = model_grid.assign_coords( {'xh':model_grid.xh, 'yh':model_grid.yh } )
    model_ave = xarray.align(model_grid, model_ave,join='override')[1]

    # Open regional climatology datasets and merge together.
    # Convert to a common grid to merge the datasets together.
    # concat each dataset onto a new dimension,
    # then average over the dimension.
    # with no overlap, only one region has data at any point, 
    # so mean ignores the nans from other regions and selects the available data.
    regional_grid = {
        'lat': np.arange( np.floor( config['lat']['south'] * 10) / 10 - 0.05, np.ceil( config['lat']['north'] * 10 ) / 10 + 0.1 , 0.1),
        'lon': np.arange( np.floor( config['lon']['west'] * 10) / 10 - 0.05,  np.ceil( config['lon']['east'] * 10 ) / 10 + 0.1 , 0.1)
        }
    # For plotting later
    combined = combine_regional_climatologies( config, regional_grid)

    # Now interpolate to the model grid to compare.
    regional_to_mod = xesmf.Regridder({'lat': combined.lat, 'lon': combined.lon}, model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}), method='bilinear', unmapped_to_nan = True)
    regional_rg = regional_to_mod(combined)
    delta_regional = model_ave - regional_rg

    glorys_rg, glorys_ave, glorys_lonc, glorys_latc = process_glorys(config, target_grid, 'so')
    delta_glorys = model_ave - glorys_rg

    # Set projection of each grid in the plot
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    fig = plt.figure(figsize=(11, 14))
    grid = AxesGrid(fig, 111,
        axes_class=(GeoAxes, dict(projection= p )),
        nrows_ncols=(2, 3),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )

    # Discrete levels for SSS plots
    levels = np.arange(25, 39, 1)
    # Discrete levels for difference plots
    bias_levels = np.arange( config['bias_min'],  config['bias_max'],  config['bias_step'])

    try:
        import colorcet
    except ModuleNotFoundError:
        cmap, norm = get_map_norm('rainbow', levels=levels)
        bias_cmap, bias_norm = get_map_norm('coolwarm', levels=bias_levels)
    else:
        cmap, norm = get_map_norm('cet_CET_L20', levels=levels)
        bias_cmap, bias_norm = get_map_norm('cet_CET_CBD1', levels=bias_levels)

    common = dict(cmap=cmap, norm=norm)
    bias_common = dict(cmap=bias_cmap, norm=bias_norm)

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    # Model 
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ave, transform=proj, **common)
    grid[0].set_title('(a) Model')
    cbar0 = autoextend_colorbar(grid.cbar_axes[0], p0)
    cbar0.ax.set_xlabel('Mean SSS')

    # Regional climatologies
    grid[1].pcolormesh(center_to_outer(regional_grid['lon']), center_to_outer(regional_grid['lat']), combined, transform=proj, **common)
    grid[1].set_title('(b) Regional climatologies')

    # Model - regional
    grid[2].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_regional, transform=proj, **bias_common)
    grid[2].set_title('(c) Model - climatologies')
    # rechunk data
    model_ave = model_ave.chunk(dict(yh=-1, xh=-1))
    regional_rg = regional_rg.chunk(dict(yh=-1, xh=-1))
    annotate_skill(model_ave, regional_rg, grid[2], weights=model_grid.areacello, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])

    # GLORYS
    p1 = grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_ave, transform=proj, **common)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('Mean SSS')

    # Model - GLORYS
    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_glorys, transform=proj, **bias_common)
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SSS difference')
    cbar2.ax.set_xticks([-2, -1, 0, 1, 2])
    grid[5].set_title('(e) Model - GLORYS12')
    annotate_skill(model_ave, glorys_rg, grid[5], weights=model_grid.areacello, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])

    for ax in grid:
        ax.set_extent([ config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max'] ], crs=proj )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for s in ax.spines.values():
            s.set_visible(False)
        
    plt.savefig('figures/sss_eval.png', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-c','--config', help='Path to config.yaml file')
    args = parser.parse_args()
    config = load_config(args.config)
    plot_sss_eval(args.pp_root, config)
