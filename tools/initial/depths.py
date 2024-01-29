import numpy as np
import xarray

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
