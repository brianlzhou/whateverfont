import json

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family, latin
from whateverfont import cli, project, proof
from whateverfont.ornament import CHRISTMAS, FROST, illuminate
from whateverfont.probe import probe
from whateverfont.remix import remix_file, round_corners


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("build")
    fam = Family(
        name="Build Test",
        base=Params(flare=0.3, contrast=0.6),
        axes=[Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 50}, 800: {"weight": 150}}),
              Axis("slnt", "Slant", -10, 0, 0, {-10: {"slant": 10}})],
        styles={"Regular": {}, "Bold Italic": {"wght": 700, "slnt": -10}},
    )
    return fam, build_family(fam, out), out


def test_build_has_no_warnings(built):
    _, res, _ = built
    assert res.warnings == []


def test_static_font_is_complete(built):
    fam, res, _ = built
    font = TTFont(res.statics["Regular"])
    cmap = font.getBestCmap()
    for ch in "AZaz09.,é«":
        assert ord(ch) in cmap, ch
    assert font["name"].getBestFamilyName() == "Build Test"
    assert font["OS/2"].fsSelection & 0x80                     # USE_TYPO_METRICS
    assert "GPOS" in font and len(font.getGlyphOrder()) == len(fam.recipes) + 1


def test_bold_italic_is_flagged(built):
    _, res, _ = built
    font = TTFont(res.statics["Bold Italic"])
    assert font["OS/2"].usWeightClass == 700
    assert font["OS/2"].fsSelection & 0x21 == 0x21            # ITALIC and BOLD
    assert font["post"].italicAngle == -10


def test_variable_font_has_every_axis_and_glyph(built):
    fam, res, _ = built
    font = TTFont(res.variable)
    assert [a.axisTag for a in font["fvar"].axes] == ["wght", "slnt"]
    assert {i.coordinates["wght"] for i in font["fvar"].instances} == {400, 700}
    assert len(font.getGlyphOrder()) == len(fam.recipes) + 1
    assert "gvar" in font and "GPOS" in font


def test_woff2_files_are_written(built):
    _, res, _ = built
    assert sum(1 for f in res.files if f.suffix == ".woff2") == 3


def test_proofs_render(built, tmp_path):
    _, res, _ = built
    sheet = proof.sheet(res.statics["Regular"], tmp_path / "sheet.png")
    row = proof.compare([(res.variable, {"wght": 800}, "bold")], tmp_path / "row.png", "Hamburg")
    assert sheet.stat().st_size > 20_000 and row.stat().st_size > 2_000


def test_kerning_pulls_open_pairs_together(built):
    _, res, _ = built
    r = proof.Renderer(res.statics["Regular"])
    kerned = r.shape("AV")[1]
    unkerned = r.shape("AV", {"kern": False})[1]
    assert kerned < unkerned
    assert r.shape("nn")[1] == r.shape("nn", {"kern": False})[1]


def test_probe_reports_a_clean_design(built):
    fam, _, _ = built
    report = probe(fam)
    assert report["problems"] == []
    assert report["measured"]["n_stems"] == [82.0, 82.0]


def test_probe_notices_a_bold_that_fills_in():
    fam = Family(name="Too Bold", base=Params(weight=260))
    assert any("filling in" in p for p in probe(fam, chars="noe")["problems"])


def test_color_font(tmp_path):
    fam = Family(name="Color Test", recipes=illuminate(latin(), names=["A", "B"]),
                 palettes={"Christmas": CHRISTMAS, "Frost": FROST})
    res = build_family(fam, tmp_path)
    assert res.warnings == []
    font = TTFont(res.statics["Regular"])
    assert font["COLR"].version == 0 and len(font["CPAL"].palettes) == 2
    layers = font["COLR"].ColorLayers
    assert set(layers) == {"A", "B"} and len(layers["A"]) >= 5


def test_remix_rounds_and_renames(built, tmp_path):
    _, res, _ = built
    out = remix_file(res.statics["Regular"], tmp_path, name="Soft Copy", round_=30)
    font = TTFont(out)
    assert font["name"].getBestFamilyName() == "Soft Copy"
    assert "remix of Build Test" in font["name"].getDebugName(10)
    with pytest.raises(ValueError):
        remix_file(res.statics["Regular"], tmp_path, name="Build Test", round_=30)


def test_only_a_large_woff2_gets_the_wide_brotli_window(built, tmp_path):
    """Data over 4 MB is compressed with a 16 MB window. A small font comes out byte for byte as before."""
    import brotli
    from whateverfont import compile as comp
    seen = []

    class Recorder:
        MODE_FONT = brotli.MODE_FONT

        def compress(self, data, **options):
            seen.append(options.get("lgwin"))
            return brotli.compress(data, **options)

    wide = comp._WideBrotli(Recorder())
    big = bytes(range(256)) * ((1 << 22) // 256 + 1)
    assert brotli.decompress(wide.compress(big, mode=brotli.MODE_FONT)) == big
    wide.compress(b"small", mode=brotli.MODE_FONT)
    assert seen == [comp.WIDE_WINDOW, None] and wide.MODE_FONT == brotli.MODE_FONT
    _, res, _ = built
    ours = comp.save_woff2(res.statics["Regular"], tmp_path / "ours")
    plain = TTFont(res.statics["Regular"])
    plain.flavor, plain.recalcTimestamp = "woff2", False
    plain.save(tmp_path / "plain.woff2")
    assert ours.read_bytes() == (tmp_path / "plain.woff2").read_bytes()


def test_a_remix_renames_the_names_in_every_language(built, tmp_path):
    """A source with Japanese, Chinese and Korean names (as Noto Sans CJK has) loses its name there too."""
    _, res, _ = built
    src = TTFont(res.statics["Regular"])
    for lang, local in ((0x411, "ビルドテスト"), (0x804, "构建测试"), (0x404, "構建測試"), (0x412, "빌드 테스트")):
        for nid in (1, 4, 16):
            src["name"].setName(local, nid, 3, 1, lang)
        src["name"].setName(f"{local} Regular", 6 if lang == 0x411 else 18, 3, 1, lang)
    src["name"].setName("Copyright 2026 The Build Test Authors", 0, 3, 1, 0x411)
    path = tmp_path / "BuildTestCJK.ttf"
    src.save(path)
    font = TTFont(remix_file(path, tmp_path / "out", name="Soft Copy", round_=30))
    names = font["name"].names
    assert {r.toUnicode() for r in names if r.nameID == 1} == {"Soft Copy"}
    assert {r.toUnicode() for r in names if r.nameID == 4} == {"Soft Copy Regular"}
    assert not [r for r in names if r.nameID in (16, 18) or r.nameID in (1, 2, 3, 4, 6) and r.langID not in (0, 0x409)]
    assert not [r for r in names if r.nameID != 0 and ("Build Test" in r.toUnicode() or "テスト" in r.toUnicode())]
    # the notices stay, in every language
    assert "The Build Test Authors" in font["name"].getName(0, 3, 1, 0x411).toUnicode()


def test_round_corners_adds_arcs_to_a_square():
    square = [[(0j, 100j), (100j, 100 + 100j), (100 + 100j, 100 + 0j), (100 + 0j, 0j)]]
    (rounded,) = round_corners(square, 20)
    assert len(rounded) == 8 and sum(1 for seg in rounded if len(seg) == 4) == 4


def test_cli_new_build_look_probe(tmp_path, capsys):
    path = tmp_path / "my-font"
    assert cli.main(["new", str(path), "--preset", "rounded", "--brief", "A soft sans."]) == 0
    assert cli.main(["build", str(path)]) == 0
    assert (path / "board.html").stat().st_size > 50_000
    assert cli.main(["look", str(path), "--text", "Hello"]) == 0
    assert cli.main(["look", str(path), "--xray", "ag"]) == 0
    assert cli.main(["look", str(path), "--directions"]) == 0
    assert (path / "proofs" / "directions.png").exists()
    capsys.readouterr()
    assert cli.main(["probe", str(path), "--glyphs", "no"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["family"] == "My Font" and "glyphs" not in summary
    assert cli.main(["probe", str(path), "--glyphs", "no", "--full"]) == 0
    assert set(json.loads(capsys.readouterr().out)["glyphs"]) == {"n", "o"}
    proj = project.load(path)
    assert proj.family.name == "My Font" and "A soft sans." in proj.brief


def test_color_family_with_axes_warns_and_keeps_color(tmp_path):
    fam = Family(name="Color Axes", recipes=illuminate(latin(), names=["A"]), palettes={"Christmas": CHRISTMAS},
                 axes=[Axis("wght", "Weight", 300, 400, 700, {700: {"weight": 130}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    res = build_family(fam, tmp_path)
    assert res.variable is None and res.warnings == []
    assert any("palettes" in n for n in res.notes)
    assert all("COLR" in TTFont(p) for p in res.statics.values())


def _strip_license(src, dst):
    font = TTFont(src)
    for nid in (13, 14):
        font["name"].removeNames(nameID=nid)
    font["name"].setName("Copyright 2026 Somebody. All rights reserved.", 0, 3, 1, 0x409)
    font.save(dst)
    return dst


def test_remix_accepts_a_closed_font_and_the_command_says_so(built, tmp_path, capsys):
    from whateverfont.remix import declared_license
    _, res, _ = built
    closed = _strip_license(res.statics["Regular"], tmp_path / "closed.ttf")
    assert declared_license(TTFont(closed))[0] is False
    assert declared_license(TTFont(res.statics["Regular"]))[0] is True
    assert cli.main(["remix", str(closed), "--name", "Soft Copy", "--round", "30", "--out", str(tmp_path / "o")]) == 0
    assert "declares no open license" in capsys.readouterr().err


def test_remix_keeps_the_pictures_of_a_symbol_font(tmp_path):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib.tables._c_m_a_p import cmap_format_4

    def square():
        pen = TTGlyphPen(None)
        pen.moveTo((100, 0)), pen.lineTo((100, 600)), pen.lineTo((500, 600)), pen.lineTo((500, 0))
        pen.closePath()
        return pen.glyph()

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "bird", "nest"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": square(), "bird": square(), "nest": square()})
    fb.setupHorizontalMetrics({n: (600, 100) for n in (".notdef", "bird", "nest")})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Dingbat Test", "styleName": "Regular",
                       "licenseDescription": "This Font Software is licensed under the SIL Open Font License, 1.1"})
    fb.setupOS2()
    fb.setupPost()
    sym = cmap_format_4(4)
    sym.platformID, sym.platEncID, sym.language = 3, 0, 0
    sym.cmap = {0xF041: "bird", 0xF042: "nest"}
    fb.font["cmap"].tables = [sym]
    src = tmp_path / "dingbat.ttf"
    fb.save(src)
    out = TTFont(remix_file(src, tmp_path / "out", name="Round Dingbat", round_=30))
    assert {"bird", "nest"} <= set(out.getGlyphOrder())
    assert out["glyf"]["bird"].numberOfContours == 1


def test_dilate_keeps_a_circle_solid():
    from whateverfont.geom import contour_area
    from whateverfont.outline import circle, dilate
    grown = dilate([circle(0, 0, 100)], 20)
    assert len(grown) == 1 and abs(contour_area(grown[0])) == pytest.approx(3.1416 * 120 ** 2, rel=0.01)


def test_contour_pen_reads_a_contour_with_no_on_curve_point():
    from whateverfont.outline import ContourPen
    pen = ContourPen()
    pen.qCurveTo((0, 100), (100, 100), (100, 0), (0, 0), None)
    assert len(pen.contours) == 1 and len(pen.contours[0]) == 4


def test_probe_skips_letter_checks_for_redrawn_letters():
    recipes = latin()

    def blob(g):
        g.shape([(0j, 400j), (400j, 400 + 400j), (400 + 400j, 400 + 0j), (400 + 0j, 0j)])
        g.frame(None, "o", "o")
    for ch in "eaon":
        recipes[ch] = type(recipes[ch])(ch, blob, ord(ch), "lower")
    report = probe(Family(name="Pictures", recipes=recipes))
    assert not any(pr.startswith(("e:", "a:", "o:", "n:")) for pr in report["problems"])
    assert "skipped" in report


def test_equal_tiles_give_every_initial_one_advance():
    for equal in (True, 880):
        fam = Family(name="Tiles", recipes=illuminate(latin(), names=["I", "W", "O"], equal=equal),
                     palettes={"Christmas": CHRISTMAS})
        glyphs = fam.draw(names=["I", "W", "O"])
        assert len({g.advance for g in glyphs.values()}) == 1


def test_the_basic_set_covers_all_of_latin1_and_common_signs():
    covered = {r.unicode for r in latin().values() if r.unicode}
    # U+00AD SOFT HYPHEN is left out on purpose: fontbakery recommends against it
    latin1 = (set(range(0x20, 0x7F)) | set(range(0xA0, 0x100))) - {0xAD}
    assert latin1 <= covered, sorted(hex(c) for c in latin1 - covered)
    assert {ord(c) for c in "ŒœŁłĐđĦħȷẞẀẁẂẃẄẅỲỳĴĵ˘˙˚˛˜˝"} <= covered
    assert set(range(0x300, 0x30D)) - {0x305, 0x309} <= covered     # combining marks
    # Polish, Turkish, Romanian, Hungarian, Baltic
    assert {ord(c) for c in "ĄąĘęŃńŚśŹźŻżĞğİŞşȘșȚțŐőŰűĀāĒēĪīŪūĖėĮįŲųĢģĶķĻļŅņďľť"} <= covered
    assert {ord(c) for c in "€£¥¢©®™§¶†‡±÷‰′″‚„⁄"} <= covered


def test_combining_marks_attach_with_mark_positioning(built):
    import uharfbuzz as hb
    _, res, _ = built
    for path in (res.statics["Regular"], res.variable):
        font = TTFont(path)
        assert {"mark", "mkmk"} <= {fr.FeatureTag for fr in font["GPOS"].table.FeatureList.FeatureRecord}
        assert "ccmp" in {fr.FeatureTag for fr in font["GSUB"].table.FeatureList.FeatureRecord}
        hbf = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        buf = hb.Buffer()
        buf.add_str("Aj́")
        buf.guess_segment_properties()
        hb.shape(hbf, buf, {})
        names = [hbf.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
        assert names == ["A", "dotlessj", "acutecomb"]          # ccmp drops the dot of j
        j_adv = buf.glyph_positions[1].x_advance
        mark_x = buf.glyph_positions[2].x_offset
        assert -j_adv < mark_x < 0                                # the accent sits over the j


def test_proof_draws_marks_where_harfbuzz_puts_them(built, tmp_path):
    _, res, _ = built
    out = proof.lines(res.statics["Regular"], tmp_path / "marks.png", ["J́ ố"], px=60)
    assert out.exists()


def test_locl_gives_romanian_commas_and_the_catalan_middle_dot(built):
    import uharfbuzz as hb
    _, res, _ = built
    hbf = hb.Font(hb.Face(hb.Blob.from_file_path(str(res.statics["Regular"]))))

    def run(text, lang):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        buf.language = lang
        hb.shape(hbf, buf, {})
        return [hbf.glyph_to_string(i.codepoint) for i in buf.glyph_infos]
    assert run("Ş", "ro") == ["Scommaaccent"] and run("Ş", "en") == ["Scedilla"]
    assert run("l·l", "ca")[1] == "periodcentered.loclCAT" and run("l·l", "en")[1] == "periodcentered"


def test_effects_build_and_a_cut_family_gets_static_fonts_only(tmp_path):
    from whateverfont import effects
    small = latin().only("Hamburgefonstiv 0123")
    cut = Family(name="Cut Test", base=Params(weight=150), recipes=effects.stencil(small),
                 axes=[Axis("wght", "Weight", 400, 400, 700, {700: {"weight": 180}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    res = build_family(cut, tmp_path / "cut")
    assert res.warnings == [] and res.variable is None and set(res.statics) == {"Regular", "Bold"}
    assert any("no variable font" in n for n in res.notes)
    # the o is cut in two by its bridge
    assert TTFont(res.statics["Regular"])["glyf"]["o"].numberOfContours == 2

    for name, recipes, keys in (
        ("inline", effects.inline(small), None),
        ("outlined", effects.outlined(small), None),
        ("shadow", effects.shadow(small), None),
        ("stripes", effects.stripes(small), None),
        ("rough", effects.rough(small), None),
        ("glow", effects.glow(small), effects.glow_palette("#FF2E9A")),
        ("layered", effects.layered_shadow(small), {"side": "#000000", "face": "#FFAA00"}),
        ("banded", effects.banded(small, bands=3), {"band0": "#111111", "band1": "#555555", "band2": "#999999"}),
        ("mosaic", effects.mosaic(small, colors=3), effects.paint_palette("#222222", ["#AA0000", "#00AA00", "#0000AA"])),
        ("dotted", effects.dotted(small, colors=3), effects.paint_palette("#EEEEEE", ["#AA0000", "#00AA00", "#0000AA"])),
        ("painted", effects.painted(small, colors=3), effects.paint_palette("#222222", ["#AA0000", "#00AA00", "#0000AA"])),
    ):
        fam = Family(name=f"Fx {name}", base=Params(weight=150), recipes=recipes,
                     palettes={"One": keys} if keys else {})
        res = build_family(fam, tmp_path / name, variable=False, woff2=False)
        assert res.warnings == [], (name, res.warnings)
        font = TTFont(res.statics["Regular"])
        assert ("COLR" in font) == bool(keys), name
        assert font["glyf"]["H"].numberOfContours > 0, name


def test_erode_reads_the_band_when_skia_cannot_cut_it(monkeypatch):
    """Skia sometimes cannot subtract the band from a long, wavy outline (Platen Ribbon's Ш). Erode then
    takes what is left from the band's own contours, and that is the same shape."""
    import pathops

    from whateverfont import effects
    from whateverfont.geom import contour_area
    from whateverfont.outline import union
    area = lambda cs: round(sum(-contour_area(c) for c in cs))
    for name in ("H", "o", "B", "eight", "percent"):             # no counter, one, two, an island
        shape = union(latin().draw(name, Params(weight=110)).contours)
        exact = effects.erode(shape, 6.0)
        with monkeypatch.context() as m:
            def fail(*args):
                raise pathops.PathOpsError("operation did not succeed")
            m.setattr(effects, "difference", fail)
            read = effects.erode(shape, 6.0)
        assert (len(read), area(read)) == (len(exact), area(exact)), name


def test_painted_letters_are_the_same_in_every_build(tmp_path):
    from whateverfont import effects
    def build(where):
        fam = Family(name="Paint", base=Params(weight=150), recipes=effects.painted(latin().only("ag"), colors=3),
                     palettes={"One": effects.paint_palette("#222222", ["#AA0000", "#00AA00", "#0000AA"])})
        return build_family(fam, tmp_path / where, variable=False, woff2=False).statics["Regular"].read_bytes()
    assert build("a") == build("b")


def test_only_keeps_the_characters_asked_for():
    small = latin().only("ab1")
    assert {r.unicode for r in small.values()} == {ord("a"), ord("b"), ord("1"), 0x20, 0xA0}
    assert 90 < len(latin().only()) < 110


def test_a_very_heavy_one_keeps_its_stem():
    from whateverfont import Params, latin
    from whateverfont.probe import _runs

    for weight in (150, 200, 230):
        p = Params(weight=weight, counter=300, width=1.04)
        one = latin().draw("one", p)
        runs = _runs(one, p.cap * 0.3)
        assert len(runs) == 1 and runs[0][1] - runs[0][0] > weight * 0.8, (weight, runs)


def test_a_cut_never_runs_along_the_stroke():
    """A horizontal cut on a nearly horizontal stroke end left a spike as long as the stroke is thick."""
    from whateverfont.geom import contour_bounds
    from whateverfont.stroke import Cap, FixedPen, Node, Stroke, expand

    flat = Stroke([Node(0j), Node(300 + 12j)], [None], False, Cap(None), Cap(1 + 0j), fixed=100)
    b = contour_bounds(expand(flat, FixedPen(100), 0.0))
    assert b[2] < 300 + 100 / 0.78 + 6         # the reach of a cut at 38 degrees to a stroke 200 thick
    steep = Stroke([Node(0j), Node(300 + 300j)], [None], False, Cap(None), Cap(1 + 0j), fixed=100)
    assert abs(contour_bounds(expand(steep, FixedPen(100), 0.0))[3] - 300) < 1      # a usual cut is not changed


def test_union_keeps_every_piece_or_says_so(monkeypatch):
    """A merge that loses a piece is tried again, and a merge that cannot be made is reported."""
    import pathops
    from whateverfont import outline
    from whateverfont.geom import contour_bounds

    def box(x0, y0, x1, y1):
        pts = [complex(x0, y0), complex(x0, y1), complex(x1, y1), complex(x1, y0)]
        return [(pts[i], pts[(i + 1) % 4]) for i in range(4)]

    two = [box(0, 0, 100, 100), box(50, 50, 200, 200)]
    del outline.trouble[:]
    merged = outline.union(two)
    assert len(merged) == 1 and contour_bounds(merged) == (0, 0, 200, 200)
    assert not outline.trouble

    # Skia loses the second box on the first try only: the second try must give the whole shape
    real, calls = pathops.Path.simplify, []

    def lossy(self, *a, **k):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("no result")
        return real(self, *a, **k)

    monkeypatch.setattr(pathops.Path, "simplify", lossy)
    merged = outline.union(two)
    assert len(merged) == 1 and len(calls) == 2 and not outline.trouble
    assert all(abs(a - b) < 1 for a, b in zip(contour_bounds(merged), (0, 0, 200, 200)))

    # a result that lacks a piece counts as a failure too
    far = [box(0, 0, 100, 100), box(400, 0, 500, 100)]
    monkeypatch.setattr(outline, "from_path", lambda path: far[:1])
    kept = outline.union(far)
    assert len(kept) == 2 and outline.trouble
    del outline.trouble[:]
    monkeypatch.undo()

    def broken(self, *a, **k):
        raise RuntimeError("no result")

    monkeypatch.setattr(pathops.Path, "simplify", broken)
    kept = outline.union(two)
    assert len(kept) == 2 and outline.trouble
    del outline.trouble[:]


def test_a_remix_keeps_every_character_unless_it_is_cut_to_latin(tmp_path):
    """A remix is a whole font: the characters and the features of its source, not a Latin core."""
    from whateverfont.presets import preset
    fam = Family(name="Whole Source", base=preset("humanist"))
    res = build_family(fam, tmp_path / "src", variable=False)
    src = TTFont(res.statics["Regular"])
    whole = TTFont(remix_file(res.statics["Regular"], tmp_path / "whole", name="Whole Copy", round_=20))
    assert set(whole.getBestCmap()) == set(src.getBestCmap())
    assert len(whole.getGlyphOrder()) == len(src.getGlyphOrder())
    cut = TTFont(remix_file(res.statics["Regular"], tmp_path / "cut", name="Cut Copy", round_=20, subset=True))
    assert set(cut.getBestCmap()) < set(src.getBestCmap())
    assert 0x1EA0 in whole.getBestCmap() and 0x1EA0 not in cut.getBestCmap()      # a Vietnamese letter
