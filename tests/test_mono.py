"""Monospaced families: one advance for every glyph, and letters that fit the cell."""

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, build_family, latin, mono
from whateverfont.geom import contour_bounds
from whateverfont.presets import preset


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    fam = Family(name="Cell Test", base=preset("mono"),
                 axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 50}, 700: {"weight": 124}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    return fam, build_family(fam, tmp_path_factory.mktemp("mono"))


def test_a_mono_base_gets_the_coding_letters():
    fam = Family(name="Cells", base=preset("mono"))
    plain = latin()
    assert set(fam.recipes) == set(mono()) and set(plain) < set(mono())      # Latin, plus box drawings
    for name in ("i", "l", "I", "one", "zero"):
        assert fam.recipes[name].fn is not plain[name].fn, name
    assert Family(name="Text", base=preset("grotesk")).recipes["i"].fn is plain["i"].fn


def test_every_glyph_has_the_cell_width(built):
    fam, res = built
    assert res.warnings == []
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        widths = {}
        for name in font.getGlyphOrder():
            widths.setdefault(font["hmtx"][name][0], []).append(name)
        assert set(widths) == {0, 600}, {k: v[:5] for k, v in widths.items()}
        assert all("comb" in n for n in widths[0])
        assert font["post"].isFixedPitch == 1 and font["OS/2"].panose.bProportion == 9
        assert "kern" not in [f.FeatureTag for f in font["GPOS"].table.FeatureList.FeatureRecord]


@pytest.mark.parametrize("weight", [50, 78, 124])
def test_wide_letters_fit_and_narrow_letters_fill(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    for name in ("m", "w", "M", "W", "at", "ae", "AE", "OE", "percent"):
        b = contour_bounds(recipes.draw(name, p).contours)
        assert b[0] >= 20 and b[2] <= 580, (name, b)
    for name in ("i", "l", "I", "one", "r", "f", "t", "j"):
        b = contour_bounds(recipes.draw(name, p).contours)
        assert b[2] - b[0] >= 270, (name, b)       # at least 45% of the cell
    # a wide letter keeps its stems: it is drawn narrower, not squashed
    m, n = recipes.draw("m", p), recipes.draw("n", p)
    from whateverfont.probe import _runs
    stem_m = min(r[1] - r[0] for r in _runs(m, p.xh * 0.3))
    stem_n = min(r[1] - r[0] for r in _runs(n, p.xh * 0.3))
    assert stem_m > stem_n * 0.90            # the boldest m gives up a little


def test_a_row_of_underscores_is_one_line():
    b = contour_bounds(mono().draw("underscore", preset("mono")).contours)
    assert b[0] <= 0.5 and b[2] >= 599.5


def test_the_zero_is_not_a_capital_o():
    p = preset("mono")
    recipes = mono()
    assert len(recipes.draw("zero", p).contours) == 3          # outside, counter, and the dot in it
    assert len(recipes.draw("O", p).contours) == 2


def test_mono_masters_are_compatible(built):
    _, res = built
    font = TTFont(res.variable)
    assert "gvar" in font and len(font.getGlyphOrder()) == len(mono()) + 1
