"""The CMYK conversion: ink stays under the limit and the colours stay themselves."""

from itertools import product

import pytest

from kinyonga import cmyk

GRID = [(r / 6, g / 6, b / 6) for r, g, b in product(range(7), repeat=3)]
NAVY = (11 / 255, 18 / 255, 32 / 255)


def test_navy_is_built_on_black_and_stays_under_the_limit():
    c, m, y, k = cmyk.to_cmyk(NAVY)
    assert k > 0.8
    assert c + m + y + k <= cmyk.INK_LIMIT


def test_no_colour_exceeds_the_limit_of_ink():
    for rgb in GRID:
        assert sum(cmyk.to_cmyk(rgb)) <= cmyk.INK_LIMIT + 1e-9
        assert sum(cmyk.to_cmyk(rgb, limit=2.0)) <= 2.0 + 1e-9


def test_neutral_greys_use_the_black_plate_alone():
    for level in (0.0, 0.3, 0.5, 1.0):
        assert cmyk.to_cmyk((level, level, level)) == pytest.approx((0.0, 0.0, 0.0, 1.0 - level))


def test_light_colours_get_almost_no_black():
    assert cmyk.to_cmyk((0.88, 0.93, 0.97))[3] < 0.1
    assert cmyk.to_cmyk((1.0, 1.0, 1.0)) == (0.0, 0.0, 0.0, 0.0)


def test_the_conversion_inverts_where_the_limit_does_not_bind():
    for rgb in GRID:
        c, m, y, k = cmyk.to_cmyk(rgb, limit=4.0)
        back = ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        assert back == pytest.approx(rgb, abs=1e-9)


def test_convert_keeps_the_length_and_rewrites_fill_and_stroke():
    pdf = b"0.0431372549 0.0705882353 0.1254901961 rg\n0.5 0.5 0.5 RG\n"
    out = cmyk.convert(pdf)
    assert len(out) == len(pdf)
    assert out.startswith(b"0.7359 0.5679 0.2318 0.8367 k")
    assert b" G" in out


def test_a_colour_too_short_to_be_replaced_in_place_is_refused():
    with pytest.raises(ValueError, match="too short"):
        cmyk.convert(b"0 0.5 1 rg\n")
