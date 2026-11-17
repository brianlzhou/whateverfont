"""Retracing: the tracer on drawn shapes, and a small Latin font built here and redrawn with another pen.

These tests need the trace extra (numpy) and are skipped without it.
"""

import math

import pytest

pytest.importorskip("numpy")

from fontTools.ttLib import TTFont

from whateverfont import Family, effects, latin, trace
from whateverfont.cli import main
from whateverfont.compile import build_family
from whateverfont.outline import circle, difference, rect, union
from whateverfont.presets import preset


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    """A small font made by the engine itself, under the OFL, with a copyright line to keep."""
    out = tmp_path_factory.mktemp("source")
    fam = Family(name="Trace Source", base=preset("grotesk"), recipes=latin().only("oilxe"),
                 copyright="Copyright 2026 The Source Authors")
    res = build_family(fam, out, variable=False, woff2=False, jobs=1)
    return res.statics["Regular"]


@pytest.fixture(scope="module")
def traced(source):
    return trace.trace_font(source, jobs=1)


@pytest.fixture(scope="module")
def pen():
    return Family(name="Round Pen", base=preset("rounded", weight=120), copyright="Copyright 2026 The Pen Authors",
                  palettes={"Pink": effects.glow_palette("#FF2E9A")})


@pytest.fixture(scope="module")
def redrawn(traced, pen, tmp_path_factory):
    return trace.redraw(traced, tmp_path_factory.mktemp("out"), "Pen Trace", pen, jobs=1)


# -- the tracer on drawn shapes ------------------------------------------------

def test_a_stem_is_one_straight_stroke():
    t = trace.trace_glyph([rect(100, 0, 180, 600)])
    assert len(t["strokes"]) == 1 and not t["dots"]
    pts = t["strokes"][0]["pts"]
    assert all(abs(q.real - 140) < 6 for q in pts)
    assert min(q.imag for q in pts) < 40 and max(q.imag for q in pts) > 560      # it runs end to end
    assert abs(t["width"] - 80) < 8


def test_a_ring_is_one_closed_stroke():
    ring = difference([circle(300, 300, 200)], [circle(300, 300, 120)])
    t = trace.trace_glyph(ring)
    assert len(t["strokes"]) == 1 and t["strokes"][0]["closed"]
    radii = [abs(q - complex(300, 300)) for q in t["strokes"][0]["pts"]]
    assert all(abs(r - 160) < 8 for r in radii)


def test_a_cross_is_two_strokes_through_the_middle():
    cross = union([rect(0, 260, 600, 340), rect(260, 0, 340, 600)])
    t = trace.trace_glyph(cross)
    assert len(t["strokes"]) == 2
    flat = []
    for s in t["strokes"]:
        a, b = s["pts"][0], s["pts"][-1]
        flat.append(abs((b - a).imag) < abs((b - a).real))
        assert abs(b - a) > 450                    # each goes all the way across
    assert sorted(flat) == [False, True]         # one across, one up


def test_a_box_keeps_its_four_corners():
    """A square ring (口) is one closed stroke with four sharp corners, and its drawn sides are straight."""
    box = difference([rect(100, 100, 700, 700)], [rect(150, 150, 650, 650)])
    t = trace.trace_glyph(box)
    assert len(t["strokes"]) == 1 and t["strokes"][0]["closed"]
    corners = t["strokes"][0]["corners"]
    assert len(corners) == 4
    for c in (complex(125, 125), complex(675, 125), complex(675, 675), complex(125, 675)):
        assert min(abs(c - q) for q in corners) < 8
    sk = trace._sk()
    pts = t["strokes"][0]["pts"]
    nodes, handles, flags = trace._bezier(sk, pts, True, eps=2.5, force=corners)
    assert len(nodes) == 4 and all(flags)                     # no node next to a corner to bend the side


def test_a_curve_does_not_bow_out_after_a_round_turn():
    """A long side after a round corner stays on the points it stands for."""
    turn = [complex(60 * math.cos(a), 60 * math.sin(a)) + complex(0, 600)
            for a in [math.pi - i * math.pi / 80 for i in range(81)]]       # a half circle, over the top
    side = [complex(60, 600 - 2 * i) for i in range(1, 300)]               # then straight down
    pts = turn + side
    sk = trace._sk()

    def worst(nodes, handles):
        out = 0.0
        for (p, q), (h0, h1) in zip(zip(nodes, nodes[1:]), handles):
            for t in (0.25, 0.5, 0.75):
                u = 1 - t
                c = u ** 3 * p + 3 * u * u * t * h0 + 3 * u * t * t * h1 + t ** 3 * q
                out = max(out, min(abs(c - d) for d in pts))
        return out

    nodes, handles, _ = trace._bezier(sk, pts, False, eps=2.5, fit=6.0)
    assert worst(nodes, handles) <= 6.0


def test_a_stroke_at_45_degrees_is_traced():
    """Zhang and Suen's thinning wore a straight 45 degree bar (the slash ／) away to one pixel."""
    corners = [complex(935, 842), complex(38, -55), complex(65, -82), complex(962, 815)]
    bar = [[(corners[i], corners[(i + 1) % 4]) for i in range(4)]]
    t = trace.trace_glyph(bar)
    assert len(t["strokes"]) == 1
    a, b = t["strokes"][0]["pts"][0], t["strokes"][0]["pts"][-1]
    assert abs(b - a) > 1150                     # it runs corner to corner


def test_a_dot_is_a_dot():
    t = trace.trace_glyph([circle(100, 100, 45)])
    assert not t["strokes"] and len(t["dots"]) == 1
    center, d = t["dots"][0]
    assert abs(center - complex(100, 100)) < 4 and abs(d - 90) < 8


def test_the_self_check_flags_a_lost_counter():
    ring = difference([circle(300, 300, 200)], [circle(300, 300, 120)])
    assert trace.check(ring, ring) == []
    problems = trace.check(ring, [circle(300, 300, 200)])
    assert any("counter" in p for p in problems)


def test_the_self_check_flags_merged_parts_and_missing_strokes():
    two = [circle(100, 100, 40), circle(300, 100, 40)]
    assert any("merged" in p for p in trace.check(two, union([rect(60, 60, 340, 140)])))
    stem = [rect(100, 0, 180, 600)]
    assert any("misses" in p for p in trace.check(stem, [rect(100, 0, 180, 250)]))


# -- a whole font ----------------------------------------------------------------

def test_every_drawn_glyph_is_traced(source, traced):
    font = TTFont(source)
    drawn = [n for n in font.getGlyphOrder() if n != ".notdef" and font["glyf"][n].numberOfContours > 0]
    assert sorted(traced.glyphs) == sorted(drawn)
    assert traced.warnings == []                   # a sans with even strokes
    assert 40 < traced.width < 140


def test_names_and_license_records(redrawn, source):
    font = TTFont(redrawn.ttf)
    name = font["name"]
    assert name.getDebugName(1) == "Pen Trace"
    assert name.getDebugName(6) == "PenTrace-Regular"
    copyright = name.getDebugName(0)
    assert "The Source Authors" in copyright and "The Pen Authors" in copyright
    assert "Open Font License" in name.getDebugName(13)
    assert name.getDebugName(14) == "https://openfontlicense.org"
    assert name.getDebugName(7) is None            # the source's trademark notice is not kept
    assert "Trace Source" in name.getDebugName(10)
    assert redrawn.woff2.exists() and redrawn.css.exists()
    assert 'font-family: "Pen Trace"' in redrawn.css.read_text()


def test_a_reserved_name_is_refused(source, tmp_path):
    font = TTFont(source)
    with pytest.raises(ValueError, match="Trace Source"):
        trace.check_name(font, "Trace Source Rounded")
    name = font["name"]
    name.setName("Copyright 2026 The Source Authors, with Reserved Font Name \"Quill\".", 0, 3, 1, 0x409)
    name.setName("Brandy is a trademark of Nobody Ltd.", 7, 3, 1, 0x409)
    with pytest.raises(ValueError, match="Quill"):
        trace.check_name(font, "Quill Pen")
    with pytest.raises(ValueError, match="Brandy"):
        trace.check_name(font, "Brandy Round")
    trace.check_name(font, "Brandywine")         # a word that only starts the same is fine


def test_shaping_tables_cmap_and_advances_are_kept(redrawn, source):
    a, b = TTFont(source), TTFont(redrawn.ttf)
    assert a.getBestCmap() == b.getBestCmap()
    assert all(a["hmtx"][n][0] == b["hmtx"][n][0] for n in a.getGlyphOrder())
    for tag in ("GSUB", "GPOS", "GDEF"):
        assert (tag in a) == (tag in b)
        if tag in a:
            assert a[tag].compile(a) == b[tag].compile(b)
    assert "fpgm" not in b and "prep" not in b     # no hinting
    o = b["glyf"]["o"]
    assert o.numberOfContours == 2                 # the o kept its counter
    assert redrawn.traced == len([n for n in a.getGlyphOrder() if n != ".notdef" and a["glyf"][n].numberOfContours])


def test_a_color_effect_gives_layers(traced, pen, tmp_path):
    res = trace.redraw(traced, tmp_path, "Pen Glow", pen, lambda r: effects.glow(r, size=40), jobs=1,
                       effect_label="glow")
    font = TTFont(res.ttf)
    assert "COLR" in font and "CPAL" in font
    layers = font["COLR"].ColorLayers
    assert set(layers) >= {"o", "i", "l", "x", "e"}
    assert all(len(v) == 5 for v in layers.values())     # glow1, glow2, glow3, halo, tube
    assert len(font["CPAL"].palettes) == 1


def test_small_parts_keep_their_color():
    """An effect that covers a dot leaves the dot its own color."""
    dot = [circle(100, 600, 40)]
    stem = [rect(60, 0, 140, 450)]
    shape = union(dot + stem)
    layers = [("letter", shape), ("snow", union([circle(100, 610, 60), rect(40, 430, 160, 480)]))]
    out = trace.uncover_small_parts(shape, layers, stem=80, letter="letter")
    snow = out[1][1]
    from whateverfont.effects import inside
    assert not inside(snow)(complex(100, 600))       # the dot is the letter's color again
    assert inside(snow)(complex(100, 460))           # the snow on the stem stays
    assert trace.uncover_small_parts(shape, layers, stem=80, letter="paint") == layers     # no such layer


def test_an_effect_that_does_not_ask_keeps_its_paint_on_the_dots(traced, tmp_path):
    """Paint on a paper layer of the same outline: the dot of i keeps its paint. Before, retrace took the
    paper for the letter (the layer whose area is closest to the outline) and took the paint off the dot."""
    paper_pen = Family(name="Paper Pen", base=preset("rounded", weight=120),
                       palettes={"Two": {"paper": "#F6F1E7", "paint": "#C8452C", "letter": "#1B1A17",
                                         "snow": "#FFFFFF"}})

    def painted(recipes):
        def effect(g, shape):
            g.layers = [("paper", shape), ("paint", shape)]
        return effects.wrapped(recipes, effect)

    def snowed(recipes):
        def effect(g, shape):
            g.layers = [("letter", shape), ("snow", shape)]
            g.letter_layer = "letter"
        return effects.wrapped(recipes, effect)

    def top_layer_parts(res):
        # i.c1 is the second layer of i: the paint, or the snow
        return TTFont(res.ttf)["glyf"]["i.c1"].numberOfContours

    paint = trace.redraw(traced, tmp_path / "paint", "Pen Paint", paper_pen, painted, jobs=1)
    assert top_layer_parts(paint) == 2            # the stem and the dot, both painted
    snow = trace.redraw(traced, tmp_path / "snow", "Pen Snowed", paper_pen, snowed, jobs=1)
    assert top_layer_parts(snow) == 1             # the dot is the letter's color: snow on the stem only


def test_a_high_contrast_source_gets_a_warning(tmp_path):
    fam = Family(name="Thin Thick", base=preset("humanist", contrast=0.2, weight=140), recipes=latin().only("onmhu"))
    path = build_family(fam, tmp_path, variable=False, woff2=False, jobs=1).statics["Regular"]
    t = trace.trace_font(path, jobs=1)
    assert t.contrast > trace.CONTRAST_WARN
    assert any("vary a lot" in w for w in t.warnings)


def test_a_postscript_source_is_read(pen, tmp_path):
    """A .otf (CFF outlines) gets TrueType outlines and is retraced like any other font."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder([".notdef", "l"])
    fb.setupCharacterMap({ord("l"): "l"})
    strings = {}
    for name, box in ((".notdef", None), ("l", (100, 0, 180, 700))):
        cs = T2CharStringPen(300, None)
        if box:
            x0, y0, x1, y1 = box
            cs.moveTo((x0, y0))
            cs.lineTo((x0, y1))
            cs.lineTo((x1, y1))
            cs.lineTo((x1, y0))
            cs.closePath()
        strings[name] = cs.getCharString()
    fb.setupCFF("PostScriptSource-Regular", {"FullName": "PostScript Source"}, strings, {})
    fb.setupHorizontalMetrics({".notdef": (300, 0), "l": (280, 100)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "PostScript Source", "styleName": "Regular",
                       "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1."})
    fb.setupOS2()
    fb.setupPost()
    path = tmp_path / "PostScriptSource-Regular.otf"
    fb.save(str(path))
    t = trace.trace_font(path, jobs=1)
    assert list(t.glyphs) == ["l"]
    res = trace.redraw(t, tmp_path / "out", "Pen Stick", pen, jobs=1)
    font = TTFont(res.ttf)
    assert "glyf" in font and "CFF " not in font
    assert font["glyf"]["l"].numberOfContours == 1 and font["hmtx"]["l"][0] == 280


def test_the_command(source, tmp_path, capsys):
    out = tmp_path / "PenTrace"
    code = main(["retrace", str(source), "--name", "Pen Trace", "--pen", "examples/lastbell",
                 "--out", str(out), "--jobs", "1"])
    assert code == 0
    text = capsys.readouterr().out
    assert "self-check:" in text and "traced" in text
    assert (out / "ttf" / "PenTrace-Regular.ttf").exists() and (out / "woff2" / "PenTrace-Regular.woff2").exists()


def test_the_named_sets_have_the_standard_characters():
    from whateverfont import charsets
    assert len(charsets.standard("japanese")) == 2965         # JIS X 0208 level 1
    assert len(charsets.standard("chinese")) == 3755          # GB 2312 level 1
    assert len(charsets.standard("korean")) == 2350           # KS X 1001 Hangul
    ja, zh, ko = (charsets.named(n) for n in ("japanese", "chinese", "korean"))
    assert {ord(c) for c in "あアー亜腕。、「」（）"} <= ja
    assert {ord(c) for c in "啊座你想要字体，。"} <= zh and ord("あ") not in zh
    assert {ord(c) for c in "가힝원하는.,?"} <= ko and ord("亜") not in ko
    assert not ({ord(c) for c in "Aa09"} & (ja | zh | ko))  # Latin letters and figures are the Latin family's
    with pytest.raises(ValueError, match="neither a named set"):
        charsets.resolve("klingon")


def test_the_traditional_set_is_big5_level_1():
    from whateverfont import charsets
    hant = charsets.standard("traditional")
    assert len(hant) == 5401                                  # Big5 level 1: A440 to C67E
    assert all(0x4E00 <= cp <= 0x9FFF for cp in hant)         # the ideographs only, not the kana after them
    assert {ord(c) for c in "字型軟體檔案臺灣體驗麼"} <= hant
    assert not {ord(c) for c in "体们这软档"} & hant         # Simplified forms are not in it
    assert len(hant & charsets.standard("chinese")) == 2434   # what the two Chinese sets share
    tc = charsets.named("traditional")
    assert {ord(c) for c in "，。、「」『』（）！？"} <= tc and ord("あ") not in tc
    assert charsets.named("chinese") - charsets.standard("chinese") == tc - hant      # the same punctuation
    assert charsets.resolve("traditional,chinese") == tc | charsets.named("chinese")


def test_only_keeps_some_characters(source, pen, tmp_path):
    """--only keeps the characters asked for, and nothing else is traced or drawn."""
    text = tmp_path / "chars.txt"
    text.write_text("ox\n", encoding="utf-8")
    from whateverfont import charsets
    t = trace.trace_font(source, jobs=1, only=charsets.resolve(str(text)))
    assert set(t.font.getBestCmap()) == {ord("o"), ord("x")}
    assert sorted(t.glyphs) == ["o", "x"]
    assert not t.cjk and t.corners == "sharp"
    res = trace.redraw(t, tmp_path / "out", "Pen Few", pen, jobs=1)
    font = TTFont(res.ttf)
    assert set(font.getBestCmap()) == {ord("o"), ord("x")}
    assert font["glyf"]["o"].numberOfContours == 2
    assert "Trace Source" in font["name"].getDebugName(10)
    with pytest.raises(ValueError, match="none of the characters"):
        trace.trace_font(source, jobs=1, only={0x4E00})


def test_the_command_takes_only(source, tmp_path, capsys):
    text = tmp_path / "chars.txt"
    text.write_text("il", encoding="utf-8")
    out = tmp_path / "PenFew"
    code = main(["retrace", str(source), "--name", "Pen Few", "--pen", "examples/lastbell", "--only", str(text),
                 "--out", str(out), "--jobs", "1"])
    assert code == 0
    printed = capsys.readouterr().out
    assert "keeping 2 of the 2 characters" in printed and "self-check: 0 of 2" in printed
    assert set(TTFont(out / "ttf" / "PenFew-Regular.ttf").getBestCmap()) == {ord("i"), ord("l")}


def test_a_dense_glyph_thins_the_pen():
    """Five bars close together: a heavy pen is thinned for the glyph, so the white between them stays."""
    bars = union([rect(100, 80 + 150 * i, 700, 120 + 150 * i) for i in range(5)] + [rect(380, 80, 420, 720)])
    t = trace._prepare(bars, 0.0, trace.SCALE, dense=True)
    assert t["gaps"][0] > 0 and min(t["gaps"][1:]) > 100        # the white between the bars, about 110 units
    t["apart"] = []
    fat = trace.Pen(None, 1.0, 40.0, 200.0)
    thin, fills = trace.density(t, fat)
    assert 0.5 <= thin < 1.0 and not fills
    light = trace.Pen(None, 1.0, 40.0, 60.0)
    assert trace.density(t, light) == (1.0, False)               # a light pen leaves the white open anyway
    crammed = trace.Pen(None, 1.0, 40.0, 600.0)
    assert trace.density(t, crammed)[1]                          # even half of this pen fills the white


def test_east_asian_fonts_are_found():
    assert trace.east_asian({0x3042: "a", 0x4E00: "b", 0x41: "c"})
    assert not trace.east_asian({0x41: "a", 0x42: "b", 0x4E00: "c"})


def test_the_command_reads_an_effect_file(source, tmp_path, capsys):
    out = tmp_path / "PenSnow"
    code = main(["retrace", str(source), "--name", "Pen Snow", "--pen", "examples/lastbell:Last Bell Snow",
                 "--effect", "examples/lastbell/snow.py:capped:depth=60", "--out", str(out), "--jobs", "1"])
    assert code == 0
    font = TTFont(out / "ttf" / "PenSnow-Regular.ttf")
    assert "COLR" in font and len(font["CPAL"].palettes) == 4
    assert math.isclose(font["head"].unitsPerEm, 1000)


# -- sources that are not like the ones this project draws --------------------

def _hand_font(path, glyphs: dict, cmap: dict, composites: dict | None = None, advance: int = 500):
    """A small TrueType source drawn by hand. ``glyphs`` maps a name to its rectangles (x0, y0, x1, y1), and
    ``composites`` a name to the glyphs it puts together."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    names = [".notdef"] + list(glyphs) + list(composites or {})
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap(cmap)
    drawn = {".notdef": TTGlyphPen(None).glyph()}
    for name, boxes in glyphs.items():
        pen = TTGlyphPen(None)
        for x0, y0, x1, y1 in boxes:
            pen.moveTo((x0, y0))
            pen.lineTo((x0, y1))
            pen.lineTo((x1, y1))
            pen.lineTo((x1, y0))
            pen.closePath()
        drawn[name] = pen.glyph()
    for name, parts in (composites or {}).items():
        pen = TTGlyphPen(drawn)
        for part in parts:
            pen.addComponent(part, (1, 0, 0, 1, 0, 0))
        drawn[name] = pen.glyph()
    fb.setupGlyf(drawn)
    fb.setupHorizontalMetrics({n: (advance, 0) for n in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Hand Source", "styleName": "Regular",
                       "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1."})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(path))
    return path


def test_a_source_with_2048_units_to_the_em_traces_the_same(source, traced, tmp_path):
    """Inter, Roboto and many others have 2048 units to the em. The tracer's lengths are for an em of 1000:
    before, the dot of such a font was too large to be a dot, and i, j, the period and every accent lost it."""
    from fontTools.ttLib.scaleUpem import scale_upem
    font = TTFont(source)
    advance = font["hmtx"]["i"][0]
    scale_upem(font, 2048)
    big = tmp_path / "big.ttf"
    font.save(big)
    t = trace.trace_font(big, jobs=1)
    assert t.upm == 1000 and t.font["head"].unitsPerEm == 1000
    parts = lambda tf: {n: (len(g["strokes"]), len(g["dots"])) for n, g in tf.glyphs.items()}
    assert parts(t) == parts(traced)
    assert len(t.glyphs["i"]["dots"]) == 1
    assert abs(t.font["hmtx"]["i"][0] - advance) <= 1         # the advances come back with the outlines
    assert abs(t.width - traced.width) < 2


def test_only_a_script_with_a_headline_gets_one(tmp_path):
    """Three letters that hang from a bar across their whole width. As Devanagari letters the bar is their
    headline. As Latin letters it is not: before, a Latin font whose dashes and arrows reach their edges at the
    x-height got a headline there, and b, d and h lost what stood above it."""
    letters = {name: [(0, 600, 500, 660), (200 + 60 * i, 0, 260 + 60 * i, 600)]
               for i, name in enumerate(("one", "two", "three"))}
    deva = _hand_font(tmp_path / "deva.ttf", letters, {0x0915 + i: n for i, n in enumerate(letters)})
    latin_ = _hand_font(tmp_path / "latin.ttf", letters, {ord("a") + i: n for i, n in enumerate(letters)})
    assert trace.trace_font(deva, jobs=1).headline
    assert not trace.trace_font(latin_, jobs=1).headline
    assert trace.trace_font(latin_, jobs=1, headline=True).headline      # a person can still ask for it


def test_a_combining_mark_keeps_its_color_in_a_composite(pen, tmp_path):
    """A retraced font keeps the source's composites: i is a stem glyph and a dot glyph. The dot's name has
    "comb" in it, and in the engine's own fonts an effect skips such names. Before, the dot of a retraced
    font got no color layers, so the i of every color font had no dot, and no accented letter its accent."""
    path = _hand_font(tmp_path / "dots.ttf", {"idotless": [(210, 0, 290, 500)], "dotaccentcomb": [(205, 620, 295, 710)]},
                      {ord("i"): "i", 0x0131: "idotless", 0x0307: "dotaccentcomb"},
                      composites={"i": ["idotless", "dotaccentcomb"]})
    t = trace.trace_font(path, jobs=1)
    assert len(t.glyphs["dotaccentcomb"]["dots"]) == 1 and "i" in t.composites
    res = trace.redraw(t, tmp_path / "out", "Pen Dots", pen, lambda r: effects.glow(r, size=40), jobs=1,
                       effect_label="glow")
    font = TTFont(res.ttf)
    layers, glyf = font["COLR"].ColorLayers, font["glyf"]
    assert len(layers["dotaccentcomb"]) == 5 and len(layers["i"]) == 5
    for layer in layers["i"]:
        g = glyf[layer.name]
        assert [c.glyphName.rsplit(".c", 1)[0] for c in g.components] == ["idotless", "dotaccentcomb"]
        g.recalcBounds(glyf)
        assert g.yMax > 620                                   # the layer reaches the dot
