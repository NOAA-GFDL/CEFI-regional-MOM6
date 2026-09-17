import os
from collections.abc import Callable
from typing import Any

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import xarray
import xskillscore
from cartopy.mpl.ticker import (
    LatitudeFormatter,
    LongitudeFormatter,
)
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.colorbar import Colorbar
from matplotlib.colors import BoundaryNorm, ListedColormap

from .types import ArrayLike, ColorbarCapable

_PC = ccrs.PlateCarree()


def get_map_norm(
    cmap_name: str, levels: ArrayLike, no_offset: bool = True
) -> tuple[ListedColormap, BoundaryNorm]:
    """
    Get a discrete colormap and normalization for plotting with matplotlib.
    Set no_offset=False for a colormap similar to what xarray.plot() uses.
    """
    nlev = len(np.asarray(levels))
    cmap = plt.cm.get_cmap(cmap_name, nlev - int(no_offset))
    colors = list(cmap(np.arange(nlev)))
    colormap = ListedColormap(colors, '')
    norm = BoundaryNorm(levels, ncolors=nlev, clip=False)
    return colormap, norm


def _scalar_result(fun: Callable[..., Any], *args, **kwargs) -> float:
    res = np.asarray(fun(*args, **kwargs))
    if res.size != 1:
        raise ValueError('Expected a scalar value')
    return float(res.item())


def annotate_skill(
    model: xarray.DataArray,
    obs: xarray.DataArray,
    ax: Axes,
    dim: list[str] | None = None,
    x0: float = -98.5,
    y0: float = 54,
    yint: float = 4,
    xint: float = 4,
    weights: xarray.DataArray | None = None,
    cols: int = 1,
    proj: ccrs.CRS = _PC,
    plot_lat: bool = False,
    **kwargs,
) -> None:
    """
    Annotate an axis with model vs obs skill metrics
    """
    if dim is None:
        dim = ['yh', 'xh']
    kws = {'dim': dim, 'skipna': True}
    bias = _scalar_result(xskillscore.me, model, obs, **kws, weights=weights)
    rmse = _scalar_result(xskillscore.rmse, model, obs, **kws, weights=weights)
    corr = _scalar_result(xskillscore.pearson_r, model, obs, **kws, weights=weights)
    medae = _scalar_result(xskillscore.median_absolute_error, model, obs, **kws)

    ax.text(x0, y0, f'Bias: {float(bias):2.2f}', transform=proj, **kwargs)

    # Set plot_lat=True in order to plot skill along a line of latitude.
    # Otherwise, plot along longitude
    if plot_lat:
        ax.text(x0 - xint, y0, f'RMSE: {float(rmse):2.2f}', transform=proj, **kwargs)
        if cols == 1:
            ax.text(
                x0 - xint * 2,
                y0,
                f'MedAE: {float(medae):2.2f}',
                transform=proj,
                **kwargs,
            )
            ax.text(
                x0 - xint * 3, y0, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs
            )
        elif cols == 2:
            ax.text(
                x0, y0 + yint, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs
            )
            ax.text(
                x0 - xint,
                y0 + yint,
                f'Corr: {float(corr):2.2f}',
                transform=proj,
                **kwargs,
            )
        else:
            raise ValueError(f'Unsupported number of columns: {cols}')

    else:
        ax.text(x0, y0 - yint, f'RMSE: {float(rmse):2.2f}', transform=proj, **kwargs)
        if cols == 1:
            ax.text(
                x0,
                y0 - yint * 2,
                f'MedAE: {float(medae):2.2f}',
                transform=proj,
                **kwargs,
            )
            ax.text(
                x0, y0 - yint * 3, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs
            )
        elif cols == 2:
            ax.text(
                x0 + xint, y0, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs
            )
            ax.text(
                x0 + xint,
                y0 - yint,
                f'Corr: {float(corr):2.2f}',
                transform=proj,
                **kwargs,
            )
        else:
            raise ValueError(f'Unsupported number of columns: {cols}')


def autoextend_colorbar(
    ax: ColorbarCapable,
    plot: ScalarMappable,
    plot_data: ArrayLike | None = None,
    **kwargs,
) -> Colorbar:
    """
    Add a colorbar, setting the extend metric based on
    whether the plot data exceeds the plot limits.
    Pulls the data from the passed plot unless plot_data is passed.
    """
    norm_min = plot.norm.vmin
    norm_max = plot.norm.vmax

    if plot_data is None:
        plot_array = np.asarray(plot.get_array())
    else:
        plot_array = np.asarray(plot_data)

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


def add_ticks(
    ax: Axes,
    xticks: ArrayLike = np.arange(-100, -31, 1),  # noqa: B008
    yticks: ArrayLike = np.arange(2, 61, 1),  # noqa: B008
    xlabelinterval: int = 2,
    ylabelinterval: int = 2,
    fontsize: int | float = 10,
    projection: ccrs.CRS = _PC,
    **kwargs,
) -> None:
    """
    Add lat and lon ticks and labels to a plot axis.
    By default, tick at 1 degree intervals for x and y, and label every other tick.
    Additional kwargs are passed to LongitudeFormatter and LatitudeFormatter.
    """
    ax.yaxis.tick_right()
    ax.set_xticks(xticks, crs=projection)
    if xlabelinterval == 0:
        plt.setp(ax.get_xticklabels(), visible=False)
    else:
        plt.setp(
            [l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval != 0],
            visible=False,
            fontsize=fontsize,
        )
        plt.setp(
            [l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval == 0],
            fontsize=fontsize,
        )
    ax.set_yticks(yticks, crs=projection)
    if ylabelinterval == 0:
        plt.setp(ax.get_yticklabels(), visible=False)
    else:
        plt.setp(
            [l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval != 0],
            visible=False,
        )
        plt.setp(
            [l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval == 0],
            fontsize=fontsize,
        )
    lon_formatter = LongitudeFormatter(direction_label=False, **kwargs)
    lat_formatter = LatitudeFormatter(direction_label=False, **kwargs)
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)


def save_figure(
    fname: str, label: str = '', pdf: bool = False, output_dir: str = 'figures'
) -> None:
    if label == '':
        plt.savefig(
            os.path.join(output_dir, f'{fname}.png'), dpi=200, bbox_inches='tight'
        )
        if pdf:
            plt.savefig(os.path.join(output_dir, f'{fname}.pdf'), bbox_inches='tight')
    else:
        plt.savefig(
            os.path.join(output_dir, f'{fname}_{label}.png'),
            dpi=200,
            bbox_inches='tight',
        )
        if pdf:
            plt.savefig(
                os.path.join(output_dir, f'{fname}_{label}.pdf'), bbox_inches='tight'
            )
