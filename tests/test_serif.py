"""Slab serifs: strokes only when asked for, one cell for every glyph, and a variable font."""

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family, latin, mono
from whateverfont.compile import serif_mismatch
from whateverfont.geom import contour_area, contour_bounds
from whateverfont.presets import preset
from whateverfont.probe import _runs


def _strokes(recipes, name, p):
    rec = recipes[name]
    g = recipes._run(rec, p)
    return [s for s in g.strokes if s.tag in ("serif", "beak")]


def test_serifs_add_strokes_only_when_on():
    recipes = latin()
    plain, slab = Params(), Params(serif=40)
    for name in ("n", "m", "h", "u", "E", "T", "A", "v", "x", "one"):
        assert _strokes(recipes, name, plain) == [], name
        assert _strokes(recipes, name, slab), name
    # with serif 0 the outline is the same as it was before serifs existed: no hidden change
    for name in ("n", "E", "a", "seven"):
        a = recipes.draw(name, Params())
        b = recipes.draw(name, Params(serif=0.0, serif_weight=0.5))
        assert a.contours == b.contours and a.advance == b.advance, name


def test_a_slab_keeps_its_letter_inside_its_sidebearings():
    recipes = latin()
    p = Params(serif=44)
    for name in ("n", "H", "i", "l", "x"):
        g = recipes.draw(name, p)
        b = contour_bounds(g.contours)
        assert b[0] > 3 and g.advance - b[2] > 3, (name, b, g.advance)
        assert g.advance > recipes.draw(name, Params()).advance - 1, name   # never narrower


@pytest.mark.parametrize("weight", [56, 84, 118])
def test_slabs_fit_the_cell_and_facing_feet_do_not_touch(weight):
    p = preset("typewriter", weight=weight)
    recipes = mono()
    for name in ("m", "w", "M", "W", "n", "H", "r", "f", "i", "l", "I", "one", "x", "k", "N", "at"):
        b = contour_bounds(recipes.draw(name, p).contours)
        assert b[0] >= 20 and b[2] <= 580, (name, b)
    for name in ("i", "l", "r", "f", "t", "one", "I", "j"):
        b = contour_bounds(recipes.draw(name, p).contours)
        assert b[2] - b[0] >= 270, (name, b)          # narrow letters fill their cell
    # the three feet of the m stay apart, so it is not a black bar at the baseline
    m = recipes.draw("m", p)
    t = recipes._run(recipes["m"], p).serif_t
    assert len(_runs(m, t / 2)) >= 3


def test_mixing_serif_on_and_off_in_one_variable_font_is_refused(tmp_path):
    fam = Family(name="Half Slab", base=preset("mono"), recipes=mono().only("nH"),
                 axes=[Axis("SERF", "Serif", 0, 0, 60, {60: {"serif": 60}})])
    assert "serif" in serif_mismatch(fam)
    res = build_family(fam, tmp_path, woff2=False, jobs=1)
    assert res.variable is None and any("serif is 0 in some masters" in w for w in res.warnings)


@pytest.fixture(scope="module")
def typed(tmp_path_factory):
    fam = Family(name="Slab Test", base=preset("typewriter"),
                 axes=[Axis("wght", "Weight", 300, 400, 700,
                            {300: {"weight": 52, "serif": 60}, 700: {"weight": 112, "serif": 42}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    return fam, build_family(fam, tmp_path_factory.mktemp("slab"))


def test_a_variable_font_builds_with_the_slab_length_on_an_axis(typed):
    fam, res = typed
    assert serif_mismatch(fam) is None
    assert res.warnings == [] and res.variable is not None
    font = TTFont(res.variable)
    assert "gvar" in font and len(font.getGlyphOrder()) == len(mono()) + 1


def test_every_serif_glyph_has_the_cell_width(typed):
    _, res = typed
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        widths = {font["hmtx"][n][0] for n in font.getGlyphOrder() if "comb" not in n}
        assert widths == {600}, widths


def test_an_effect_keeps_the_slabs_in_the_cell():
    from whateverfont import effects
    p = preset("typewriter")
    plain = mono().only("nmrH")
    rough = effects.rough(plain, amount=2)
    for name in ("n", "m", "r", "H"):
        a = contour_bounds(plain.draw(name, p).contours)
        b = contour_bounds(rough.draw(name, p).contours)
        assert abs((a[0] + a[2]) / 2 - (b[0] + b[2]) / 2) < 6, name      # still centered
        assert sum(-contour_area(c) for c in rough.draw(name, p).contours) > 0
