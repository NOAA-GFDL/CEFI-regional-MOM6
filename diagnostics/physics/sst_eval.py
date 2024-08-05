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
import xesmf

from plot_common import annotate_skill, autoextend_colorbar, corners, get_map_norm, open_var


def plot_sst_eval(pp_root, config):
    model = open_var(pp_root, config['domain'], 'tos')
    model_grid = xarray.open_dataset( config['model_grid'] )
    target_grid = model_grid[config['rename_vars']].rename(config['rename_map'])
    model_ave = model.mean('time').load()

    glorys = xarray.open_dataset( config['glorys'] ).squeeze()['thetao'] #.rename({'longitude': 'lon', 'latitude': 'lat'})
    try:
        glorys_lonc, glorys_latc = corners(glorys.lon, glorys.lat)
    except:
        glorys_lonc, glorys_latc = corners(glorys.longitude, glorys.latitude)
    glorys_ave = glorys.mean('time').load()
    glorys_to_mom = xesmf.Regridder(glorys_ave, target_grid, method='bilinear', unmapped_to_nan=True)
    glorys_rg = glorys_to_mom(glorys_ave)
    delta_glorys = model_ave - glorys_rg
    oisst = (
        xarray.open_mfdataset([config['oisst']+f'sst.month.mean.{y}.nc' for y in range(1993, 2020)])
        .sst
        .sel(lat=slice(config['lat']['south'], config['lat']['north']), lon=slice(config['lon']['west'] ,config['lon']['east']))
    )
    oisst_lonc, oisst_latc = corners(oisst.lon, oisst.lat)
    oisst_lonc -= 360
    mom_to_oisst = xesmf.Regridder(
        target_grid, 
        {'lat': oisst.lat, 'lon': oisst.lon, 'lat_b': oisst_latc, 'lon_b': oisst_lonc}, 
        method='conservative_normed', 
        unmapped_to_nan=True
    )
    oisst_ave = oisst.mean('time').load()
    mom_rg = mom_to_oisst(model_ave)
    delta_oisst = mom_rg - oisst_ave
    fig = plt.figure(figsize=(11, 14))
    grid = AxesGrid(fig, 111,
        axes_class=(GeoAxes, dict(projection=ccrs.PlateCarree())),
        nrows_ncols=(2, 3),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )

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

    # Model 
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ave, cmap=cmap, norm=norm)
    grid[0].set_title('(a) Model')
    cbar1 = grid.cbar_axes[0].colorbar(p0)
    cbar1.ax.set_xlabel('Mean SST (°C)')

    # OISST
    grid[1].pcolormesh(oisst_lonc, oisst_latc, oisst_ave, cmap=cmap, norm=norm)
    grid[1].set_title('(b) OISST')

    # Model - OISST
    grid[2].pcolormesh(oisst_lonc, oisst_latc, delta_oisst, **bias_common)
    grid[2].set_title('(c) Model - OISST')
    annotate_skill(mom_rg, oisst_ave, grid[2], dim=['lat', 'lon'])

    # GLORYS
    p1 = grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_ave, cmap=cmap, norm=norm)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('Mean SST (°C)')

    # Model - GLORYS
    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_glorys, **bias_common)
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SST difference (°C)')
    cbar2.ax.set_xticks([-2, -1, 0, 1, 2])
    grid[5].set_title('(e) Model - GLORYS12')
    annotate_skill(model_ave, glorys_rg, grid[5], weights=model_grid.areacello)

    for ax in grid:
        ax.set_xlim(config['x']['min'], config['x']['max'])
        ax.set_ylim(config['y']['min'], config['y']['max'])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for s in ax.spines.values():
            s.set_visible(False)
        
    plt.savefig(config['figures_dir']+'sst_eval.png', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    from argparse import ArgumentParser
    import yaml
    parser = ArgumentParser()
    parser.add_argument('-p','--pp_root', type=str, help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-c','--config', type=str, help='Path to config.yaml file containing relevant paths for diagnostic scripts')
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    plot_sst_eval(args.pp_root, config)
