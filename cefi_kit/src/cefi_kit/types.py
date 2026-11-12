from os import PathLike
from typing import TYPE_CHECKING, Protocol

from numpy.typing import ArrayLike, NDArray
from xarray import DataArray

__all__ = ['ArrayLike', 'ColorbarCapable', 'NDArray', 'NDArrayLike', 'PathLike']

NDArrayLike = NDArray | DataArray

# Keep matplotlib optional
if TYPE_CHECKING:
    from matplotlib.cm import ScalarMappable
    from matplotlib.colorbar import Colorbar


class ColorbarCapable(Protocol):
    """A type (such as matplotlib figure or axes) with a colorbar method"""

    def colorbar(self, mappable: 'ScalarMappable', **kwargs) -> 'Colorbar': ...
