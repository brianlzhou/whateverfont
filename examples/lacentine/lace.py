"""The `doily` color effect and its palettes, for the Lacentine families (see font.py).

Each letter is cut from red card and glued on a paper doily cut to its shape: a band of paper
around the letter with a scalloped edge, a small eyelet in each scallop and a row of punched hearts.
"""

import math

from whateverfont import effects
from whateverfont.geom import contour_area, flatten_contour, reverse_contour
from whateverfont.outline import circle, difference, dilate, union


def heart(cx, cy, size):
    """An upright heart, ``size`` units wide, centered on its box. One clockwise contour of cubics."""
    s = size / 2

    def p(x, y):
        return complex(cx + x * s, cy + (y - 0.02) * s)

    tip, left, dip, right = p(0, -0.92), p(-1.0, 0.32), p(0, 0.50), p(1.0, 0.32)
    return [
        (tip, p(-0.58, -0.42), p(-1.04, -0.08), left),
        (left, p(-0.96, 0.78), p(-0.30, 0.96), dip),
        (dip, p(0.30, 0.96), p(0.96, 0.78), right),
        (right, p(1.04, -0.08), p(0.58, -0.42), tip),
    ]


def along(points, step):
    """Points spaced evenly along a closed polyline, about ``step`` apart; the count is chosen so the ends meet."""
    n = len(points)
    if n < 3:
        return []
    lengths = [abs(points[(i + 1) % n] - points[i]) for i in range(n)]
    total = sum(lengths)
    count = max(3, round(total / step))
    gap = total / count
    out, k, walked = [], 0, 0.0
    for j in range(count):
        target = j * gap
        while k < n - 1 and walked + lengths[k] < target:
            walked += lengths[k]
            k += 1
        t = 0.0 if lengths[k] < 1e-9 else (target - walked) / lengths[k]
        out.append(points[k] + (points[(k + 1) % n] - points[k]) * min(1.0, t))
    return out


def thin(hole, amount):
    """True if a counter of the paper is too narrow to show as a counter (a scrap between scallops)."""
    try:
        return not effects.erode([reverse_contour(hole)], amount)
    except Exception:
        return abs(contour_area(hole)) < 4 * amount * amount


def doily(recipes, band=100.0, scallop=27.0, spacing=1.45, eyelet=6.0, punch=40.0, punch_at=0.55,
          punch_step=1.9, gap=44.0, rim=8.0, keys=4, names=None):
    """Letters on a paper doily cut to their shape.

    Keys, bottom first: backing, lace0 to lace{keys-1} (the letters take them in turn), letter.

    ``band`` is how far the paper reaches past the letter, ``scallop`` the radius of the round
    scallops on its edge, and ``spacing`` the distance between two scallops as a multiple of that
    radius. ``eyelet`` is the radius of the hole in each scallop (0 for none). ``punch`` is the width
    of a punched heart, ``punch_at`` how far into the band its center sits (a share of ``band``),
    and ``punch_step`` the distance between two hearts as a multiple of ``punch``. ``gap`` is the
    paper-to-paper distance between two letters before kerning. ``rim`` is how far the backing
    reaches past the paper (0 for no backing: the hearts then show the page).
    """
    reach = band + 0.4 * scallop + rim      # how far the doily reaches past the letter

    def effect(g, ink):
        # the edge: scallops whose centers stand on an outline a little inside the band
        base = dilate(ink, band - scallop * 0.6)
        centers = []
        for c in base:
            centers += along(flatten_contour(c, 1.0), scallop * spacing)
        paper = union(base + [circle(q.real, q.imag, scallop) for q in centers])
        # a counter that the paper nearly closed leaves a ragged scrap of ground: fill it
        paper = [c for c in paper if not (contour_area(c) > 0 and thin(c, scallop * 1.3))]

        # Under the paper: its silhouette, a little larger, in the color of the palette's ground. On that
        # ground it does not show; on any other paper it rims the doily and fills the punched hearts.
        backing = dilate(paper, rim) if rim > 0 else []

        # the punched hearts: on an outline in the middle of the band, never touching each other
        clear = effects.inside(dilate(ink, 8.0))
        on_paper = effects.inside(paper)
        holes, placed = [], []
        for c in dilate(ink, band * punch_at):
            for q in along(flatten_contour(c, 1.0), punch * punch_step):
                if any(abs(q - o) < punch * 1.12 for o in placed):
                    continue
                outline = [q + complex(dx, dy) * punch / 2
                           for dx, dy in ((-1.05, 0.3), (1.05, 0.3), (0, -1.0), (-0.5, 0.95), (0.5, 0.95), (0, 0))]
                if any(clear(p) for p in outline) or not all(on_paper(p) for p in outline):
                    continue
                placed.append(q)
                holes.append(heart(q.real, q.imag, punch))
        if eyelet > 0:
            ring = [complex(math.cos(a), math.sin(a)) * scallop * 1.3 for a in (k * math.pi / 6 for k in range(12))]
            for q in centers:
                edge = not all(on_paper(q + d) for d in ring)       # a filled counter has no edge here
                if edge and on_paper(q) and not clear(q) and all(abs(q - o) > punch * 0.55 + eyelet + 6 for o in placed):
                    holes.append(circle(q.real, q.imag, eyelet))
        if holes:
            paper = difference(paper, holes)
        paper = [c for c in paper if abs(contour_area(c)) > 30]

        key = f"lace{sum(map(ord, g.name)) % keys}"
        g.layers = ([("backing", backing)] if backing else []) + [(key, paper), ("letter", ink)]
        g.letter_layer = "letter"

        # The paper sets the spacing: every letter stands the same distance from its neighbors' paper.
        if g._advance is not None:
            # a tabular figure: one advance for all, widened by the doily on both sides
            g._advance += 2 * reach + gap - g.sidebearing("s")
        else:
            side = (reach + gap / 2) / g.sidebearing("s")
            g.frame(None, side, side)

    out = effects.wrapped(recipes, effect, names=names)

    # Combining marks (U+0300 and on) get no doily: they sit over a letter that already has one. Without
    # layers they would take the text color, so a decomposed accent (G + U+0301 for a missing Ǵ) would
    # come out black. In the letter's color it reads as part of the letter.
    def mark(g, ink):
        g.layers = [("letter", ink)]

    return effects.wrapped(out, mark, names=[n for n in recipes if "comb" in n])


def palette(letter, lace, backing):
    """``lace`` is one color, or a list of four colors that the letters take in turn."""
    laces = lace if isinstance(lace, (list, tuple)) else [lace] * 4
    out = {"backing": backing}
    out.update({f"lace{k}": c for k, c in enumerate(laces)})
    out["letter"] = letter
    return out


# Each palette is drawn for a ground, and its backing has the ground's color (or one close to it).
GROUNDS = {"Valentine": "#F4BFCB", "Candy": "#FFF8EE", "Pink": "#B3122E", "Chocolate": "#2B150E"}
PALETTES = {
    "Valentine": palette("#C3142D", "#FFFFFF", "#F4BFCB"),                                   # red card, white doily
    "Candy": palette("#D3203E", ["#F7BFCF", "#F9DF8E", "#BFE5CF", "#D6C6F0"], "#FFFFFF"),    # red print, pastel candy
    "Pink": palette("#E8467C", "#FFFFFF", "#B3122E"),                                       # pink card, white doily
    "Chocolate": palette("#4A2216", "#E2BC6E", "#2B150E"),                                  # chocolate, gold doily
}
