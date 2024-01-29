"""
Compare the model 2005-019 sea surface temperature trends from OISST and GLORYS. 
How to use:
python sst_trends.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import colorcet
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf

from plot_common import autoextend_colorbar, corners, get_map_norm, annotate_skill, open_var, save_figure

PC = ccrs.PlateCarree()


def get_3d_trends(x, y):
    x = np.array(x)
    y2 = np.array(y).reshape((len(x), -1))
    coefs = np.polyfit(x, y2, 1)
    trends = coefs[0, :].reshape(y.shape[1:])
    return trends


def plot_sst_trends(pp_root, label):
    model = (
        open_var(pp_root, 'ocean_monthly', 'tos')
        .sel(time=slice('2005', '2019'))
        .resample(time='1AS')
        .mean('time')
        .load()
    )
    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')

    model_trend = get_3d_trends(model['time.year'], model) * 10 # -> C / decade
    model_trend = xarray.DataArray(model_trend, dims=['yh', 'xh'], coords={'yh': model.yh, 'xh': model.xh})

    oisst = (
        xarray.open_mfdataset([f'/work/acr/oisstv2/sst.month.mean.{y}.nc' for y in range(2005, 2020)])
        .sst
        .sel(lat=slice(0, 60), lon=slice(360-100, 360-30))
        .resample(time='1AS')
        .mean('time')
        .load()
    )
    oisst_trend = get_3d_trends(oisst['time.year'], oisst) * 10 # -> C / decade

    glorys = (
        xarray.open_dataset('/work/acr/mom6/diagnostics/glorys/glorys_sfc.nc')
        ['thetao']
        .sel(time=slice('2005', '2019'))
        .resample(time='1AS')
        .mean('time')
    )
    glorys_trend = get_3d_trends(glorys['time.year'], glorys) * 10 # -> C / decade

    oisst_lonc, oisst_latc = corners(oisst.lon, oisst.lat)
    oisst_lonc -= 360
    oisst_to_mom = xesmf.Regridder({'lat': oisst.lat, 'lon': oisst.lon}, model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}), method='bilinear')

    glorys_lonc, glorys_latc = corners(glorys.lon, glorys.lat)
    glorys_to_mom = xesmf.Regridder(glorys, model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}), method='bilinear')

    glorys_rg = glorys_to_mom(glorys_trend)
    glorys_rg = xarray.DataArray(glorys_rg, dims=['yh', 'xh'], coords={'yh': model.yh, 'xh': model.xh})
    glorys_delta = model_trend - glorys_rg

    oisst_rg = oisst_to_mom(oisst_trend)
    oisst_rg = xarray.DataArray(oisst_rg, dims=['yh', 'xh'], coords={'yh': model.yh, 'xh': model.xh})
    oisst_delta = model_trend - oisst_rg

    fig = plt.figure(figsize=(10, 14))
    grid = AxesGrid(fig, 111, 
        nrows_ncols=(2, 3),
        axes_class = (GeoAxes, dict(projection=PC)),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )

    cmap, norm = get_map_norm('cet_CET_D1', np.arange(-2, 2.1, .25), no_offset=True)
    common = dict(cmap=cmap, norm=norm)

    bias_cmap, bias_norm = get_map_norm('RdBu_r', np.arange(-1.5, 1.51, .25), no_offset=True)
    bias_common = dict(cmap=bias_cmap, norm=bias_norm)

    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_trend, **common)
    grid[0].set_title('(a) Model')
    cbar0 = autoextend_colorbar(grid.cbar_axes[0], p0)
    cbar0.ax.set_xlabel('SST trend (°C / decade)')
    cbar0.set_ticks([-2, -1, 0, 1, 2])
    cbar0.set_ticklabels([-2, -1, 0, 1, 2])

    p1 = grid[1].pcolormesh(oisst_lonc, oisst_latc, oisst_trend, **common)
    grid[1].set_title('(b) OISST')

    grid[2].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, oisst_delta, **bias_common)
    grid[2].set_title('(c) Model - OISST')
    annotate_skill(model_trend, oisst_rg, grid[2], weights=model_grid.areacello)

    grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_trend, **common)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('SST trend (°C / decade)')
    cbar1.set_ticks([-2, -1, 0, 1, 2])
    cbar1.set_ticklabels([-2, -1, 0, 1, 2])

    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, glorys_delta, **bias_common)
    grid[5].set_title('(e) Model - GLORYS12')
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SST trend difference (°C / decade)')
    annotate_skill(model_trend, glorys_rg, grid[5], weights=model_grid.areacello)

    for i, ax in enumerate(grid):
        ax.set_xlim(-99, -35)
        ax.set_ylim(4, 59)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        if i != 3:
            ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)

    save_figure('sst_trends', label=label)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_sst_trends(args.pp_root, args.label)
