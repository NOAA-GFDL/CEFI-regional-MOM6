"""
Compare model MLD with climatologies from Holte et al. 2017
and de Boyer 2022.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python mld_eval.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod/
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf

from plot_common import annotate_skill, autoextend_colorbar, get_map_norm, open_var


def plot_mld_eval(pp_root):
    model = open_var(pp_root, 'ocean_monthly', 'MLD_003')
    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    mom_mld_climo = model.groupby('time.month').mean('time').load()
    mom_mld_winter = mom_mld_climo.sel(month=slice(1, 3)).mean('month')

    argo = (
        xarray.open_dataset('/net2/acr/mld/Argo_mixedlayers_monthlyclim_03172021.nc')
        .swap_dims({'iLAT': 'lat', 'iLON': 'lon', 'iMONTH': 'month'})
        .mld_dt_mean
    )
    argo_grid = dict(lat=argo.lat, lon=argo.lon, lat_b=np.arange(-90, 90.1, 1), lon_b=np.arange(-180, 180.1, 1))
    argo_mld_winter = argo.sel(month=slice(1, 3)).mean('month')

    mom_to_argo = xesmf.Regridder(
        model_grid[['geolon', 'geolat', 'geolon_c', 'geolat_c']].rename({'geolon': 'lon', 'geolat': 'lat', 'geolon_c': 'lon_b', 'geolat_c': 'lat_b'}),
        argo_grid,
        method='conservative_normed',
        unmapped_to_nan=True,
        reuse_weights=False
    )
    mom_rg = mom_to_argo(mom_mld_winter)
    delta = mom_rg - argo_mld_winter

    deboyer = xarray.open_dataset('/net2/acr/deBoyer2022/mld_dr003_ref10m.nc')
    deboyer['time'] = np.arange(len(deboyer['time']), dtype='float64') + 1
    deboyer = deboyer.rename({'time': 'month'})
    deboyer_mld_winter =  deboyer.mld_dr003.where(deboyer.mask==1).sel(month=slice(1, 3)).mean('month')

    # the two observed datasets have the same grid
    delta_deboyer = mom_rg - deboyer_mld_winter

    fig = plt.figure(figsize=(8, 6))
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(2, 3),
        axes_class = (GeoAxes, dict(projection=ccrs.PlateCarree())),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )

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

    p = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, mom_mld_winter, cmap=cmap, norm=norm)
    grid[0].set_title('(a) Model')
    cbar = autoextend_colorbar(grid.cbar_axes[0], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))

    p = grid[1].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], deboyer_mld_winter, cmap=cmap, norm=norm)
    grid[1].set_title('(b) dBM 2022')
    cbar = autoextend_colorbar(grid.cbar_axes[1], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))

    p = grid[2].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], delta_deboyer, cmap=bias_cmap, norm=bias_norm)
    grid[2].set_title('(c) Model - dBM')
    cbar = autoextend_colorbar(grid.cbar_axes[2], p)
    cbar.ax.set_xlabel('Difference (m)')
    annotate_skill(mom_rg, deboyer_mld_winter, grid[2], dim=['lat', 'lon'], fontsize=8) # TODO: need to cosine weight

    p = grid[4].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], argo_mld_winter, cmap=cmap, norm=norm)
    grid[4].set_title('(b) Holte et al. 2017')
    cbar = autoextend_colorbar(grid.cbar_axes[4], p)
    cbar.ax.set_xlabel('Mean Jan-Mar MLD (m)')
    cbar.ax.set_xticks(np.arange(0, 301, 100, dtype=int))

    p = grid[5].pcolormesh(argo_grid['lon_b'], argo_grid['lat_b'], delta, cmap=bias_cmap, norm=bias_norm)
    grid[5].set_title('(c) Model - Holte')
    cbar = autoextend_colorbar(grid.cbar_axes[5], p)
    cbar.ax.set_xlabel('Difference (m)')
    annotate_skill(mom_rg, argo_mld_winter, grid[5], dim=['lat', 'lon'], fontsize=8) # TODO: need to cosine weight

    for i, ax in enumerate(grid):
        ax.set_xlim(-99, -35)
        ax.set_ylim(4, 59)
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
        
    plt.savefig('figures/mld003_eval.png', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    args = parser.parse_args()
    plot_mld_eval(args.pp_root)
