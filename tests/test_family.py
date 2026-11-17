import pytest

from whateverfont import Axis, Family, Params, latin
from whateverfont.geom import contour_area
from whateverfont.presets import PRESETS, preset


def family():
    return Family(
        name="Test Family",
        base=Params(flare=0.3, contrast=0.6),
        axes=[
            Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 50}, 800: {"weight": 150}}),
            Axis("wdth", "Width", 75, 100, 100, {75: {"width": 0.75}}),
            Axis("FLAR", "Flare", 0, 30, 100, {0: {"flare": 0.0}, 100: {"flare": 0.8}}),
            Axis("slnt", "Slant", -12, 0, 0, {-12: {"slant": 12}}),
        ],
        styles={"Regular": {}, "Bold": {"wght": 700}},
    )


def test_default_location_is_the_base_style():
    fam = family()
    assert fam.params_at() == fam.base


def test_axis_values_interpolate_between_poles():
    fam = family()
    assert fam.params_at({"wght": 800}).weight == 150
    assert fam.params_at({"wght": 600}).weight == pytest.approx(82 + (150 - 82) * 0.5)
    assert fam.params_at({"wght": 350}).weight == pytest.approx(82 - (82 - 50) * 0.5)


def test_axis_effects_add_up():
    p = family().params_at({"wght": 800, "wdth": 75, "slnt": -12})
    assert (p.weight, p.width, p.slant) == (150, 0.75, 12)


def test_unknown_axis_is_an_error():
    with pytest.raises(KeyError):
        family().params_at({"opsz": 12})


def test_masters_are_default_plus_axis_extremes():
    assert len(family().masters()) == 1 + 2 + 1 + 2 + 1


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_recipe_draws_in_every_preset(name):
    recipes = latin()
    for weight in (44, 150):
        p = preset(name, weight=weight)
        for glyph_name in recipes:
            g = recipes.draw(glyph_name, p)
            # combining marks have no advance: the mark feature places them on the letter before
            assert g.advance > 0 or "comb" in glyph_name, glyph_name
            if glyph_name not in ("space", "nbspace"):
                assert sum(-contour_area(c) for c in g.contours) > 0, glyph_name


def test_masters_share_one_point_structure():
    fam = family()
    drawn = [fam.draw(loc, keep_structure=True) for loc in fam.masters()]
    for name in fam.recipes:
        shapes = [[[len(seg) for seg in c] for c in d[name].contours] for d in drawn]
        assert all(s == shapes[0] for s in shapes), name


def test_a_pole_at_the_default_is_rejected():
    with pytest.raises(ValueError, match="base"):
        Axis("wght", "Weight", 300, 400, 800, {400: {"weight": 82}, 800: {"weight": 150}})


def test_axis_tag_and_range_are_checked():
    with pytest.raises(ValueError):
        Axis("weight", "Weight", 300, 400, 800)
    with pytest.raises(ValueError):
        Axis("wght", "Weight", 500, 400, 800)


def test_kana_paths_parse_and_draw(tmp_path):
    from whateverfont import kana
    segs = kana.parse_path("M10,20c5,0,10,5,10,10s5,10,10,10L50,60")
    assert [s[3] for s in segs] == [20 + 30j, 30 + 40j, 50 + 60j]
    assert segs[1][1] == 20 + 35j                       # the smooth curve mirrors the last handle
    (tmp_path / "03042.svg").write_text('<svg><path id="s1" d="M20,30c10,-5,30,-5,60,0"/>'
                                        '<path id="s2" d="M50,15c0,20,-2,50,-10,70"/></svg>')
    recipes = kana.recipes(tmp_path)
    glyph = recipes.draw("uni3042", Params(roundness=1.0))
    assert glyph.unicode == 0x3042 and glyph.advance == 1000 and len(glyph.contours) >= 1


def _ink(glyph) -> float:
    return sum(-contour_area(c) for c in glyph.contours)


def test_accented_letters_follow_a_redrawn_base_letter():
    plain, redrawn = latin(), latin()

    @redrawn.add("e", "e")
    def e(g):                                   # a ring with a bar: much more ink than the built-in e
        g.ring(g.rw / 2, g.bot, g.cw + g.sw, g.top(g.xh))
        g.bar(g.rw / 2, g.cw + g.sw, g.xh / 2)
        g.bar(g.rw / 2, g.cw + g.sw, g.xh / 4)
        g.frame(g.cw + g.sw + g.rw / 2, "r", "r")

    p = Params()
    extra = _ink(redrawn.draw("e", p)) - _ink(plain.draw("e", p))
    assert extra > 2000
    for name in ("eacute", "ecircumflex", "ecaron", "eogonek", "oe", "ae"):
        gained = _ink(redrawn.draw(name, p)) - _ink(plain.draw(name, p))
        assert gained == pytest.approx(extra, rel=0.25), name
    # letters that do not contain an e are untouched
    assert _ink(redrawn.draw("aacute", p)) == _ink(plain.draw("aacute", p))


def test_ae_keeps_a_two_story_a():
    recipes = latin()
    one, two = Params(a_story=1), Params(a_story=2)
    assert recipes.draw("ae", one).advance == recipes.draw("ae", two).advance
    assert recipes.draw("a", one).advance != recipes.draw("a", two).advance
    assert recipes.draw("ae", one).advance != recipes.draw("oe", one).advance


def test_a_heavy_narrow_AE_keeps_the_white_between_its_diagonal_and_its_stem():
    from whateverfont.probe import _runs
    p = preset("condensed", weight=150, width=0.6)
    g = latin().draw("AE", p)
    runs = _runs(g, p.cap * 0.12)                # below the bar of the A: the diagonal, then the stem
    assert len(runs) >= 2 and runs[1][0] - runs[0][1] > 12


def test_line_height_can_be_set_on_the_family(tmp_path):
    from fontTools.ttLib import TTFont
    from whateverfont import build_family
    from whateverfont.probe import probe
    recipes = latin()

    @recipes.add("A", "A", case="upper")
    def tall(g):
        g.stem(g.L, -300, 1150)
        g.frame(g.sw)

    fam = Family(name="Tall", recipes=recipes)
    assert any("A: reaches" in p and "ascent=" in p for p in probe(fam, chars="A")["problems"])
    fam = Family(name="Tall", recipes=recipes, ascent=1200, descent=-340)
    assert not any("A: reaches" in p for p in probe(fam, chars="A")["problems"])
    font = TTFont(build_family(fam, tmp_path, variable=False, woff2=False).statics["Regular"])
    assert (font["hhea"].ascent, font["hhea"].descent) == (1200, -340)
    assert (font["OS/2"].sTypoAscender, font["OS/2"].sTypoDescender) == (1200, -340)


def test_frame_after_fixed_advance_makes_a_figure_proportional():
    recipes = latin()
    p = Params()
    tabular = recipes.draw("one", p).advance

    @recipes.add("one", "1", case="figure")
    def one(g):
        latin()["one"].fn(g)
        g.frame(None, 0.5, 0.5)

    assert recipes.draw("one", p).advance < tabular - 40


def test_a_failing_effect_says_where(tmp_path):
    from whateverfont import build_family, effects

    def broken(g, ink):
        return ink[0][0][0][1]                     # a point is not a list

    fam = Family(name="Broken", recipes=effects.wrapped(latin().only("A"), broken))
    res = build_family(fam, tmp_path, variable=False, woff2=False, jobs=1)
    assert len(res.warnings) == 1
    assert "glyph 'A' failed" in res.warnings[0] and "test_family.py, line" in res.warnings[0]


def _widths(params):
    recipes = latin()
    return {name: recipes.draw(name, params).advance
            for name in ("n", "o", "s", "a", "f", "t", "r", "H", "O", "zero", "space")}


def test_the_width_numbers_change_only_their_own_letters():
    """round_width, cap_width, arm and word_space are 1 by default; each one moves its letters and no others."""
    base = _widths(Params())
    assert _widths(Params(round_width=1.0, cap_width=1.0, arm=1.0, word_space=1.0)) == base
    wide = _widths(Params(round_width=1.2))
    assert wide["n"] == base["n"] and wide["H"] == base["H"] and wide["f"] == base["f"]
    assert all(wide[g] > base[g] for g in ("o", "s", "a", "zero"))
    caps = _widths(Params(cap_width=1.15))
    assert caps["n"] == base["n"] and caps["o"] == base["o"]
    assert caps["H"] > base["H"] and caps["O"] > base["O"]
    arms = _widths(Params(arm=1.2))
    assert arms["n"] == base["n"] and arms["o"] == base["o"]
    assert all(arms[g] > base[g] for g in ("f", "t", "r"))
    words = _widths(Params(word_space=1.25))
    assert words["space"] > base["space"] and {k: v for k, v in words.items() if k != "space"} == \
        {k: v for k, v in base.items() if k != "space"}


def test_the_width_numbers_can_sit_on_an_axis():
    fam = Family(name="W", base=Params(), axes=[Axis("wght", "Weight", 400, 400, 700, {700: {"weight": 128, "arm": 1.2}})])
    assert fam.params_at({"wght": 700}).arm == pytest.approx(1.2)
    assert fam.params_at({"wght": 550}).arm == pytest.approx(1.1)


def _right_edge(glyph):
    """How tall the upright edge at the far right of a glyph is."""
    from whateverfont.geom import flatten_contour
    pts = [p for c in glyph.contours for p in flatten_contour(c, 1.0)]
    far = max(p.real for p in pts)
    ys = [p.imag for p in pts if p.real > far - 1.5]
    return max(ys) - min(ys)


def test_a_flat_cut_ends_the_arm_of_r_upright():
    """cut="flat" ends the arm of r (and the hooks of f, t, j) on an upright line, not in a wedge."""
    recipes = latin()
    flat, level = Params(cut="flat", weight=128), Params(cut="horizontal", weight=128)
    assert _right_edge(recipes.draw("r", flat)) > 60          # an upright end about as tall as the stroke is thick
    assert _right_edge(recipes.draw("r", level)) < 20         # the level cut ends in a point
    for name in ("c", "e", "s", "o", "n"):                    # the other letters are the same in both
        assert recipes.draw(name, flat).advance == recipes.draw(name, level).advance
