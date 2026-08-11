from os import path

import numpy as np
import xarray
import xesmf


def center_to_outer(center, left=None, right=None):
    """
    Given an array of center coordinates, find the edge coordinates,
    including extrapolation for far left and right edge.
    """
    if hasattr(center,'values'): # handle xarray dataarays and similar objects
        edges = 0.5 * (center.values[0:-1] + center.values[1:])
    else:
        edges = 0.5 * (center[0:-1] + center[1:])
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


def mom_center_area(supergrid_area):
    return (supergrid_area[::2, ::2] + supergrid_area[1::2, 1::2]) + (supergrid_area[1::2, ::2] + supergrid_area[::2, 1::2])


def hgrid_to_xesmf(hgrid):
    return {
        'lon': hgrid.x[1::2, 1::2],
        'lon_b': hgrid.x[::2, ::2],
        'lat': hgrid.y[1::2, 1::2],
        'lat_b': hgrid.y[::2, ::2]
    }


def vgrid_to_interfaces(vgrid, max_depth=6500.0):
    if isinstance(vgrid, xarray.DataArray):
        vgrid = vgrid.data
    zi = np.concatenate([[0], np.cumsum(vgrid)])
    zi[-1] = max_depth
    return zi


def vgrid_to_layers(vgrid, max_depth=6500.0):
    if isinstance(vgrid, xarray.DataArray):
        vgrid = vgrid.data
    ints = vgrid_to_interfaces(vgrid, max_depth=max_depth)
    z = (ints + np.roll(ints, shift=1)) / 2
    layers = z[1:]
    return layers


def reuse_regrid(*args, **kwargs):
    filename = kwargs.pop('filename', None)
    reuse_weights = kwargs.pop('reuse_weights', False)

    if reuse_weights:
        if path.isfile(filename):
            return xesmf.Regridder(*args, reuse_weights=True, filename=filename, **kwargs)
        else:
            regrid = xesmf.Regridder(*args, **kwargs)
            regrid.to_netcdf(filename)
            return regrid
    else:
        regrid = xesmf.Regridder(*args, **kwargs)
        return regrid
