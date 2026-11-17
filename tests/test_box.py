"""Box drawings and block elements: glyphs that fill the cell and join their neighbors."""

import unicodedata

import pytest
from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, build_family, mono
from whateverfont.geom import contour_area, contour_bounds
from whateverfont.presets import preset

CODES = range(0x2500, 0x25A0)
WEIGHTS = [50, 78, 124]
CELL = 600


def name(cp: int) -> str:
    return f"uni{cp:04X}"


def area(glyph) -> float:
    """Ink in square units. A clockwise contour has a negative area, and a hole a positive one."""
    return -sum(contour_area(c) for c in glyph.contours)


def edge(glyph, side: str, p) -> list:
    """The ink on one edge of the cell: merged (from, to) spans along that edge."""
    at = {"l": 0.0, "r": float(CELL), "d": p.line_bottom, "u": p.line_top}[side]
    spans = []
    for contour in glyph.contours:
        for seg in contour:
            a, b = seg[0], seg[-1]
            if side in "lr" and abs(a.real - at) < 0.01 and abs(b.real - at) < 0.01:
                spans.append(sorted((a.imag, b.imag)))
            if side in "du" and abs(a.imag - at) < 0.01 and abs(b.imag - at) < 0.01:
                spans.append(sorted((a.real, b.real)))
    merged = []
    for lo, hi in sorted(spans):
        if merged and lo <= merged[-1][1] + 0.01:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [(round(lo, 2), round(hi, 2)) for lo, hi in merged]


def line_ends(recipes, p) -> dict:
    """What a neighbor shows on the shared edge: the ends of the light, heavy and double lines."""
    flat = {k: edge(recipes.draw(name(cp), p), "r", p) for k, cp in (("l", 0x2500), ("h", 0x2501), ("d", 0x2550))}
    upright = {k: edge(recipes.draw(name(cp), p), "u", p) for k, cp in (("l", 0x2502), ("h", 0x2503), ("d", 0x2551))}
    flat["-"] = upright["-"] = []
    return {"l": flat, "r": flat, "u": upright, "d": upright}


#: Arms in the order up, down, left, right: - none, l light, h heavy, d double. Written by hand from the code charts.
ARMS = {
    0x2500: "--ll", 0x2502: "ll--", 0x250C: "-l-l", 0x2510: "-ll-", 0x2514: "l--l", 0x2518: "l-l-",
    0x251C: "ll-l", 0x2524: "lll-", 0x252C: "-lll", 0x2534: "l-ll", 0x253C: "llll",
    0x2501: "--hh", 0x2503: "hh--", 0x250F: "-h-h", 0x2513: "-hh-", 0x2517: "h--h", 0x251B: "h-h-",
    0x2523: "hh-h", 0x252B: "hhh-", 0x2533: "-hhh", 0x253B: "h-hh", 0x254B: "hhhh",
    0x250D: "-l-h", 0x250E: "-h-l", 0x251E: "hl-l", 0x2521: "hl-h", 0x252D: "-lhl", 0x2532: "-hlh",
    0x253D: "llhl", 0x2540: "hlll", 0x2543: "hlhl", 0x2546: "lhlh", 0x254A: "hhlh",
    0x2550: "--dd", 0x2551: "dd--", 0x2554: "-d-d", 0x2557: "-dd-", 0x255A: "d--d", 0x255D: "d-d-",
    0x2560: "dd-d", 0x2563: "ddd-", 0x2566: "-ddd", 0x2569: "d-dd", 0x256C: "dddd",
    0x2552: "-l-d", 0x2553: "-d-l", 0x2555: "-ld-", 0x2556: "-dl-", 0x2558: "l--d", 0x2559: "d--l",
    0x255B: "l-d-", 0x255C: "d-l-", 0x255E: "ll-d", 0x255F: "dd-l", 0x2561: "lld-", 0x2562: "ddl-",
    0x2564: "-ldd", 0x2565: "-dll", 0x2567: "l-dd", 0x2568: "d-ll", 0x256A: "lldd", 0x256B: "ddll",
    0x256D: "-l-l", 0x256E: "-ll-", 0x256F: "l-l-", 0x2570: "l--l",
    0x2574: "--l-", 0x2575: "l---", 0x2576: "---l", 0x2577: "-l--",
    0x2578: "--h-", 0x2579: "h---", 0x257A: "---h", 0x257B: "-h--",
    0x257C: "--lh", 0x257D: "lh--", 0x257E: "--hl", 0x257F: "hl--",
}


def test_the_mono_set_has_every_box_and_block():
    recipes = mono()
    for cp in CODES:
        assert recipes[name(cp)].unicode == cp


@pytest.mark.parametrize("weight", WEIGHTS)
def test_every_glyph_draws_inside_its_cell(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    for cp in CODES:
        g = recipes.draw(name(cp), p)
        assert g.advance == CELL, name(cp)
        assert area(g) > 100, name(cp)
        b = contour_bounds(g.contours)
        assert b[0] >= 0 and b[2] <= CELL and b[1] >= p.line_bottom and b[3] <= p.line_top, (name(cp), b)


@pytest.mark.parametrize("weight", WEIGHTS)
def test_lines_reach_the_edges_of_the_cell(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    flat = contour_bounds(recipes.draw("uni2500", p).contours)
    assert (flat[0], flat[2]) == (0, CELL)
    upright = contour_bounds(recipes.draw("uni2502", p).contours)
    assert (upright[1], upright[3]) == (p.line_bottom, p.line_top)
    full = recipes.draw("uni2588", p)
    assert contour_bounds(full.contours) == (0, p.line_bottom, CELL, p.line_top)
    assert area(full) == pytest.approx(CELL * (p.line_top - p.line_bottom))


@pytest.mark.parametrize("weight", WEIGHTS)
def test_every_arm_joins_the_line_next_to_it(weight):
    p = preset("mono", weight=weight)
    recipes = mono()
    ends = line_ends(recipes, p)
    assert ends["l"]["l"] != ends["l"]["h"] != ends["l"]["d"] and len(ends["l"]["d"]) == 2
    for cp, arms in ARMS.items():
        g = recipes.draw(name(cp), p)
        for side, kind in zip("udlr", arms):
            assert edge(g, side, p) == ends[side][kind], (name(cp), side)
    # the rest of the junctions: whatever reaches an edge is the end of a light, heavy or double line
    for cp in range(0x2500, 0x2580):
        words = unicodedata.name(chr(cp)).split()
        if "DASH" in words or "DIAGONAL" in words:
            continue
        g = recipes.draw(name(cp), p)
        found = [next((k for k in "-lhd" if edge(g, side, p) == ends[side][k]), None) for side in "udlr"]
        assert None not in found and found != ["-"] * 4, (name(cp), found)


def test_double_lines_stay_open_where_they_meet():
    p = preset("mono")
    recipes = mono()
    # a double cross is four corners around an open center; a double corner is an outer and an inner line
    assert len(recipes.draw("uni256C", p).contours) == 4
    assert len(recipes.draw("uni2554", p).contours) == 2
    assert len(recipes.draw("uni2550", p).contours) == 2
    assert len(recipes.draw("uni253C", p).contours) == 1


@pytest.mark.parametrize("cp, count, side", [(0x254C, 2, "x"), (0x2504, 3, "x"), (0x2509, 4, "x"),
                                             (0x254F, 2, "y"), (0x2506, 3, "y"), (0x250A, 4, "y")])
def test_a_row_of_dashes_has_an_even_rhythm(cp, count, side):
    p = preset("mono")
    g = mono().draw(name(cp), p)
    lo, hi = (0, CELL) if side == "x" else (p.line_bottom, p.line_top)
    i = 0 if side == "x" else 1
    dashes = sorted((contour_bounds([c])[i], contour_bounds([c])[i + 2]) for c in g.contours)
    assert len(dashes) == count
    gaps = [b[0] - a[1] for a, b in zip(dashes, dashes[1:])]
    around = (dashes[0][0] - lo) + (hi - dashes[-1][1])          # the gap between this cell and the next
    assert max(gaps + [around]) - min(gaps + [around]) <= 1
    assert min(gaps) > 20


def test_shades_and_blocks_cover_their_share_of_the_cell():
    p = preset("mono")
    recipes = mono()
    cell = CELL * (p.line_top - p.line_bottom)
    shares = {0x2591: 0.25, 0x2592: 0.50, 0x2593: 0.75,                 # the shades
              0x2580: 1 / 2, 0x2581: 1 / 8, 0x2584: 1 / 2, 0x2587: 7 / 8, 0x2589: 7 / 8, 0x258C: 1 / 2,
              0x258F: 1 / 8, 0x2590: 1 / 2, 0x2594: 1 / 8, 0x2595: 1 / 8,
              0x2596: 1 / 4, 0x2599: 3 / 4, 0x259A: 1 / 2, 0x259F: 3 / 4}
    for cp, share in shares.items():
        assert area(recipes.draw(name(cp), p)) / cell == pytest.approx(share, abs=0.01), name(cp)
    # halves that meet: the lower block ends where the upper block starts, and so do left and right
    lower, upper = (contour_bounds(recipes.draw(name(cp), p).contours) for cp in (0x2584, 0x2580))
    assert lower[3] == upper[1] and (lower[1], upper[3]) == (p.line_bottom, p.line_top)
    left, right = (contour_bounds(recipes.draw(name(cp), p).contours) for cp in (0x258C, 0x2590))
    assert left[2] == right[0] and (left[0], right[2]) == (0, CELL)
    assert contour_bounds(recipes.draw("uni2598", p).contours) == (0, lower[3], left[2], p.line_top)


def test_boxes_stay_upright_in_a_slanted_style():
    p = preset("mono", slant=10)
    recipes = mono()
    flat = contour_bounds(recipes.draw("uni2500", p).contours)
    assert flat[0] == pytest.approx(0, abs=0.01) and flat[2] == pytest.approx(CELL, abs=0.01)
    upright = contour_bounds(recipes.draw("uni2502", p).contours)
    assert upright[2] - upright[0] == pytest.approx(70, abs=0.01)


def test_a_proportional_font_draws_them_in_a_600_cell():
    p = preset("grotesk")
    g = mono().draw("uni2500", p)
    assert g.advance == CELL and contour_bounds(g.contours)[2] == CELL


def test_a_family_builds_with_the_boxes_in_every_font(tmp_path):
    fam = Family(name="Box Test", base=preset("mono"),
                 axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 50}, 700: {"weight": 124}})],
                 styles={"Regular": {}, "Bold": {"wght": 700}})
    res = build_family(fam, tmp_path)
    assert res.warnings == []
    for path in list(res.statics.values()) + [res.variable]:
        font = TTFont(path)
        cmap, glyf, hmtx = font.getBestCmap(), font["glyf"], font["hmtx"]
        for cp in CODES:
            assert cmap[cp] == name(cp) and hmtx[name(cp)][0] == CELL, (path.name, name(cp))
            assert glyf[name(cp)].numberOfContours > 0, (path.name, name(cp))
        # a row joins up, and so do the lines of a text: the glyphs end on the advance and on the line height
        flat, upright, full = glyf["uni2500"], glyf["uni2502"], glyf["uni2588"]
        assert (flat.xMin, flat.xMax) == (0, CELL)
        assert (upright.yMin, upright.yMax) == (font["hhea"].descent, font["hhea"].ascent)
        assert font["hhea"].lineGap == 0 and font["OS/2"].sTypoLineGap == 0
        assert (full.xMin, full.yMin, full.xMax, full.yMax) == (0, font["hhea"].descent, CELL, font["hhea"].ascent)
    assert "gvar" in TTFont(res.variable)
