import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter, LatitudeLocator, LongitudeLocator
from glob import glob
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import os
import xarray
import xskillscore

def center_to_outer(center, left=None, right=None):
    """
    Given an array of center coordinates, find the edge coordinates,
    including extrapolation for far left and right edge.
    """
    edges = 0.5 * (center.values[0:-1] + center.values[1:])
    if left is None:
        left = edges[0] - (edges[1] - edges[0])
    if right is None:
        right = edges[-1] + (edges[-1] - edges[-2])
    outer = np.hstack([left, edges, right])
    return outer


def corners(lon, lat):
    """
    Given 1D lon and lat, return 1D lon and lat corners 
    for use in pcolormesh or xesmf conservative
    """
    lonc = center_to_outer(lon)
    latc = center_to_outer(lat)
    assert len(lonc) == len(lon) + 1
    assert len(latc) == len(lat) + 1
    return lonc, latc


def get_map_norm(cmap, levels, no_offset=True):
    """
    Get a discrete colormap and normalization for plotting with matplotlib.
    Set no_offset=False to obtain a colormap that is similar to what xarray.plot() yields.
    """
    nlev = len(levels)
    cmap = plt.cm.get_cmap(cmap, nlev-int(no_offset))
    colors = list(cmap(np.arange(nlev)))
    cmap = ListedColormap(colors, "")
    norm = BoundaryNorm(levels, ncolors=nlev, clip=False)
    return cmap, norm

def annotate_skill(model, obs, ax, dim=['yh', 'xh'], x0=-98.5, y0=54, yint=4, xint=4, weights=None, cols=1, **kwargs):
    """
    Annotate an axis with model vs obs skill metrics
    """
    bias = xskillscore.me(model, obs, dim=dim, skipna=True, weights=weights)
    rmse = xskillscore.rmse(model, obs, dim=dim, skipna=True, weights=weights)
    corr = xskillscore.pearson_r(model, obs, dim=dim, skipna=True, weights=weights)
    medae = xskillscore.median_absolute_error(model, obs, dim=dim, skipna=True)
    ax.text(x0, y0, f'Bias: {float(bias):2.2f}', **kwargs)
    ax.text(x0, y0-yint, f'RMSE: {float(rmse):2.2f}', **kwargs)
    if cols == 1:
        ax.text(x0, y0-yint*2, f'MedAE: {float(medae):2.2f}', **kwargs)
        ax.text(x0, y0-yint*3, f'Corr: {float(corr):2.2f}', **kwargs)
    elif cols == 2:
        ax.text(x0+xint, y0, f'MedAE: {float(medae):2.2f}', **kwargs)
        ax.text(x0+xint, y0-yint, f'Corr: {float(corr):2.2f}', **kwargs)
    else:
        raise ValueError(f'Unsupported number of columns: {cols}')
    
def autoextend_colorbar(ax, plot, plot_array=None, **kwargs):
    """
    Add a colorbar, setting the extend metric based on 
    whether the plot data exceeds the plot limits.
    Pulls the data from the passed plot unless plot_array is passed.
    """
    norm_min = plot.norm.vmin
    norm_max = plot.norm.vmax
    
    if plot_array is None:
        plot_array = plot.get_array()
        
    actual_min = plot_array.min()
    actual_max = plot_array.max()
    
    if actual_min < norm_min and actual_max > norm_max:
        extend = 'both'
    elif actual_min < norm_min:
        extend = 'min'
    elif actual_max > norm_max:
        extend = 'max'
    else:
        extend = 'neither'
    return ax.colorbar(plot, extend=extend, **kwargs)

def add_ticks(ax, xticks=np.arange(-100, -31, 1), yticks=np.arange(2, 61, 1), xlabelinterval=2, ylabelinterval=2, fontsize=10, **kwargs):
    """
    Add lat and lon ticks and labels to a plot axis.
    By default, tick at 1 degree intervals for x and y, and label every other tick.
    Additional kwargs are passed to LongitudeFormatter and LatitudeFormatter.
    """
    ax.yaxis.tick_right()
    ax.set_xticks(xticks, crs=ccrs.PlateCarree())
    if xlabelinterval == 0:
        plt.setp(ax.get_xticklabels(), visible=False)
    else:
        plt.setp([l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval != 0], visible=False, fontsize=fontsize)
        plt.setp([l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval == 0], fontsize=fontsize)
    ax.set_yticks(yticks, crs=ccrs.PlateCarree())
    if ylabelinterval == 0:
        plt.setp(ax.get_yticklabels(), visible=False)
    else:
        plt.setp([l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval != 0], visible=False)
        plt.setp([l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval == 0], fontsize=fontsize)
    lon_formatter = LongitudeFormatter(direction_label=False, **kwargs)
    lat_formatter = LatitudeFormatter(direction_label=False, **kwargs)
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

def open_var(pp_root, kind, var):
    freq = 'daily' if 'daily' in kind else 'monthly'
    longslice = '19930101-20191231' if freq == 'daily' else '199301-201912'
    longfile = os.path.join(pp_root, 'pp', kind, 'ts', freq, '27yr', f'{kind}.{longslice}.{var}.nc')
    if os.path.isfile(longfile):
        os.system(f'dmget {longfile}')
        return xarray.open_dataset(longfile)[var]
    elif len(glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '1yr', f'{kind}.*.{var}.nc'))) > 0:
        files = glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '1yr', f'{kind}.*.{var}.nc'))
        os.system(f'dmget {" ".join(files)}')
        return xarray.open_mfdataset(files)[var]
    elif len(glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '5yr', f'{kind}.*.{var}.nc'))) > 0:
        files = glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '5yr', f'{kind}.*.{var}.nc'))
        os.system(f'dmget {" ".join(files)}')
        return xarray.open_mfdataset(files)[var]
    else:
        raise Exception('Did not find postprocessed files')

def save_figure(fname, label='', pdf=False, output_dir='figures'):
    if label == '':
        plt.savefig(os.path.join(output_dir, f'{fname}.png'), dpi=200, bbox_inches='tight')
        if pdf:
            plt.savefig(os.path.join(output_dir, f'{fname}.pdf'), bbox_inches='tight')
    else:
        plt.savefig(os.path.join(output_dir, f'{fname}_{label}.png'), dpi=200, bbox_inches='tight')
        if pdf:
            plt.savefig(os.path.join(output_dir, f'{fname}_{label}.pdf'), bbox_inches='tight')
