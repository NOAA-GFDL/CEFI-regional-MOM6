"""
Comparison of model seasonal mean surface phosphate and nitrate with the World Ocean Atlas data
How to use:
python nutrients.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
from calendar import month_abbr
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import cmcrameri.cm as cmc
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
from string import ascii_lowercase
import xarray
import xesmf

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../physics'))
from plot_common import open_var, autoextend_colorbar, get_map_norm, annotate_skill, save_figure

PC = ccrs.PlateCarree()


def load_woa():
    woa_seasons = {1: 13, 4: 14, 7: 15, 10:16}
    woa = []
    for month, woa_label in woa_seasons.items():
        woa_files = [
            f'/work/acr/woa/WOA18/NO3/woa18_all_n{woa_label}_01.nc',
            f'/work/acr/woa/WOA18/O2/woa18_all_o{woa_label}_01.nc',
            f'/work/acr/woa/WOA18/PO4/woa18_all_p{woa_label}_01.nc',
            f'/work/acr/woa/WOA18/SiO4/woa18_all_i{woa_label}_01.nc'
        ]
        ds = (
            # compat='override' because depth_bnds is different for seasonal datasets?
            xarray.open_mfdataset(woa_files, decode_times=False, compat='override')
            .rename({'depth': 'z', 'n_an': 'no3', 'o_an': 'o2', 'p_an': 'po4', 'i_an': 'sio4'})
            [['no3', 'o2', 'po4', 'sio4']]
            .squeeze()
            # micromoles per kg -> millimoles per m3
        )
        ds['month'] = month
        woa.append(ds)
        
    woa_climo = xarray.concat(woa, dim='month').isel(z=0)
    return woa_climo


def plot_nutrients(pp_root, label):
    grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    variables = ['sfc_no3', 'sfc_po4']
    mod = xarray.merge((open_var(pp_root, 'ocean_cobalt_sfc', v) for v in variables))
    mod = mod.rename({'sfc_no3': 'no3', 'sfc_po4': 'po4'})
    mod = mod * 1000 * 1035 # mol kg-1 -> mmol m-3
    mod_climo = mod.resample(time='1QS').mean('time').groupby('time.month').mean('time').load()
    woa_climo = load_woa()
    woa_grid = {
        'lat': woa_climo.lat,
        'lon': woa_climo.lon,
        'lat_b': np.arange(-90, 90.1, 1),
        'lon_b': np.arange(-180, 180.1, 1)
    }
    mom_grid = {
        'lat': grid.geolat,
        'lon': grid.geolon,
        'lat_b': grid.geolat_c,
        'lon_b': grid.geolon_c
    }
    mom_to_woa = xesmf.Regridder(
        mom_grid, 
        woa_grid, 
        method='conservative_normed',
        unmapped_to_nan=True,
        reuse_weights=False
    )
    mom_rg = mom_to_woa(mod_climo).load()
    delta = mom_rg - woa_climo

    var = 'no3'
    cmap, norm = get_map_norm('cmc.davos', np.arange(0, 14, 1), no_offset=True)
    bias_cmap, bias_norm = get_map_norm('cmc.vik', np.arange(-4, 4.1, .5), no_offset=True)
    common = dict(norm=norm, cmap=cmap)

    fig = plt.figure(figsize=(10, 6))
    agrid = AxesGrid(fig, 111,
        nrows_ncols=(3, 4),
        axes_class=(GeoAxes, dict(projection=PC)),
        axes_pad=0.3,
        cbar_location='right',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='8%',
        label_mode=''
    )

    for i, m in enumerate(mod_climo.month):
        months = f'{month_abbr[int(m)]}-{month_abbr[int(m)+2]}'
        p0 = agrid[i].pcolormesh(grid.geolon_c, grid.geolat_c, mod_climo.sel(month=m)[var], **common)
        agrid[i].set_title(f'({ascii_lowercase[i]}) Model {months}', fontsize=10)
        p1 = agrid[i+4].pcolormesh(woa_grid['lon_b'], woa_grid['lat_b'], woa_climo.sel(month=m)[var], **common)
        agrid[i+4].set_title(f'({ascii_lowercase[i+4]}) WOA {months}', fontsize=10)
        p2 = agrid[i+8].pcolormesh(woa_grid['lon_b'], woa_grid['lat_b'], delta.sel(month=m)[var], cmap=bias_cmap, norm=bias_norm)
        agrid[i+8].set_title(f'({ascii_lowercase[i+8]}) Model-WOA {months}', fontsize=10)
        weight = xarray.ones_like(woa_climo.sel(month=m)[var]) * np.cos(np.deg2rad(woa_climo.lat))
        annotate_skill(mom_rg.sel(month=m)[var], woa_climo.sel(month=m)[var], agrid[i+8], fontsize=8, dim=['lat', 'lon'], weights=weight)

        if i == 0:
            cbar0 = agrid.cbar_axes[0].colorbar(p0, extend='max')
            cbar1 = agrid.cbar_axes[1].colorbar(p1, extend='max')
            cbar2 = agrid.cbar_axes[2].colorbar(p2, extend='both')
            for cb in [cbar0, cbar1, cbar2]:
                cb.ax.set_title('    mmol m$^{-3}$', fontsize=9)
                cb.ax.tick_params(labelsize=9)

    for ax in agrid:
        ax.set_xlim(-100, -35)
        ax.set_ylim(4, 59)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)
            
    plt.suptitle('Surface NO$_3$', y=0.95, fontweight='bold')
    save_figure('surface_no3_woa', label=label)

    var = 'po4'
    cmap, norm = get_map_norm('cmc.davos', np.arange(0, 1.21, .1), no_offset=True)
    bias_cmap, bias_norm = get_map_norm('cmc.vik', np.arange(-.3, .31, .05), no_offset=True)
    common = dict(norm=norm, cmap=cmap)

    fig = plt.figure(figsize=(10, 6))
    agrid = AxesGrid(fig, 111,
        nrows_ncols=(3, 4),
        axes_class=(GeoAxes, dict(projection=PC)),
        axes_pad=0.3,
        cbar_location='right',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='8%',
        label_mode=''
    )

    for i, m in enumerate(mod_climo.month):
        months = f'{month_abbr[int(m)]}-{month_abbr[int(m)+2]}'
        p0 = agrid[i].pcolormesh(grid.geolon_c, grid.geolat_c, mod_climo.sel(month=m)[var], **common)
        agrid[i].set_title(f'({ascii_lowercase[i]}) Model {months}', fontsize=10)
        p1 = agrid[i+4].pcolormesh(woa_grid['lon_b'], woa_grid['lat_b'], woa_climo.sel(month=m)[var], **common)
        agrid[i+4].set_title(f'({ascii_lowercase[i+4]}) WOA {months}', fontsize=10)
        p2 = agrid[i+8].pcolormesh(woa_grid['lon_b'], woa_grid['lat_b'], delta.sel(month=m)[var], cmap=bias_cmap, norm=bias_norm)
        agrid[i+8].set_title(f'({ascii_lowercase[i+8]}) Model-WOA {months}', fontsize=10)
        weight = xarray.ones_like(woa_climo.sel(month=m)[var]) * np.cos(np.deg2rad(woa_climo.lat))
        annotate_skill(mom_rg.sel(month=m)[var], woa_climo.sel(month=m)[var], agrid[i+8], fontsize=8, dim=['lat', 'lon'], weights=weight)
        if i == 0:
            cbar0 = autoextend_colorbar(agrid.cbar_axes[0], p0)
            cbar1 = autoextend_colorbar(agrid.cbar_axes[1], p1)
            cbar2 = autoextend_colorbar(agrid.cbar_axes[2], p2)
            for cb in [cbar0, cbar1, cbar2]:
                cb.ax.set_title('    mmol m$^{-3}$', fontsize=9)
                cb.ax.tick_params(labelsize=9)

    for ax in agrid:
        ax.set_xlim(-100, -35)
        ax.set_ylim(4, 59)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)
            
    plt.suptitle('Surface PO$_4$', y=0.95, fontweight='bold')
    save_figure('surface_po4_woa', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_nutrients(args.pp_root, args.label)
