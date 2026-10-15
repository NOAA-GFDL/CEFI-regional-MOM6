import numpy as np
import pytest

from cefi_kit import grids


def test_vgrid_to_interfaces():
    # be sure it fails if sum of layer thicknesses is > set bottom depth
    with pytest.raises(ValueError, match='exceeds specified bottom depth'):
        grids.vgrid_to_interfaces(np.array([10, 10, 10]), max_depth=20.0)

    # = to bottom depth is ok
    interfaces = grids.vgrid_to_interfaces(np.array([10, 10, 10]), max_depth=30.0)
    assert pytest.approx(30.0) == interfaces[-1]

    # be sure that bottom depth < max_depth is replaced with max_depth
    interfaces = grids.vgrid_to_interfaces(np.array([10, 10, 10]), max_depth=40.0)
    assert pytest.approx(40.0) == interfaces[-1]
