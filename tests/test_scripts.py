"""Greek and Cyrillic: every letter in the set and in the font, the Latin letters unchanged, shared letters
drawn by their Latin recipes, and outlines that interpolate."""

import unicodedata

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family, latin, mono, outline, spacing
from whateverfont.geom import contour_area, contour_bounds
from whateverfont.outline import dilate, intersection, union
from whateverfont.presets import preset
from whateverfont.recipes.cyrillic import ALPHABET as CYRILLIC, CYRILLIC as CYRILLIC_SET
from whateverfont.recipes.greek import ALPHABET as GREEK, GREEK as GREEK_SET
from whateverfont.stroke import expand

#: What a font must cover: Cyrillic U+0400 to U+045F with Ґ ґ, and the letters of Kazakh, Uzbek, Tatar,
#: Tajik and Kyrgyz; modern Greek with the tonos, the dialytika, the question mark and the ano teleia.
CYRILLIC_WANTED = ({*range(0x0400, 0x0460), 0x0490, 0x0491}
                   | {ord(c) for c in "ӘәҒғҚқҢңӨөҰұҮүҺһҖҗҲҳҶҷӢӣӮӯ"})
GREEK_WANTED = ({*range(0x0391, 0x03AA)} - {0x03A2}) | {*range(0x03B1, 0x03CA)} | {
    ord(c) for c in "ΆΈΉΊΌΎΏάέήίόύώϊϋΐΰΪΫ΄΅"} | {0x037E, 0x0387}

#: Letters that have the shape of another one and must be drawn by its recipe: (new, twin).
TWINS = list(zip("АВЕКМНОРСТХЅІЈҮаеорсухѕіјһЁёЀѐЇїкћӘә", "ABEKMHOPCTXSIJYaeopcyxsijhËëÈèÏïĸħƏə")) + \
    list(zip("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧομκΪΫ\u037eΓΠΦφ", "ABEZHIKMNOPTYXoµĸÏŸ;ГПФф"))

#: Sans, flare serif, slab serif, rounded, heavy, light, condensed, slanted and monospaced styles.
STYLES = {
    "sans": Params(),
    "flare serif": preset("flare", flare=0.34, flare_len=230, contrast=0.60, xh=492, counter=282, aperture=0.82),
    "slab serif": preset("typewriter", mono=0, weight=100),
    "rounded heavy": preset("rounded", weight=132, xh=540, desc=-150),
    "light": Params(weight=40, contrast=0.6, flare=0.3),
    "heavy": preset("technical", weight=150),
    "condensed bold": preset("flare", width=0.56, weight=132, cap=715, asc=752),
    "broadnib slanted": preset("broadnib", slant=11),
    "typewriter": preset("typewriter", weight=112),
    "mono bold": preset("mono", weight=126, xh=542),
}


def _by_char(recipes):
    return {chr(r.unicode): n for n, r in recipes.items() if r.unicode}


def _codes(recipes) -> set:
    return {r.unicode for r in recipes.values() if r.unicode}


def test_every_letter_is_in_the_latin_and_the_mono_set():
    for recipes in (latin(), mono()):
        missing = sorted(hex(c) for c in (CYRILLIC_WANTED | GREEK_WANTED) - _codes(recipes))
        assert not missing, missing
    assert len(_codes(latin())) == 800 and len(_codes(mono())) == 960


def test_the_scripts_can_be_left_out_or_kept_in_a_small_set():
    plain = latin(greek=False, cyrillic=False)
    assert len(_codes(plain)) == 605 and len(_codes(mono(greek=False, cyrillic=False))) == 765
    assert not _codes(plain) & (CYRILLIC_WANTED | GREEK_WANTED - {0x03A9, 0x03C0})
    assert CYRILLIC_WANTED <= _codes(latin(greek=False)) and not GREEK_WANTED - {0x03A9} <= _codes(latin(greek=False))
    assert GREEK_WANTED <= _codes(latin(cyrillic=False)) and not CYRILLIC_WANTED & _codes(latin(cyrillic=False))
    small = latin().only(greek=True, cyrillic=True)
    assert (CYRILLIC_WANTED | GREEK_WANTED) <= _codes(small)
    assert not _codes(latin().only()) & CYRILLIC_WANTED
    assert {ord(c) for c in CYRILLIC} == _codes(CYRILLIC_SET) and {ord(c) for c in GREEK} >= _codes(GREEK_SET)


def test_the_latin_glyphs_keep_their_names_order_outlines_and_advances():
    """The new alphabets come after everything else; nothing that was there before changes."""
    for fn, p in ((latin, STYLES["flare serif"]), (latin, STYLES["slab serif"]), (mono, STYLES["typewriter"])):
        full, plain = fn(), fn(greek=False, cyrillic=False)
        assert list(full)[:len(plain)] == list(plain)
        for name in plain:
            a, b = plain.draw(name, p), full.draw(name, p)
            assert (a.advance, a.unicode, a.contours) == (b.advance, b.unicode, b.contours), name


@pytest.mark.parametrize("style", ["sans", "flare serif", "slab serif", "rounded heavy", "typewriter"])
def test_shared_letters_are_drawn_by_their_twins(style):
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    names = _by_char(recipes)
    for new, twin in TWINS:
        a, b = recipes.draw(names[new], p), recipes.draw(names[twin], p)
        assert a.contours == b.contours and a.advance == b.advance, (style, new, twin)


def test_a_redrawn_latin_letter_is_redrawn_in_greek_and_cyrillic_too():
    recipes = latin()

    @recipes.add("A", "A", case="upper")
    def wide_a(g):
        g.stem(g.L, 0, g.cap)
        g.frame(g.sw * 3)
    p = Params()
    for ch in "АΑ":
        assert recipes.draw(_by_char(recipes)[ch], p).advance == recipes.draw("A", p).advance


@pytest.mark.parametrize("style", list(STYLES))
def test_every_new_glyph_draws_in_every_style(style):
    """No glyph fails or is empty, none has a defect the engine could not repair, and none reaches out of
    the line."""
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    for name in list(CYRILLIC_SET) + list(GREEK_SET):
        del outline.trouble[:]
        g = recipes.draw(name, p)
        b = contour_bounds(g.contours)
        assert b and g.advance > 0, (style, name)
        # as for the Latin letters: a mark over a tall capital (Ё is Ë) may pass the top of the line a little
        assert p.line_bottom < b[1] and b[3] < p.line_top + 40 and b[2] - b[0] < 1200, (style, name, b)
        assert not outline.trouble, (style, name, outline.trouble)
        if p.mono:
            assert g.advance == p.mono and -1 <= b[0] and b[2] <= p.mono + 1, (style, name, b)


def _holes(contours) -> int:
    return sum(1 for c in contours if contour_area(c) > 0)


@pytest.mark.parametrize("style", ["sans", "flare serif", "rounded heavy", "light", "typewriter"])
def test_counters_stay_open(style):
    """The loop of γ, the bowls of Ь Ы Ю Б Я β θ, the counters of Д Ф ф and the eye of δ stay open."""
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    names = _by_char(recipes)
    want = {"γ": 1, "Ь": 1, "Ы": 1, "Ю": 1, "Б": 1, "Я": 1, "β": 2, "θ": 2, "Д": 1, "Ф": 2, "ф": 2, "δ": 1,
            "Θ": 1, "Ψ": 0, "ю": 1, "ж": 0, "ш": 0}
    for ch, n in want.items():
        g = recipes.draw(names[ch], p)
        assert _holes(g.contours) == n, (style, ch, _holes(g.contours))


@pytest.mark.parametrize("style", ["sans", "flare serif", "heavy", "condensed bold", "mono bold"])
def test_the_tonos_stands_clear_of_the_capital(style):
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    names = _by_char(recipes)
    gap = p.cap * 0.02
    for ch in "ΆΈΉΊΌΎΏ":
        g = recipes._run(recipes[names[ch]], p)
        mark = union([c for s in g.strokes if s.tag == "mark" for c in expand(s, g.pen, p.roundness)])
        letter = union([c for s in g.strokes if s.tag != "mark" for c in expand(s, g.pen, p.roundness)])
        assert mark, (style, ch)
        near = intersection(dilate(mark, gap / 2), dilate(letter, gap / 2))
        assert not any(abs(contour_area(c)) > 0.5 for c in near), (style, ch)
        assert contour_bounds(mark)[0] < contour_bounds(letter)[0] + p.cap * 0.25, (style, ch)   # in front of it


def test_descenders_hang_below_the_baseline_and_above_the_descender():
    p = Params()
    recipes = latin()
    names = _by_char(recipes)
    for ch in "ДЦЩЏҚҢдцщџқңрфуηρφχψβζξς":
        b = contour_bounds(recipes.draw(names[ch], p).contours)
        assert p.desc - p.overshoot - 1 <= b[1] < -p.xh * 0.12, (ch, b)
    for ch in "ЛлПпШшИиЖжЭэЮюЯяαδεθιλνοστυω":
        assert contour_bounds(recipes.draw(names[ch], p).contours)[1] > -p.overshoot - 1, ch


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    fam = Family(name="Script Test", base=Params(flare=0.3, contrast=0.6),
                 axes=[Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 44}, 800: {"weight": 150}}),
                       Axis("wdth", "Width", 75, 100, 100, {75: {"width": 0.75}})],
                 styles={"Regular": {}, "Bold": {"wght": 800}})
    return fam, build_family(fam, tmp_path_factory.mktemp("scripts"))


def test_a_family_with_axes_builds_every_letter_into_every_font(built):
    """The variable font keeps every new glyph: their outlines interpolate across both axes."""
    _, res = built
    assert res.warnings == []
    assert res.variable is not None and set(res.statics) == {"Regular", "Bold"}
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        missing = sorted(hex(c) for c in (CYRILLIC_WANTED | GREEK_WANTED) - set(font.getBestCmap()))
        assert not missing, (path.name, missing)
        scripts = {s.ScriptTag for s in font["GPOS"].table.ScriptList.ScriptRecord}
        assert {"DFLT", "latn", "cyrl", "grek"} <= scripts, path.name


def test_the_variable_font_draws_each_master_of_the_new_letters(built):
    from fontTools.varLib.instancer import instantiateVariableFont
    fam, res = built
    vf = TTFont(res.variable)
    for loc in ({"wght": 300, "wdth": 75}, {"wght": 800, "wdth": 100}):
        inst = instantiateVariableFont(TTFont(res.variable), loc)
        glyf = inst["glyf"]
        for ch in "ЖДЛγζΨ":
            name = inst.getBestCmap()[ord(ch)]
            g = glyf[name]
            g.recalcBounds(glyf)
            assert g.numberOfContours > 0 and g.xMax - g.xMin > 50, (loc, ch)
    assert vf["fvar"].axes


def _shaper(path):
    import uharfbuzz as hb
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def run(text, features=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features or {})
        return ([font.glyph_to_string(i.codepoint) for i in buf.glyph_infos],
                [(q.x_offset, q.y_offset, q.x_advance) for q in buf.glyph_positions])
    return run


def test_decomposed_text_uses_the_composed_letters_and_the_stress_mark_attaches(built):
    _, res = built
    run = _shaper(res.statics["Regular"])
    names, _ = run(unicodedata.normalize("NFD", "йёάΐ"))
    assert names == ["uni0439", "uni0451", "alphatonos", "iotadieresistonos"]
    # a stressed Cyrillic vowel: the combining acute sits over the letter, not after it
    names, pos = run("ы́")
    assert names == ["uni044B", "acutecomb"]
    letter_advance = pos[0][2]
    assert pos[1][2] == 0 and 0.2 * letter_advance < -pos[1][0] < 0.9 * letter_advance
    # a stressed Ukrainian і loses its dot, as í does
    assert run("і́")[0] == ["dotlessi", "acutecomb"]


def test_cyrillic_and_greek_are_kerned_and_the_latin_pairs_stay(built):
    fam, res = built
    p = fam.params_at({})
    glyphs = fam.draw({})
    kerns = spacing.kerning(glyphs, p)
    names = _by_char(fam.recipes)
    k = lambda a, b: kerns.get((names[a], names[b]), 0.0)
    assert k("Г", "а") < -10 and k("Т", "о") < -10 and k("У", "а") < -10 and k("Γ", "α") < -10
    assert (names["А"], names["A"]) not in kerns                 # no pairs across scripts
    before = latin(greek=False, cyrillic=False)
    plain = {n: g for n, g in glyphs.items() if n in before}
    old = spacing.kerning(plain, p)
    assert {pair: v for pair, v in kerns.items() if pair in old} == old
    assert set(old) <= set(kerns)


def test_the_monospaced_font_keeps_one_width(tmp_path):
    fam = Family(name="Script Mono", base=preset("mono"), styles={"Regular": {}})
    res = build_family(fam, tmp_path, variable=False)
    assert res.warnings == []
    font = TTFont(res.statics["Regular"])
    widths = {font["hmtx"][n][0] for n in font.getGlyphOrder()} - {0}
    assert widths == {600}
    assert (CYRILLIC_WANTED | GREEK_WANTED) <= set(font.getBestCmap())
