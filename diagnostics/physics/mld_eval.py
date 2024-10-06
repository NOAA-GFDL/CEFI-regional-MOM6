"""
Compare model MLD with climatologies from Holte et al. 2017
and de Boyer 2022.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python mld_eval.py -p /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod/ -c config.yaml
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf
import logging

from plot_common import annotate_skill, autoextend_colorbar, get_map_norm, open_var, load_config

# Configure logging for mld_eval
logger = logging.getLogger(__name__)
logging.basicConfig(filename="mld_eval.log", format='%(asctime)s %(levelname)s:%(name)s: %(message)s',level=logging.INFO)

def plot_mld_eval(pp_root, config):
    model = open_var(pp_root, config['domain'] , 'MLD_003')
    model_grid = xarray.open_dataset( config['model_grid'] )
    mom_mld_climo = model.groupby('time.month').mean('time').load()
    mom_mld_winter = mom_mld_climo.sel(month=slice(1, 3)).mean('month')
    logger.info("MODEL_GRID: %s",model_grid)
    logger.info("MODEL_MLD_CLIMO: %s",mom_mld_climo)
    logger.info("MODEL_MLD_WINTER: %s",mom_mld_winter)
    logger.info("Successfully opened model grid, took mean over all months and over winter months")

    argo = (
        xarray.open_dataset('/net2/acr/mld/Argo_mixedlayers_monthlyclim_03172021.nc')
        .swap_dims({'iLAT': 'lat', 'iLON': 'lon', 'iMONTH': 'month'})
        .mld_dt_mean
    )
    argo_grid = dict(lat=argo.lat, lon=argo.lon, lat_b=np.arange(-90, 90.1, 1), lon_b=np.arange(-180, 180.1, 1))
    argo_mld_winter = argo.sel(month=slice(1, 3)).mean('month')
    logger.info("ARGO_MLD_WINTER: %s",argo_mld_winter)

    mom_to_argo = xesmf.Regridder(
        model_grid[ config['rename_map'].keys() ].rename( config['rename_map'] ),
        argo_grid,
        method='conservative_normed',
        unmapped_to_nan=True,
        reuse_weights=False
    )
    mom_rg = mom_to_argo(mom_mld_winter)
    delta = mom_rg - argo_mld_winter
    logger.info("DELTA: %s",delta)

    deboyer = xarray.open_dataset('/net2/acr/deBoyer2022/mld_dr003_ref10m.nc')
    deboyer['time'] = np.arange(len(deboyer['time']), dtype='float64') + 1
    deboyer = deboyer.rename({'time': 'month'})
    deboyer_mld_winter =  deboyer.mld_dr003.where(deboyer.mask==1).sel(month=slice(1, 3)).mean('month')

    # the two observed datasets have the same grid
    delta_deboyer = mom_rg - deboyer_mld_winter
    logger.info("DEBOYER_MLD_WINTER: %s",deboyer_mld_winter)
    logger.info("DELTA_DEBOYER: %s",delta_deboyer)

    # Set projection of each grid in the plot
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_grid'] == 'NorthPolarStereo':
        p = ccrs.NorthPolarStereo()
    else:
        p = ccrs.PlateCarree()

    fig = plt.figure(figsize=(8, 6))
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(2, 3),
        axes_class = (GeoAxes, dict(projection = p)),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )
    logger.info("Successfully created grid")

    levels = np.arange(0, 326, 25)
    bias_levels = np.arange(-50, 51, 10)

    try:
        import colorcet
    except ModuleNotFoundError:
        cmap, norm = get_map_norm('rainbow', levels)
        bias_cmap, bias_norm = get_map_norm('coolwarm', bias_levels)
    else:
        cmap, norm = get_map_norm('cet_CET_L20', levels)
        bias_cmap, bias_norm = get_map_norm('cet_CET_D9', bias_levels)

    # Set projection of input data files so that data is correctly tranformed when plotting
    # For now, sst_eval.py will only support a projection for the arctic and a projection for all other domains
    if config['projection_data'] == 'NorthPolarStereo':
        proj = ccrs.NorthPolarStereo()
    else:
        proj = ccrs.PlateCarree()

    # Model
    p = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, mom_mld_winter, cmap=cmap, norm=norm, transform=proj)
    grid[0].set_title('(a) Model')
    cbar = autoextend_colorbar(grid.cbar_axes[0], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))
    logger.info("Successfully plotted model data")

    # DeBoyer
    p = grid[1].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], deboyer_mld_winter, cmap=cmap, norm=norm, transform=proj)
    grid[1].set_title('(b) dBM 2022')
    cbar = autoextend_colorbar(grid.cbar_axes[1], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))
    logger.info("Successfully plotted DeBoyer data")

    # Model - DeBoyer
    p = grid[2].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], delta_deboyer, cmap=bias_cmap, norm=bias_norm, transform=proj)
    grid[2].set_title('(c) Model - dBM')
    cbar = autoextend_colorbar(grid.cbar_axes[2], p)
    cbar.ax.set_xlabel('Difference (m)')
    annotate_skill(mom_rg, deboyer_mld_winter, grid[2], dim=['lat', 'lon'], fontsize=8, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat']) # TODO: need to cosine weight
    logger.info("Successfully plotted Model - DeBoyer data")

    # Holte
    p = grid[4].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], argo_mld_winter, cmap=cmap, norm=norm, transform=proj)
    grid[4].set_title('(b) Holte et al. 2017')
    cbar = autoextend_colorbar(grid.cbar_axes[4], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))
    logger.info("Successfully plotted Holte data")

    # Model - Holte
    p = grid[5].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], delta, cmap=bias_cmap, norm=bias_norm, transform=proj)
    grid[5].set_title('(c) Model - Holte')
    cbar = autoextend_colorbar(grid.cbar_axes[5], p)
    cbar.ax.set_xlabel('Difference (m)')
    annotate_skill(mom_rg, argo_mld_winter, grid[5], dim=['lat', 'lon'], fontsize=8, x0=config['text_x'], y0=config['text_y'], xint=config['text_xint'], plot_lat=config['plot_lat']) # TODO: need to cosine weight
    logger.info("Successfully plotted Model - Holte data")

    for i, ax in enumerate(grid):
        ax.set_extent([ config['x']['min'], config['x']['max'], config['y']['min'], config['y']['max'] ], crs=proj)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        if i != 3:
            ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)
    logger.info("Successfully set extent of each axis")

    plt.savefig('figures/mld003_eval.png', dpi=300, bbox_inches='tight')
    logger.info("Successfully saved figure")


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', help='Path to postprocessed data (up to but not including /pp/)', required = True)
    parser.add_argument('-c','--config', help='Path to config file', required = True)
    args = parser.parse_args()
    config = load_config(args.config)
    plot_mld_eval(args.pp_root, config)
