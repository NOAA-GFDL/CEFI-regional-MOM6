"""
Compare Mean surface alkalinity, dissolved inorganic carbon, and aragonite saturation statee between the model and the
observation-derived climatology
How to use:
python oa_metrics.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
import cartopy.crs as ccrs
import cmcrameri.cm as cmc
import colorcet
import matplotlib.pyplot as plt
import numpy as np
import xarray
import xesmf

from mpl_toolkits.axes_grid1 import AxesGrid
from cartopy.mpl.geoaxes import GeoAxes

PC = ccrs.PlateCarree()

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../physics'))
from plot_common import autoextend_colorbar, get_map_norm, annotate_skill, open_var, save_figure

def plot_oa_metrics(pp_root, label, dev):
    mom_grid = xarray.open_dataset('../data/geography/ocean_static.nc')

    model = []
    if dev:
        print('Using any available model data')
        # co3_ion / co3_sol_arag
        model.append(open_var(pp_root, 'ocean_cobalt_omip_sfc', 'talkos') * 1e6 / 1035) # mol m-3 -> umol kg
        # model.append(open_var(pp_root, 'ocean_cobalt_tracers_month_z', 'omega_arag').isel(z_l=0))
        model.append(open_var(pp_root, 'ocean_cobalt_omip_sfc', 'dissicos') * 1e6 / 1035) # mol m-3 -> umol kg
        co3_ion = open_var(pp_root, 'ocean_cobalt_sfc', 'sfc_co3_ion')
        co3_sol_arag = open_var(pp_root, 'ocean_cobalt_sfc', 'sfc_co3_sol_arag')
        omega_arag = co3_ion / co3_sol_arag
        omega_arag.name = 'omega_arag'
        model.append(omega_arag)
    else:
        model.append(open_var(pp_root, 'ocean_cobalt_omip_sfc', 'talkos').sel(time=slice('2004', '2018')) * 1e6 / 1035) # mol m-3 -> umol kg
        # model.append(open_var(pp_root, 'ocean_cobalt_tracers_month_z', 'omega_arag').sel(time=slice('2004', '2018')).isel(z_l=0))
        model.append(open_var(pp_root, 'ocean_cobalt_omip_sfc', 'dissicos').sel(time=slice('2004', '2018')) * 1e6 / 1035) # mol m-3 -> umol kg
        co3_ion = open_var(pp_root, 'ocean_cobalt_sfc', 'sfc_co3_ion').sel(time=slice('2004', '2018'))
        co3_sol_arag = open_var(pp_root, 'ocean_cobalt_sfc', 'sfc_co3_sol_arag').sel(time=slice('2004', '2018'))
        omega_arag = co3_ion / co3_sol_arag
        omega_arag.name = 'omega_arag'
        model.append(omega_arag)

    model = xarray.Dataset({m.name: m for m in model}).load()
    model_mean = model.mean('time')

    obs = xarray.open_mfdataset('/net2/acr/oa_climo/CODAP_NA_climatologies_1x1/*.nc', decode_times=False).isel(depth=0, time=0)
    obs_lonc = np.arange(obs.lon[0]-0.5, obs.lon[-1]+0.51, 1.0)
    obs_latc = np.arange(obs.lat[0]-0.5, obs.lat[-1]+0.51, 1.0)
    weight = xarray.ones_like(obs['TAlk_an']) * np.cos(np.deg2rad(obs.lat))

    model_to_obs = xesmf.Regridder(
        {'lon': mom_grid.geolon, 'lat': mom_grid.geolat, 'lon_b': mom_grid.geolon_c, 'lat_b': mom_grid.geolat_c},
        {'lon': obs.lon, 'lat': obs.lat, 'lon_b': obs_lonc, 'lat_b': obs_latc},
        method='conservative_normed',
        unmapped_to_nan=True
    )
    model_rg = model_to_obs(model_mean).load()

    fig = plt.figure(figsize=(10, 20))
    grid = AxesGrid(fig, 111,  # similar to subplot(121)
        nrows_ncols=(3, 3),
        axes_class=(GeoAxes, dict(projection=PC)),
        axes_pad=(0.25, 0.7),
        cbar_location='bottom',
        cbar_mode='each',
        cbar_pad=0.01,
        cbar_size='5%',
        label_mode=''
    )

    levels = np.arange(1800, 2501, 50)
    cmap, norm = get_map_norm('cmc.batlowK', levels, no_offset=True)
    common = dict(cmap=cmap, norm=norm)
    delta_cmap, delta_norm = get_map_norm('cet_CET_D9', np.arange(-100, 101, 20), no_offset=True)
    delta_common = dict(cmap=delta_cmap, norm=delta_norm)

    p = grid[0].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_mean['talkos'], **common)
    cb = autoextend_colorbar(grid.cbar_axes[0], p)
    cb.ax.set_xticks(np.arange(1800, 2501, 200))
    cb.ax.tick_params(labelsize=9)
    grid[0].set_title('(a) Model surface ALK ($\mu$mol kg$^{-1}$)', fontsize=10)

    p = grid[1].pcolormesh(obs_lonc, obs_latc, obs['TAlk_an'], **common)
    cb = autoextend_colorbar(grid.cbar_axes[1], p)
    cb.ax.set_xticks(np.arange(1800, 2501, 200))
    cb.ax.tick_params(labelsize=9)
    grid[1].set_title('(b) Observed surface ALK ($\mu$mol kg$^{-1}$)', fontsize=10)

    p = grid[2].pcolormesh(obs_lonc, obs_latc, model_rg['talkos'] - obs['TAlk_an'], **delta_common)
    cb = autoextend_colorbar(grid.cbar_axes[2], p)
    cb.ax.tick_params(labelsize=9)
    grid[2].set_title('(c) Model - observed ($\mu$mol kg$^{-1}$)', fontsize=10)
    annotate_skill(model_rg['talkos'], obs['TAlk_an'], grid[2], fontsize=8, dim=['lat', 'lon'], weights=weight)

    levels = np.arange(1800, 2151, 25)
    cmap, norm = get_map_norm('cmc.oslo', levels, no_offset=True)
    common = dict(cmap=cmap, norm=norm)
    delta_cmap, delta_norm = get_map_norm('cet_CET_D9', np.arange(-100, 101, 20), no_offset=True)
    delta_common = dict(cmap=delta_cmap, norm=delta_norm)

    p = grid[3].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_mean['dissicos'], **common)
    cb = autoextend_colorbar(grid.cbar_axes[3], p)
    cb.ax.set_xticks(np.arange(1800, 2200, 100))
    cb.ax.tick_params(labelsize=9)
    grid[3].set_title('(d) Model surface DIC ($\mu$mol kg$^{-1}$)', fontsize=10)

    p = grid[4].pcolormesh(obs_lonc, obs_latc, obs['DIC_an'], **common)
    cb = autoextend_colorbar(grid.cbar_axes[4], p)
    cb.ax.set_xticks(np.arange(1800, 2200, 100))
    cb.ax.tick_params(labelsize=9)
    grid[4].set_title('(e) Observed surface DIC ($\mu$mol kg$^{-1}$)', fontsize=10)

    p = grid[5].pcolormesh(obs_lonc, obs_latc, model_rg['dissicos'] - obs['DIC_an'], **delta_common)
    cb = autoextend_colorbar(grid.cbar_axes[5], p)
    cb.ax.tick_params(labelsize=9)
    grid[5].set_title('(f) Model - observed ($\mu$mol kg$^{-1}$)', fontsize=10)
    annotate_skill(model_rg['dissicos'], obs['DIC_an'], grid[5], fontsize=8, dim=['lat', 'lon'], weights=weight)

    levels = np.arange(0.75, 4.01, .25)
    cmap, norm = get_map_norm('cmc.acton', levels, no_offset=True)
    common = dict(cmap=cmap, norm=norm)
    delta_cmap, delta_norm = get_map_norm('cet_CET_D9', np.arange(-0.5, 0.51, .1), no_offset=True)
    delta_common = dict(cmap=delta_cmap, norm=delta_norm)

    p = grid[6].pcolormesh(mom_grid.geolon_c, mom_grid.geolat_c, model_mean['omega_arag'], **common)
    # grid[6].contour(mom_grid.geolon, mom_grid.geolat, model_mean['omega_arag'], levels=[1.5], colors='k')
    cb = autoextend_colorbar(grid.cbar_axes[6], p)
    cb.ax.set_xticks(np.arange(1, 4.1, .5))
    cb.ax.tick_params(labelsize=9)
    grid[6].set_title('(g) Model surface $\Omega_{ar}$', fontsize=10)

    p = grid[7].pcolormesh(obs_lonc, obs_latc, obs['OmegaA_an'], **common)
    # grid[7].contour(obs.lon, obs.lat, obs['OmegaA_an'], levels=[1.5], colors='k')
    cb = autoextend_colorbar(grid.cbar_axes[7], p)
    cb.ax.set_xticks(np.arange(1, 4.1, .5))
    cb.ax.tick_params(labelsize=9)
    grid[7].set_title('(h) Observed surface $\Omega_{ar}$', fontsize=10)

    p = grid[8].pcolormesh(obs_lonc, obs_latc, model_rg['omega_arag'] - obs['OmegaA_an'], **delta_common)
    cb = autoextend_colorbar(grid.cbar_axes[8], p)
    cb.ax.tick_params(labelsize=9)
    grid[8].set_title('(i) Model - observed', fontsize=10)
    annotate_skill(model_rg['omega_arag'], obs['OmegaA_an'], grid[8], fontsize=8, dim=['lat', 'lon'], weights=weight)

    for ax in grid:
        ax.set_xlim(-99, -35)
        ax.set_ylim(4, 59)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_facecolor('#cccccc')
        for s in ax.spines.values():
            s.set_visible(False)
    
    save_figure('alk_dic_omega', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    parser.add_argument('-d', '--dev', help='Use any available model data', action='store_true')
    args = parser.parse_args()
    plot_oa_metrics(args.pp_root, args.label, args.dev)
