"""A complete font: the signs, letters, arrows and shapes people type, and the figure and case features."""

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family, effects, latin, mono
from whateverfont.geom import contour_bounds
from whateverfont.presets import preset

#: The characters this work added, by group.
ADDED = {
    "letters": "ĲĳĸĿŀŊŋŦŧſƒⁱΩΩπ",
    "punctuation": "‐‑‒―‛‟",
    "superscripts and subscripts": "⁰⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉",
    "fractions": "⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞",
    "currency": "₠₡₢₣₤₥₦₧₨₩₪₭₮₯₱₲₳₴₵₸₹₺₼₽₾₿⃀",
    "signs": "№℮◊",
    "math": "∂∆∏∑√∞∫≈≠≤≥",
    "arrows": "←↑→↓↔↕↖↗↘↙",
    "shapes": "✓✗★☆♥●○■□▲▼◆",
    "pinyin": "ǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜ",
    "more languages": "əƏʻʼṣṢṅṄɓɗƙƁƊƘ",
}
CHARS = "".join(ADDED.values())
FIGS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


def _cps():
    # the Ohm sign is folded into Omega by Unicode normalization, so name it by its code point
    return {ord(c) for c in CHARS} | {0x2126}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    fam = Family(name="Complete Test", base=Params(flare=0.3, contrast=0.6),
                 axes=[Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 44}, 800: {"weight": 150}})],
                 styles={"Regular": {}, "Bold": {"wght": 800}})
    return fam, build_family(fam, tmp_path_factory.mktemp("complete"))


@pytest.fixture(scope="module")
def mono_built(tmp_path_factory):
    fam = Family(name="Complete Mono", base=preset("mono"),
                 axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 50}, 700: {"weight": 124}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    return fam, build_family(fam, tmp_path_factory.mktemp("complete-mono"))


def _shaper(path):
    import uharfbuzz as hb
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def run(text, features=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features or {})
        return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos], [p.x_advance for p in buf.glyph_positions]
    return run


def test_every_added_character_is_in_the_latin_and_the_mono_set():
    for recipes in (latin(), mono()):
        covered = {r.unicode for r in recipes.values() if r.unicode}
        missing = sorted(hex(c) for c in _cps() - covered)
        assert not missing, missing
    # Latin and the signs; Greek and Cyrillic come on top (tests/test_scripts.py)
    assert len({r.unicode for r in latin(greek=False, cyrillic=False).values() if r.unicode}) == 605


def test_a_family_with_a_weight_axis_builds_with_no_warnings(built):
    fam, res = built
    assert res.warnings == []
    assert res.variable is not None and set(res.statics) == {"Regular", "Bold"}
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        missing = sorted(hex(c) for c in _cps() - set(font.getBestCmap()))
        assert not missing, (path.name, missing)
        tags = {r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord}
        assert {"frac", "numr", "dnom", "sups", "subs", "sinf", "ordn", "zero", "case", "pnum"} <= tags, path.name
        assert "tnum" not in tags                   # the default figures are tabular already


def test_a_roundness_axis_keeps_every_added_glyph_in_the_variable_font(tmp_path):
    """Gantry's ROND axis runs from sharp corners to round ones: a filled star or square must have the
    same points at both ends."""
    fam = Family(name="Round Test", base=preset("technical", roundness=0.25),
                 axes=[Axis("ROND", "Roundness", 0, 25, 100, {0: {"roundness": 0.0}, 100: {"roundness": 1.0}})],
                 styles={"Regular": {}})
    res = build_family(fam, tmp_path)
    assert res.warnings == []
    missing = sorted(hex(c) for c in _cps() - set(TTFont(res.variable).getBestCmap()))
    assert not missing, missing


def test_a_monoline_weight_axis_keeps_every_added_glyph_in_the_variable_font(tmp_path):
    """In a monoline family (Neon) the horizontal and the vertical stroke are equally thick in light
    masters and not in heavy ones. A stroke whose width changes from node to node must still have the
    same segments in every master."""
    tube = dict(contrast=1.0, round_weight=1.0, join=1.0, cap_weight=1.0, flare=0.0, roundness=1.0)
    fam = Family(name="Tube Test", base=preset("geometric", **tube, weight=62),
                 axes=[Axis("wght", "Weight", 200, 400, 700, {200: {"weight": 34}, 700: {"weight": 118}})],
                 styles={"Regular": {}})
    res = build_family(fam, tmp_path)
    assert res.warnings == []
    missing = sorted(hex(c) for c in _cps() - set(TTFont(res.variable).getBestCmap()))
    assert not missing, missing


def test_frac_makes_a_fraction_from_figures_and_a_slash(built):
    _, res = built
    run = _shaper(res.statics["Regular"])
    names, _ = run("1/2 23/45 a/b", {"frac": True})
    assert names == ["onesuperior", "fraction", "two.dnom", "space", "twosuperior", "threesuperior", "fraction",
                     "four.dnom", "five.dnom", "space", "a", "slash", "b"]
    # without the feature nothing changes
    assert run("1/2")[0] == ["one", "slash", "two"]
    # the fraction slash moves closer to both, so 1/2 is about as wide as ½
    frac = sum(run("1/2", {"frac": True})[1])
    half = sum(run("½")[1])
    assert abs(frac - half) < 0.25 * half


@pytest.mark.parametrize("feature, text, want", [
    ("sups", "x2", ["x", "twosuperior"]),
    ("subs", "H2O", ["H", "twoinferior", "O"]),
    ("sinf", "C6", ["C", "sixinferior"]),
    ("numr", "37", ["threesuperior", "sevensuperior"]),
    ("dnom", "37", ["three.dnom", "seven.dnom"]),
    ("ordn", "1a 2o", ["one", "ordfeminine", "space", "two", "ordmasculine"]),
    ("ordn", "No.", ["numero"]),
    ("zero", "10", ["one", "zero.zero"]),
    ("case", "(H-E)", ["parenleft.case", "H", "hyphen.case", "E", "parenright.case"]),
    ("case", "«¡A!»", ["guillemotleft.case", "exclamdown.case", "A", "exclam", "guillemotright.case"]),
    ("pnum", "101", ["one.pnum", "zero.pnum", "one.pnum"]),
])
def test_each_feature_changes_the_shaped_glyphs(built, feature, text, want):
    _, res = built
    for path in (res.statics["Regular"], res.variable):
        names, _ = _shaper(path)(text, {feature: True})
        assert names == want, (path.name, feature, names)


def test_proportional_figures_are_narrower_and_tabular_ones_line_up(built):
    _, res = built
    run = _shaper(res.statics["Regular"])
    tab = run("0123456789")[1]
    pro = run("0123456789", {"pnum": True})[1]
    assert len(set(tab)) == 1                        # tabular: one advance
    assert len(set(pro)) > 5 and pro[1] < tab[1]     # the 1 is the narrowest
    small = run("0123456789", {"sups": True})[1] + run("0123456789", {"subs": True})[1] + \
        run("0123456789", {"dnom": True})[1]
    assert len(set(small)) == 1                      # the small figures are tabular too


def _bounds(font, name):
    glyf = font["glyf"]
    g = glyf[name]
    g.recalcBounds(glyf)
    return g.xMin, g.yMin, g.xMax, g.yMax


def test_small_figures_and_fractions_line_up(built):
    """Superscripts share one top and one baseline, so do denominators and subscripts, and the parts of a
    vulgar fraction stand where the numerator and the denominator glyphs stand."""
    _, res = built
    for path in res.statics.values():
        font = TTFont(path)
        cap = font["OS/2"].sCapHeight
        sups = [_bounds(font, n) for n in ("zerosuperior", "onesuperior", "foursuperior", "sevensuperior")]
        dnom = [_bounds(font, f"{n}.dnom") for n in ("zero", "one", "four", "seven")]
        infs = [_bounds(font, n) for n in ("zeroinferior", "oneinferior", "fourinferior", "seveninferior")]
        flat = lambda bs, i: max(b[i] for b in bs) - min(b[i] for b in bs)
        # the flat tops of 1 4 7 and the round top of 0 differ by the overshoot only
        assert flat(sups, 3) < 12 and flat(dnom, 3) < 12 and flat(infs, 3) < 12, path.name
        assert flat(sups[1:], 1) < 3 and flat(dnom[1:], 1) < 3, path.name           # flat feet on one line
        assert abs(max(b[3] for b in sups) - cap) < 15, path.name                     # numerators reach the caps
        assert abs(min(b[1] for b in dnom[1:])) < 3, path.name                        # denominators stand on the baseline
        assert max(b[1] for b in infs) < -0.1 * cap, path.name                        # subscripts hang below it
        # ⅜: its numerator reaches as high as ³, its denominator stands as low as 8.dnom
        cmap = font.getBestCmap()
        frac = _bounds(font, cmap[0x215C])
        assert abs(frac[3] - _bounds(font, "threesuperior")[3]) < 3, path.name
        assert abs(frac[1] - _bounds(font, "eight.dnom")[1]) < 3, path.name


def test_case_forms_center_on_the_capitals(built):
    _, res = built
    font = TTFont(res.statics["Regular"])
    cap = font["OS/2"].sCapHeight
    for name in ("hyphen", "endash", "parenleft", "guillemotleft", "periodcentered"):
        b = _bounds(font, f"{name}.case")
        assert abs((b[1] + b[3]) / 2 - cap / 2) < cap * 0.03, name
        assert font["hmtx"][f"{name}.case"][0] == font["hmtx"][name][0], name
    b = _bounds(font, "exclamdown.case")
    assert b[1] > -15 and abs(b[3] - _bounds(font, "exclam")[3]) < 15


def test_a_family_can_make_its_default_figures_proportional(tmp_path):
    fam = Family(name="Text Figures", base=Params(), figures="proportional")
    assert fam.recipes["zero.tnum"].unicode is None and fam.recipes["zero"].unicode == ord("0")
    assert "zero.pnum" not in fam.recipes
    res = build_family(fam, tmp_path, variable=False)
    assert res.warnings == []
    path = res.statics["Regular"]
    run = _shaper(path)
    assert len(set(run("0123456789")[1])) > 5
    names, adv = run("101", {"tnum": True})
    assert names == ["one.tnum", "zero.tnum", "one.tnum"] and len(set(adv)) == 1
    tags = {r.FeatureTag for r in TTFont(path)["GSUB"].table.FeatureList.FeatureRecord}
    assert "tnum" in tags and "pnum" not in tags
    with pytest.raises(ValueError):
        Family(name="Bad", figures="oldstyle")


def test_the_monospaced_set_keeps_one_width(mono_built):
    fam, res = mono_built
    assert res.warnings == []
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        widths = {font["hmtx"][n][0] for n in font.getGlyphOrder()} - {0}       # combining marks have no width
        assert widths == {600}, (path.name, widths)
        tags = {r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord}
        assert "pnum" not in tags and {"frac", "case", "zero"} <= tags
    # a form is fitted to the cell like the glyph it stands for: the em dash still runs edge to edge
    font = TTFont(res.statics["Regular"])
    for name, form in (("hyphen", "hyphen.case"), ("emdash", "emdash.case"), ("parenleft", "parenleft.case"),
                       ("twosuperior", "two.dnom")):
        a, b = _bounds(font, name), _bounds(font, form)
        assert abs((b[2] - b[0]) - (a[2] - a[0])) < 0.05 * (a[2] - a[0]), (name, a, b)
    # frac keeps the cell: no glyph moves or changes its advance
    names, adv = _shaper(res.statics["Regular"])("1/2", {"frac": True})
    assert names == ["onesuperior", "fraction", "two.dnom"] and adv == [600, 600, 600]


@pytest.mark.parametrize("weight", [56, 126])
def test_every_added_glyph_keeps_the_cell_and_the_drawing_inside_it(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    by_uni = {r.unicode: n for n, r in recipes.items() if r.unicode}
    for cp in sorted(_cps()):
        g = recipes.draw(by_uni[cp], p)
        b = contour_bounds(g.contours)
        assert g.advance == 600, (hex(cp), g.advance)
        assert b[0] >= -1 and b[2] <= 601, (hex(cp), b)


STYLES = {
    "light": Params(weight=40, contrast=0.6, flare=0.3),
    "heavy": preset("technical", weight=150),
    "condensed bold": preset("flare", width=0.56, weight=132, cap=715, asc=752),
    "typewriter": preset("typewriter", weight=112),
    "rounded heavy": preset("rounded", weight=132, xh=540, desc=-150),
    "broadnib": preset("broadnib"),
}


@pytest.mark.parametrize("style", list(STYLES))
def test_every_added_glyph_draws_in_every_style(style):
    """No glyph fails, none is empty, and none reaches far outside the line (a stray point)."""
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    from whateverfont import outline
    for name in list(recipes)[465:]:
        del outline.trouble[:]
        g = recipes.draw(name, p)
        b = contour_bounds(g.contours)
        assert b, (style, name)
        assert -400 < b[1] and b[3] < p.line_top + 40 and b[2] - b[0] < 1400, (style, name, b)
        assert not outline.trouble, (style, name, outline.trouble)
        if name.startswith("Udieresis") and name != "Udieresis":
            # Ǘ: the stack gets smaller, and in a heavy weight the tone mark comes down between the dots,
            # so that it stays under the top of the line as the Vietnamese capitals do
            assert b[3] <= p.line_top, (style, name, b[3], p.line_top)


def test_features_are_harmless_with_an_effect_and_a_small_set(tmp_path):
    """An effect family gets the forms and the features too; a small set gets only what its glyphs allow."""
    fam = Family(name="Fx Test", base=preset("grotesk", weight=150), recipes=effects.inline(latin(), width=0.17))
    res = build_family(fam, tmp_path / "fx")
    assert res.warnings == []
    names, _ = _shaper(res.statics["Regular"])("1/2 (A)", {"frac": True, "case": True})
    assert names == ["onesuperior", "fraction", "two.dnom", "space", "parenleft.case", "A", "parenright.case"]
    small = Family(name="Small Test", base=Params(), recipes=latin().only())
    res = build_family(small, tmp_path / "small")
    assert res.warnings == []
    tags = {r.FeatureTag for r in TTFont(res.statics["Regular"])["GSUB"].table.FeatureList.FeatureRecord} \
        if "GSUB" in TTFont(res.statics["Regular"]) else set()
    assert not tags & {"frac", "sups", "case", "pnum"}
