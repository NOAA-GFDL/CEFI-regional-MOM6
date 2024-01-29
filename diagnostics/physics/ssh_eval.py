"""
Compare model SSH with 1993--2019 data from GLORYS.
Includes a plot of the Gulf Stream position and index,
and a comparison of time mean SSH.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python ssh_eval.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""

import cartopy.feature as feature
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf

from plot_common import autoextend_colorbar, corners, get_map_norm, open_var, add_ticks, annotate_skill, save_figure



_LAND_50M = feature.NaturalEarthFeature(
    'physical', 'land', '50m',
    edgecolor='face',
    facecolor='#999999'
)

PC = ccrs.PlateCarree()


def plot_ssh_eval(pp_root, label):
    # Ideally would use SSH, but some diag_tables only saved zos
    try:
        model_ssh = open_var(pp_root, 'ocean_monthly', 'ssh')
    except:
        print('Using zos')
        model_ssh = open_var(pp_root, 'ocean_monthly', 'zos')
        
    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    model_ssh_ave = model_ssh.mean('time')

    glorys_zos = xarray.open_mfdataset('/work/acr/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/glorys_monthly_z_fine_*.nc').zos
    glorys_zos = glorys_zos.rename({'latitude': 'lat', 'longitude': 'lon'})
    glorys_zos_ave = glorys_zos.mean('time').load()
    glorys_lonc, glorys_latc = corners(glorys_zos.lon, glorys_zos.lat)

    # Plot of time-mean SSH.
    fig = plt.figure(figsize=(6, 8))
    grid = AxesGrid(fig, 111,
        nrows_ncols=(2, 1),
        axes_class = (GeoAxes, dict(projection=PC)),
        axes_pad=0.55,
        cbar_location='right',
        cbar_mode='edge',
        cbar_pad=0.5,
        cbar_size='5%',
        label_mode=''
    )

    levels = np.arange(-1.1, .8, .1)
    try:
        import colorcet
    except ModuleNotFoundError:
        cm = 'rainbow'
    else:
        cm = 'cet_CET_L8'
    cmap, norm = get_map_norm(cm, levels=levels)

    xl, xr = -90, -35
    yb, yt = 20, 50

    target_grid = model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'})
    glorys_to_mom = xesmf.Regridder(glorys_zos_ave, target_grid, method='bilinear', unmapped_to_nan=True)
    glorys_rg = glorys_to_mom(glorys_zos_ave)
    mod_mask = (model_grid.geolon >= xl) & (model_grid.geolon <= xr) & (model_grid.geolat >= yb) & (model_grid.geolat <= yt)


    p = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ssh_ave, cmap=cmap, norm=norm)
    cbar = autoextend_colorbar(grid.cbar_axes[0], p)
    cbar.ax.set_title('SSH (m)', fontsize=10)
    grid[0].set_title('(a) Model mean SSH')

    p = grid[1].pcolormesh(glorys_lonc, glorys_latc, glorys_zos_ave, cmap=cmap, norm=norm)
    cbar = autoextend_colorbar(grid.cbar_axes[1], p)
    cbar.ax.set_title('SSH (m)', fontsize=10)
    grid[1].set_title('(b) GLORYS12 mean SSH')
    annotate_skill(
        model_ssh_ave.where(mod_mask),
        glorys_rg.where(mod_mask),
        grid[1],
        weights=model_grid.areacello.where(mod_mask).fillna(0),
        x0=-89,
        y0=48,
        yint=2,
        fontsize=8
    )

    for ax in grid:
        add_ticks(ax, xlabelinterval=2, ylabelinterval=2, xticks=np.arange(-100, -31, 5), yticks=np.arange(0, 61, 5))
        ax.set_xlim(xl, xr)
        ax.set_ylim(yb, yt)
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)

    save_figure('mean_ssh_eval', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_ssh_eval(args.pp_root, args.label)
