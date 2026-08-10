from os import PathLike
from typing import Protocol

from matplotlib.cm import ScalarMappable
from matplotlib.colorbar import Colorbar
from numpy.typing import ArrayLike, NDArray
from xarray import DataArray

__all__ = ['ArrayLike', 'ColorbarCapable', 'NDArray', 'NDArrayLike', 'PathLike']

NDArrayLike = NDArray | DataArray


class ColorbarCapable(Protocol):
    """A type (such as matplotlib figure or axes) with a colorbar method"""

    def colorbar(self, mappable: ScalarMappable, **kwargs) -> Colorbar: ...
