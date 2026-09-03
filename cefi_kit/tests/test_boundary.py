import numpy as np
from pytest import approx

from cefi_kit import boundary


def test_rotate_uv():
    # Check for
    # github.com/NOAA-GFDL/CEFI-regional-MOM6/pull/94#pullrequestreview-2318247618
    urot, vrot = boundary.rotate_uv(
        np.array([0.0]), np.array([1.0]), np.array([np.pi / 2.0])
    )
    assert approx(urot) == 1.0
    assert approx(vrot) == 0.0


def test_ep2ap_ap2ep():
    # Test that a round trip ellipse -> amp/phase -> ellipse
    # ends with the same values as the start.
    start = [
        np.array([1.0]),
        np.array([0.5]),
        np.array([np.pi / 2]),
        np.array([np.pi / 2]),
    ]
    ua, va, up, vp = boundary.ep2ap(*start)
    uc = ua * np.exp(-1j * up)
    vc = va * np.exp(-1j * vp)
    finish = boundary.ap2ep(uc, vc)
    for expected, actual in zip(start, finish, strict=True):
        assert approx(expected) == actual


def test_ap2ep_ep2ep():
    # Test that a round trip amp/phase -> ellipse -> amp/phase
    # ends with the same values as the start.
    start = [1.0, 0.5, np.pi, -np.pi / 2]
    ua, va, up, vp = start
    uc = ua * np.exp(-1j * up)
    vc = va * np.exp(-1j * vp)
    ep = boundary.ap2ep(uc, vc)
    finish = boundary.ep2ap(*ep)
    for expected, actual in zip(start, finish, strict=True):
        assert approx(expected) == actual
