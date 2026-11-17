"""Vietnamese: every letter in the set and in the font, marks that keep apart, and nothing clipped."""

import unicodedata

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family, latin, mono
from whateverfont.geom import contour_area, contour_bounds
from whateverfont.outline import dilate, intersection, union
from whateverfont.presets import preset
from whateverfont.recipes.vietnamese import ALPHABET, LETTERS
from whateverfont.stroke import expand

#: The vowels with a circumflex or a breve and a tone mark: the letters that stack two marks above.
STACKED = [c for c in LETTERS if len([m for m in unicodedata.normalize("NFD", c)[1:] if m != "̣"]) == 2
           and "̛" not in unicodedata.normalize("NFD", c)]
HORNED = [c for c in LETTERS if "̛" in unicodedata.normalize("NFD", c)]

#: Styles at the edges of what the examples use: light, heavy, condensed, slab serif, monospaced, slanted.
STYLES = {
    "light": Params(weight=40, contrast=0.6, flare=0.3),
    "regular": Params(),
    "heavy": preset("technical", weight=150),
    "condensed bold": preset("flare", width=0.56, weight=132, cap=715, asc=752),
    "typewriter": preset("typewriter", weight=112),
    "mono bold": preset("mono", weight=126, xh=542),
    "rounded heavy": preset("rounded", weight=132, xh=540, desc=-150),
    "tube condensed": preset("condensed", contrast=1.0, cap_weight=1.0, roundness=1.0, weight=118, xh=560),
}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    fam = Family(name="Viet Test", base=Params(flare=0.3, contrast=0.6),
                 axes=[Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 44}, 800: {"weight": 150}})],
                 styles={"Regular": {}, "Bold": {"wght": 800}})
    return fam, build_family(fam, tmp_path_factory.mktemp("viet"))


def _parts(recipes, char, p):
    """The ink of each mark of a letter, in the order drawn, and the ink of its horn."""
    by_char = {chr(r.unicode): n for n, r in recipes.items() if r.unicode}
    rec = recipes[by_char[char]]
    g = recipes._run(rec, p)
    ink = lambda strokes: union([c for s in strokes for c in expand(s, g.pen, p.roundness)])
    marks = [ink([s]) for s in g.strokes if s.tag == "mark"]
    horn = ink([s for s in g.strokes if s.tag == "horn"])
    return marks, horn


def _apart(a, b, gap):
    """The two shapes keep at least ``gap`` between them."""
    near = intersection(dilate(a, gap / 2), dilate(b, gap / 2))
    return not any(abs(contour_area(c)) > 0.5 for c in near)


def test_every_vietnamese_letter_is_in_the_latin_and_the_mono_set():
    for recipes in (latin(), mono()):
        covered = {r.unicode for r in recipes.values() if r.unicode}
        missing = [c for c in ALPHABET if ord(c) not in covered]
        assert not missing, missing
        assert set(range(0x1EA0, 0x1EFA)) | {0x1A0, 0x1A1, 0x1AF, 0x1B0, 0x20AB, 0x309, 0x323, 0x31B} <= covered


def test_a_small_set_can_keep_the_vietnamese_alphabet():
    small = latin().only(vietnamese=True)
    assert {ord(c) for c in ALPHABET} <= {r.unicode for r in small.values()}
    assert len(latin().only()) < len(small) < len(latin()) * 0.6


def test_a_family_with_a_weight_axis_builds_with_no_warnings(built):
    fam, res = built
    assert res.warnings == []
    assert res.variable is not None and set(res.statics) == {"Regular", "Bold"}
    for path in list(res.statics.values()) + [res.variable]:
        cmap = TTFont(path).getBestCmap()
        missing = [c for c in ALPHABET if ord(c) not in cmap]
        assert not missing, (path.name, missing)


def test_decomposed_text_uses_the_composed_letters(built):
    import uharfbuzz as hb
    _, res = built
    hbf = hb.Font(hb.Face(hb.Blob.from_file_path(str(res.statics["Regular"]))))

    def run(text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hbf, buf, {})
        return [hbf.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    assert run(unicodedata.normalize("NFD", "ấợỰ")) == ["acircumflexacute", "ohorndotbelow", "Uhorndotbelow"]
    assert run("ḅx̉") == ["b", "dotbelowcomb", "x", "hookabovecomb"]


@pytest.mark.parametrize("style", list(STYLES))
def test_two_marks_keep_apart_and_the_horn_clears_the_marks(style):
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    gap = p.xh * 0.02
    for char in STACKED:
        marks, _ = _parts(recipes, char, p)
        assert len(marks) == 2, (char, len(marks))
        first, tone = marks
        assert _apart(first, tone, gap), (style, char)
        assert contour_bounds(tone)[3] > contour_bounds(first)[3], (style, char)      # the tone mark is above
    for char in HORNED:
        marks, horn = _parts(recipes, char, p)
        assert horn, (style, char)
        for m in marks:
            assert _apart(horn, m, gap), (style, char)


@pytest.mark.parametrize("style", list(STYLES))
def test_the_dot_below_clears_the_letter(style):
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    by_char = {chr(r.unicode): n for n, r in recipes.items() if r.unicode}
    for char in "ạặậẹệịọộợụựỵẠẶẬẸỆỊỌỘỢỤỰỴ":
        g = recipes._run(recipes[by_char[char]], p)
        dot = [c for kind, c, _ in g.shapes if kind == "dot"][-1]
        b = contour_bounds([dot])
        assert b[3] < -p.overshoot, (style, char)                     # under the baseline and the overshoot
        letter = union([c for s in g.strokes for c in expand(s, g.pen, p.roundness)])
        assert _apart(letter, [dot], p.xh * 0.02), (style, char)       # and clear of a tail (ỵ)


@pytest.mark.parametrize("weight", [56, 126])
def test_every_vietnamese_glyph_keeps_the_cell(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    for char in LETTERS + "₫":
        rec = next(r for r in recipes.values() if r.unicode == ord(char))
        g = recipes.draw(rec.name, p)
        b = contour_bounds(g.contours)
        assert g.advance == 600, (char, g.advance)
        assert b[0] >= 0 and b[2] <= 600, (char, b)


@pytest.mark.parametrize("style", list(STYLES))
def test_the_tallest_letter_stays_under_the_top_of_the_line(style):
    p = STYLES[style]
    recipes = mono() if p.mono else latin()
    tops = {}
    for name in recipes:
        if recipes[name].unicode and chr(recipes[name].unicode) in ALPHABET:
            b = contour_bounds(recipes.draw(name, p).contours)
            if b:
                tops[name] = b[3]
    tallest = max(tops, key=tops.get)
    assert tops[tallest] <= p.line_top, (style, tallest, tops[tallest], p.line_top)


def test_the_tallest_glyph_is_inside_the_ascent_of_every_font(built):
    from fontTools.varLib.instancer import instantiateVariableFont
    _, res = built
    for path in res.statics.values():
        font = TTFont(path)
        glyf = font["glyf"]
        viet = [font.getBestCmap()[ord(c)] for c in ALPHABET]
        assert max(glyf[n].yMax for n in viet if glyf[n].numberOfContours) <= font["hhea"].ascent, path.name
        assert font["head"].yMax <= font["OS/2"].usWinAscent and -font["head"].yMin <= font["OS/2"].usWinDescent
    # the variable font: the boldest instance must not pass the clipping zone of the file either
    vf = TTFont(res.variable)
    bold = instantiateVariableFont(TTFont(res.variable), {"wght": 800})
    glyf = bold["glyf"]
    tops = []
    for n in bold.getGlyphOrder():
        if glyf[n].numberOfContours:
            glyf[n].recalcBounds(glyf)
            tops.append(glyf[n].yMax)
    assert max(tops) <= vf["OS/2"].usWinAscent
