"""
Compare the model 2005-019 sea surface temperature trends from OISST and GLORYS. 
How to use:
python sst_trends.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod -c config.yaml
"""
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import colorcet
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import logging

from plot_common import( autoextend_colorbar, corners, get_map_norm,
                         annotate_skill, open_var, save_figure, load_config,
                         process_glorys, process_oisst)

# Configure logging for sst_eval
logger = logging.getLogger(__name__)
logging.basicConfig(filename="sst_trends.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def get_3d_trends(y):
    x = np.array( y['time.year'] )
    y2 = np.array(y).reshape((len(x), -1))
    coefs = np.polyfit(x, y2, 1)
    trends = coefs[0, :].reshape(y.shape[1:]) * 10 # -> C / decade

    return trends


def plot_sst_trends(pp_root, label, config):
    model = (
        open_var(pp_root, 'ocean_monthly', 'tos')
        .sel(time=slice(config['start_year'], config['end_year']))
        .resample(time='1AS')
        .mean('time')
        .load()
    )
    logger.info("MODEL: %s",model)
    model_grid = xarray.open_dataset( config['model_grid'])
    logger.info("MODEL_GRID: %s",model_grid)

    # Verify that xh/yh are set as coordinates, then make sure model coordinates match grid data
    model_grid = model_grid.assign_coords( {'xh':model_grid.xh, 'yh':model_grid.yh } )
    model = xarray.align(model_grid, model, join='override', exclude='time')[1]
    logger.info("Successfully modified coordinates of model grid, and aligned model coordinates to grid coordinates")

    model_trend = get_3d_trends(model)
    # Convert to Data Array, since xskillscore expects dataarrays to calculate skill metrics
    model_trend = xarray.DataArray(model_trend, dims=['yh', 'xh'], coords={'yh': model.yh, 'xh': model.xh})
    logger.info("MODEL_TREND: %s", model_trend)

    target_grid = model_grid[ config['rename_map'].keys() ].rename( config['rename_map'] )

    # Process OISST and get trend
    mom_rg, oisst, oisst_lonc, oisst_latc = process_oisst(config, target_grid, model_trend, start =  int(config['start_year']),
                                                                end = int(config['end_year'])+1, resamp_freq = '1AS')
    logger.info("OISST: %s", oisst )
    oisst_trend = get_3d_trends(oisst)
    oisst_trend = xarray.DataArray(oisst_trend, dims=['lat','lon'], coords={'lat':oisst.lat,'lon':oisst.lon} )
    logger.info("OISST_TREND: %s",oisst_trend)

    oisst_delta = mom_rg - oisst_trend
    logger.info("MOM_RG: %s",mom_rg)
    logger.info("OISST_DELTA: %s",oisst_delta)

    # Process Glorys and get trend
    # NOTE: Glorys_ave is glorys_trends because we call get_3d_trends on it.
    glorys_rg, glorys_trend, glorys_lonc, glorys_latc = process_glorys(config, target_grid, 'thetao',
                                                                      sel_time = slice(config['start_year'], config['end_year']),
                                                                      resamp_freq = '1AS', preprocess_regrid = get_3d_trends)
    logger.info("GLORYS_TREND: %s",glorys_trend)

    glorys_rg = xarray.DataArray(glorys_rg, dims=['yh', 'xh'], coords={'yh': model.yh, 'xh': model.xh})
    glorys_delta = model_trend - glorys_rg
    logger.info("GLORYS_RG: %s",glorys_rg)
    logger.info("GLORYS_DELTA: %s",glorys_delta)

    # Set projection of each grid in the plot
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    fig = plt.figure(figsize=(10, 14))
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(2, 3),
        axes_class = (GeoAxes, dict(projection=p)),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode='keep'
    )
    logger.info("Successfully created grid")

    cmap, norm = get_map_norm('cet_CET_D1', np.arange(config['bias_min'], config['bias_max'], config['bias_step']), no_offset=True)
    common = dict(cmap=cmap, norm=norm)

    bias_cmap, bias_norm = get_map_norm('RdBu_r', np.arange(config['bias_min_trends'], config['bias_max_trends'], config['bias_step']), no_offset=True)
    bias_common = dict(cmap=bias_cmap, norm=bias_norm)

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    # MODEL
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_trend, transform = proj, **common)
    grid[0].set_title('(a) Model')
    cbar0 = autoextend_colorbar(grid.cbar_axes[0], p0)
    cbar0.ax.set_xlabel('SST trend (°C / decade)')
    cbar0.set_ticks( config['ticks'] )
    cbar0.set_ticklabels( config['ticks'] )
    logger.info("Successfully plotted model data")

    # OISST
    p1 = grid[1].pcolormesh(oisst_lonc, oisst_latc, oisst_trend, transform = proj, **common)
    grid[1].set_title('(b) OISST')
    logger.info("Successfully plotted oisst")

    # MODEL - OISST
    grid[2].pcolormesh(oisst_lonc, oisst_latc, oisst_delta, transform = proj, **bias_common)
    grid[2].set_title('(c) Model - OISST')
    # NOTE: Oisst dims are [lat,lon], so dim argument is needed. Must use mom_rg though, since oisst also contains
    # an extra time dimension that changes output of xskillscore functions and leads to error when annotating plot
    annotate_skill(mom_rg, oisst_trend, grid[2], dim= list(mom_rg.dims), x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])
    logger.info("Successfully plotted difference between model and oisst")

    # GLORYS
    grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_trend, transform = proj, **common)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('SST trend (°C / decade)')
    cbar1.set_ticks( config['ticks'] )
    cbar1.set_ticklabels( config['ticks'] )
    logger.info("Successfully plotted glorys")

    # MODEL - GLORYS
    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, glorys_delta, transform = proj, **bias_common)
    grid[5].set_title('(e) Model - GLORYS12')
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SST trend difference (°C / decade)')
    annotate_skill(model_trend, glorys_rg, grid[5], weights=model_grid.areacello, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat'])
    logger.info("Successfully plotted difference between glorys and model")

    for i, ax in enumerate(grid):
        ax.set_extent([ config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max'] ], crs=proj)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        if i != 3:
            ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)
    logger.info("Successfully set extent of each axis")

    save_figure('sst_trends', label=label)
    logger.info("Successfully saved figure")


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-c','--config', help='Path to yaml config file', required = True)
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    config = load_config(args.config)
    plot_sst_trends(args.pp_root, args.label, config)
