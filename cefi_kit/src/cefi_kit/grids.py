import numpy as np
import xarray


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