"""breaker: the Great Wave look for whateverfont.

Each letter is a wave. Its crest is white foam whose lower edge runs down into the water in
pointed tongues, hooked claws of foam curl off the top toward the right, the body is Prussian blue
with paler streaks that follow the outline, and a cream halo stands for the paper of the print.

Palette keys, bottom layer first: paper, line, sea, swell, foam, spray.
"""

import math

from whateverfont import effects
from whateverfont.effects import erode, seed_for
from whateverfont.outline import circle, difference, dilate, intersection, rect, union


# ---------------------------------------------------------------- geometry helpers

def _point(seg, t):
    """A point on a line (2 points) or a Bezier segment (3 or 4 points)."""
    pts = list(seg)
    while len(pts) > 1:
        pts = [a + (b - a) * t for a, b in zip(pts, pts[1:])]
    return pts[0]


def _flatten(contours, steps=10):
    """Every contour as a closed list of points."""
    out = []
    for contour in contours:
        pts = []
        for seg in contour:
            n = 1 if len(seg) == 2 else steps
            pts.extend(_point(seg, i / n) for i in range(n))
        if len(pts) > 2:
            out.append(pts)
    return out


def _bounds(polys):
    xs = [p.real for poly in polys for p in poly]
    ys = [p.imag for poly in polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _top_at(polys, x):
    """The highest y of the shape on the vertical line at x (far below when there is none)."""
    best = -1e9
    for poly in polys:
        a = poly[-1]
        for b in poly:
            if (a.real - x) * (b.real - x) <= 0 and a.real != b.real:
                best = max(best, a.imag + (b.imag - a.imag) * (x - a.real) / (b.real - a.real))
            a = b
    return best


def claw(x, y, w, h):
    """A hooked finger of foam: it stands on (x, y), rises h, curls to the right and ends in a point."""
    def at(u, v):
        return complex(x + u * w, y + v * h)

    return [
        (at(-0.46, -0.40), at(-0.52, 0.30), at(-0.36, 0.86), at(0.12, 0.98)),     # up the back
        (at(0.12, 0.98), at(0.60, 1.10), at(1.10, 0.86), at(1.08, 0.24)),         # over, down to the tip
        (at(1.08, 0.24), at(0.98, 0.60), at(0.70, 0.72), at(0.42, 0.62)),         # back under the hook
        (at(0.42, 0.62), at(0.20, 0.54), at(0.30, 0.15), at(0.40, -0.40)),        # down the front
        (at(0.40, -0.40), at(-0.46, -0.40)),
    ]


def tongue(x, y, w, length, lean):
    """A fang of foam that hangs from (x, y) and bends to the right by ``lean``.

    The contour runs clockwise, like every contour here: ``union`` cancels a shape that runs the
    other way where the two overlap.
    """
    tip = complex(x + lean, y - length)
    left, right = complex(x - w / 2, y + 14), complex(x + w / 2, y + 14)
    return [
        (tip, tip + complex(-0.34 * w, 0.16 * length), complex(x - w / 2, y - 0.66 * length), left),
        (left, right),
        (right, complex(x + w / 2, y - 0.26 * length), tip + complex(-0.04 * w, 0.36 * length), tip),
    ]


# ---------------------------------------------------------------- the effect

def _inside(poly, p):
    hit = False
    a = poly[-1]
    for b in poly:
        if (a.imag > p.imag) != (b.imag > p.imag):
            if p.real < a.real + (b.real - a.real) * (p.imag - a.imag) / (b.imag - a.imag):
                hit = not hit
        a = b
    return hit


def _pieces(ink):
    """The separate parts of a letter (the stem and the dot of an i), each with its holes."""
    polys = _flatten(ink)
    pairs = [(c, poly) for c, poly in zip([c for c in ink if len(c)], polys)] if len(polys) == len(ink) else None
    if pairs is None:                                      # a degenerate contour was dropped
        return [(list(ink), polys)]
    depth = [sum(_inside(other, poly[0]) for j, (_, other) in enumerate(pairs) if j != i)
             for i, (_, poly) in enumerate(pairs)]
    pieces = []
    for i, (c, poly) in enumerate(pairs):
        if depth[i] % 2 == 0:
            pieces.append(([c], [poly], i))
    for i, (c, poly) in enumerate(pairs):
        if depth[i] % 2:
            owners = [pc for pc in pieces if depth[pc[2]] == depth[i] - 1 and _inside(pc[1][0], poly[0])]
            if owners:
                owners[0][0].append(c)
                owners[0][1].append(poly)
    return [(cs, ps) for cs, ps, _ in pieces]


#: Small signs get a foam cap and no claws, whatever their height.
CALM = {"period", "comma", "colon", "semicolon", "hyphen", "endash", "emdash", "asterisk", "quoteleft",
        "quoteright", "quotedblleft", "quotedblright", "quotesingle", "quotedbl"}


def breaker(recipes, foam=0.20, rim=15.0, claw_size=(64.0, 100.0), every=140.0, paper=34.0,
            streaks=2, spray=True, seed=0, names=None):
    """Wave letters.

    ``foam`` is the depth of the foam cap as a share of the height of the letter, ``rim`` the
    width of the dark line around the letter, ``claw_size`` the width and height of a claw,
    ``every`` the distance between claws, ``paper`` the width of the cream halo (0 for none) and
    ``streaks`` the number of pale lines in the water.
    """

    def wave(g, rng, contours, polys):
        """One part of a letter as a wave. Returns its line, water, swell, foam and spray."""
        x0, y0, x1, y1 = _bounds(polys)
        height = y1 - max(y0, min(0.0, y1 - 1))            # a descender does not count
        small = g.name in CALM or y1 - y0 < 0.40 * g.cap   # a comma, a quote, the dot of an i
        k = 0.5 if small else 1.0

        # The foam cap: the top of the part, with tongues that run down into the water.
        depth = min(foam * height, 0.40 * (y1 - y0))
        split = y1 - depth
        cap = [rect(x0 - 40, split, x1 + 40, y1 + 40)]
        x = x0 - rng.uniform(0, 50)
        while x < x1 + 40:
            w = rng.uniform(38, 70) * k
            long = rng.random() < 0.34
            cap.append(tongue(x + w / 2, split, w, (rng.uniform(96, 150) if long else rng.uniform(30, 80)) * k,
                              rng.uniform(0.16, 0.42) * w))
            x += w * rng.uniform(0.9, 1.0)
        cap = union(cap)
        body = erode(contours, rim)
        # Keep the foam that hangs from the crest. A tongue may also cross a stroke further down
        # (the bowl of a 5); that piece would float, so it stays water.
        foam_cap = [c for c in intersection(body, cap)
                    if max((p.imag for seg in c for p in seg), default=-1e9) > split - 2]

        # Claws stand on the crest: wherever the top edge is near the highest point.
        claws = []
        dots = []
        if not small:
            cw, ch = claw_size
            near = y1 - 0.10 * g.cap

            def foot_of(x, w):
                return min(_top_at(polys, x - 0.44 * w), _top_at(polys, x), _top_at(polys, x + 0.38 * w))

            sites = []
            x = x0 + 0.62 * cw
            while x <= x1 - 0.95 * cw:
                if foot_of(x, cw) >= near:
                    sites.append(x + min(rng.uniform(0, 10), max(0.0, x1 - 0.95 * cw - x)))
                    x += every * rng.uniform(0.9, 1.12)
                else:
                    x += 8
            if not sites:                                  # a point, like the top of A
                steps = [x0 + i * (x1 - x0) / 60 for i in range(61)]
                peak = [x for x in steps if _top_at(polys, x) >= y1 - 12]
                mid = sum(peak) / len(peak) if peak else (x0 + x1) / 2
                sites.append(min(max(mid - 0.1 * cw, x0 + 0.6 * cw), max(x0 + 0.6 * cw, x1 - 0.9 * cw)))
            for i, x in enumerate(sites):
                s = rng.uniform(0.84, 1.0) if i % 2 else rng.uniform(1.0, 1.16)
                w, h = cw * s, ch * s
                foot = max(foot_of(x, w), y1 - 0.2 * g.cap)
                claws.append(claw(x, foot - 2, w, h))
                # A smaller finger tucked in front of the big one, where there is room.
                x2 = x + 0.62 * w
                if x2 <= x1 - 0.62 * cw and (i + 1 == len(sites) or sites[i + 1] - x > 1.9 * cw) \
                        and foot_of(x2, 0.6 * cw) >= near and rng.random() < 0.8:
                    claws.append(claw(x2, foot_of(x2, 0.6 * cw) - 2, 0.6 * w, 0.62 * h))
                if spray:
                    for _ in range(rng.choice((1, 1, 2))):
                        dots.append(circle(min(x + rng.uniform(0.75, 1.45) * w, x1 + 6),
                                           foot + h * rng.uniform(0.55, 1.2) + 26,
                                           rng.uniform(6.5, 11)))

        line = list(contours)
        if claws:
            line += dilate(union(claws), rim * 0.8)
        white = list(foam_cap) + claws

        # Paler streaks in the water, parallel to the outline of the letter.
        water = difference(body, foam_cap) if foam_cap else body
        swell = []
        step = rim * 1.9
        for i in range(0 if small else streaks):
            outer = erode(contours, rim + step * (i + 0.9))
            inner = erode(contours, rim + step * (i + 0.9) + rim * 0.62)
            if outer:
                swell += difference(outer, inner) if inner else outer
        if swell:
            swell = intersection(union(swell), water)
        return line, water, swell, white, dots

    def effect(g, ink):
        rng = seed_for(g, seed)
        line, water, swell, white, dots = [], [], [], [], []
        for contours, polys in _pieces(ink):
            if not polys:
                continue
            for total, part in zip((line, water, swell, white, dots), wave(g, rng, contours, polys)):
                total += part
        if not line:
            return
        line = union(line)
        # whateverfont kerns a color glyph by its bottom layer. Put the letter and its claws there,
        # under the sheet where they do not show, or the pairs are kerned as if the sheet were ink.
        layers = [("paper", line)]
        plain = union(list(line) + dots)
        sheet = plain
        if paper:
            # Grow, then shrink a little: the sheet gets an even edge. Keep its outer edge only,
            # so the paper also fills the counters.
            try:
                sheet = erode(dilate(plain, paper + 26), 26)
            except Exception:
                sheet = dilate(plain, paper)          # Skia could not shrink it (the ^ of Kanagawa Swell)
            flat = _flatten(sheet)
            if len(flat) == len(sheet):
                sheet = [c for i, c in enumerate(sheet)
                         if not any(_inside(o, flat[i][0]) for j, o in enumerate(flat) if j != i)]
            layers.append(("paper", sheet))
        layers += [("line", line), ("sea", water)]
        if swell:
            layers.append(("swell", swell))
        layers.append(("foam", union(white)))
        if dots:
            layers.append(("spray", dots))
        g.layers = layers
        # Some renderers clip color layers to the box of the plain glyph (whateverfont's own proofs
        # did when this was written). The plain glyph stays a letter, for programs that show no
        # color, and four specks of four units at the outermost points of the sheet stretch its
        # box over every layer. The engine slants the drawing after this effect, so the outermost
        # points are found on the slant.
        lean = math.tan(math.radians(g.p.slant))
        pts = [q for poly in _flatten(sheet) for q in poly]
        specks = []
        for q in (min(pts, key=lambda q: q.real + q.imag * lean), max(pts, key=lambda q: q.real + q.imag * lean),
                  min(pts, key=lambda q: q.imag), max(pts, key=lambda q: q.imag)):
            specks.append(rect(q.real - 2, q.imag - 2, q.real + 2, q.imag + 2))
        effects.redraw(g, list(plain) + specks)

    return effects.wrapped(recipes, effect, names=names)


PRINT = {
    "paper": "#EADBB4",      # the cream sheet
    "line": "#081B33",       # the key block: almost black Prussian blue
    "sea": "#113A66",        # Prussian blue
    "swell": "#6C9BBE",      # the pale blue of the wave's stripes
    "foam": "#FCF8EC",       # unprinted paper, a little whiter than the sheet
    "spray": "#FCF8EC",
}

NIGHT = {
    "paper": "#0A1626",      # a night sky
    "line": "#03080F",
    "sea": "#16487A",
    "swell": "#4E8DBD",
    "foam": "#E8F1F5",       # moonlit foam
    "spray": "#E8F1F5",
}

# The print's colors with no sheet: for a poster that is already cream.
BARE = dict(PRINT, paper="#EADBB400")
