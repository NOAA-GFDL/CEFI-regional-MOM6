"""
Compare model SSS with 1993--2019 data from regional climatologies and GLORYS.
Uses whatever model data can be found within the directory pp_root,
and does not try to match the model and observed time periods.
How to use:
python sss_eval.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import os
import xarray
import xesmf

from plot_common import annotate_skill, autoextend_colorbar, corners, get_map_norm, open_var


def plot_sss_eval(pp_root):
    model = open_var(pp_root, 'ocean_monthly', 'sos')
    model_grid = xarray.open_dataset('../data/geography/ocean_static.nc')
    target_grid = model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'})
    model_ave = model.mean('time').load()

    # Open 3 different regional climatology datasets and merge together.
    # These are decadal average files, except the most recent decade
    # has been extended, so calculate a weighted average in time.
    rcdir = '/net2/acr/regional_climatologies/'

    sw = xarray.open_mfdataset([os.path.join(rcdir, 'swa_95A4_s00_10.nc'), os.path.join(rcdir, 'swa_A5B7_s00_10.nc')], decode_times=False)
    weights = xarray.DataArray([2004-1995+1, 2017-2005+1], dims=['time'], coords={'time': sw.time})
    sw = sw.weighted(weights).mean('time')

    gom = xarray.open_mfdataset([os.path.join(rcdir, 'gom_95A4_s00_10.nc'), os.path.join(rcdir, 'gom_A5B7_s00_10.nc')], decode_times=False)
    weights = xarray.DataArray([2004-1995+1, 2017-2005+1], dims=['time'], coords={'time': gom.time})
    gom = gom.weighted(weights).mean('time')

    nwa = xarray.open_mfdataset([os.path.join(rcdir, 'nwa_95A4_s00_10.nc'), os.path.join(rcdir, 'nwa_A5B7_s00_10.nc')], decode_times=False, combine='nested', compat='override')
    weights = xarray.DataArray([2004-1995+1, 2017-2005+1], dims=['time'], coords={'time': nwa.time})
    nwa = nwa.weighted(weights).mean('time')

    # Convert to a common grid to merge the datasets together.
    # concat each dataset onto a new dimension,
    # then average over the dimension.
    # with no overlap, only one region has data at any point, 
    # so mean ignores the nans from other regions and selects the available data.
    regional_grid = {'lat': np.arange(10.05, 65.10, 0.1), 'lon': np.arange(-97.95, -39.90, 0.1)}
    # For plotting later
    regional_gridc = {'lat': np.arange(10.00, 65.15, 0.1), 'lon': np.arange(-98.0, -39.85, 0.1)}
    nwa_i = xesmf.Regridder(nwa, regional_grid, method='bilinear', unmapped_to_nan=True)(nwa.s_an.isel(depth=0))
    sw_i = xesmf.Regridder(sw, regional_grid, method='bilinear', unmapped_to_nan=True)(sw.s_an.isel(depth=0))
    gom_i = xesmf.Regridder(gom, regional_grid, method='bilinear', unmapped_to_nan=True)(gom.s_an.isel(depth=0))
    combined = xarray.concat([nwa_i, sw_i, gom_i], dim='region').mean('region')

    # Now interpolate to the model grid to compare.
    regional_to_mod = xesmf.Regridder({'lat': combined.lat, 'lon': combined.lon}, model_grid[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}), method='bilinear')
    regional_rg = regional_to_mod(combined + 273) 
    regional_rg = regional_rg.where(regional_rg > 0) - 273
    delta_regional = model_ave - regional_rg

    glorys = xarray.open_dataset('/work/acr/mom6/diagnostics/glorys/glorys_sfc.nc')['so'] #.rename({'longitude': 'lon', 'latitude': 'lat'})
    glorys_lonc, glorys_latc = corners(glorys.lon, glorys.lat)
    glorys_ave = glorys.mean('time').load()
    glorys_to_mom = xesmf.Regridder(glorys_ave, target_grid, method='bilinear', unmapped_to_nan=True)
    glorys_rg = glorys_to_mom(glorys_ave)
    delta_glorys = model_ave - glorys_rg

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

    # Discrete levels for SSS plots
    levels = np.arange(25, 39, 1)
    # Discrete levels for difference plots
    bias_levels = np.arange(-2, 2.1, 0.25)

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

    # Model 
    p0 = grid[0].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, model_ave, **common)
    grid[0].set_title('(a) Model')
    cbar0 = autoextend_colorbar(grid.cbar_axes[0], p0)
    cbar0.ax.set_xlabel('Mean SSS')

    # Regional climatologies
    grid[1].pcolormesh(regional_gridc['lon'], regional_gridc['lat'], combined, **common)
    grid[1].set_title('(b) Regional climatologies')

    # Model - regional
    grid[2].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_regional, **bias_common)
    grid[2].set_title('(c) Model - climatologies')
    # rechunk data
    model_ave = model_ave.chunk(dict(yh=-1, xh=-1))
    regional_rg = regional_rg.chunk(dict(yh=-1, xh=-1))
    annotate_skill(model_ave, regional_rg, grid[2], weights=model_grid.areacello)

    # GLORYS
    p1 = grid[4].pcolormesh(glorys_lonc, glorys_latc, glorys_ave, **common)
    grid[4].set_title('(d) GLORYS12')
    cbar1 = autoextend_colorbar(grid.cbar_axes[1], p1)
    cbar1.ax.set_xlabel('Mean SSS')

    # Model - GLORYS
    p2 = grid[5].pcolormesh(model_grid.geolon_c, model_grid.geolat_c, delta_glorys, **bias_common)
    cbar2 = autoextend_colorbar(grid.cbar_axes[2], p2)
    cbar2.ax.set_xlabel('SSS difference')
    cbar2.ax.set_xticks([-2, -1, 0, 1, 2])
    grid[5].set_title('(e) Model - GLORYS12')
    annotate_skill(model_ave, glorys_rg, grid[5], weights=model_grid.areacello)

    for ax in grid:
        ax.set_xlim(-99, -35)
        ax.set_ylim(4, 59)
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
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    args = parser.parse_args()
    plot_sss_eval(args.pp_root)
