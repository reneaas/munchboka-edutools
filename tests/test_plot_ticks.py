import math

import pytest

from munchboka_edutools.directives.plot import _endpoint_excluding_multiple_ticks


def test_endpoint_excluding_multiple_ticks_omits_pi_axis_bounds():
    ticks = _endpoint_excluding_multiple_ticks(-math.pi, math.pi, math.pi / 2)

    assert ticks == pytest.approx([-math.pi / 2, 0.0, math.pi / 2])


def test_endpoint_excluding_multiple_ticks_keeps_interior_pi_multiples():
    ticks = _endpoint_excluding_multiple_ticks(-2 * math.pi, 2 * math.pi, math.pi)

    assert ticks == pytest.approx([-math.pi, 0.0, math.pi])

