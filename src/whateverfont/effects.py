"""Effects: ways to finish every letter of a set after it is drawn.

An effect takes a recipe set and returns a new one. Each glyph is drawn as
usual, and the effect then works on the result: it cuts bridges for a stencil,
lays brush marks along the strokes, or stacks color layers for a glow::

    from whateverfont import Family, effects, latin

    FAMILY = Family(name="Marquee", recipes=effects.inline(latin()))
    PAINT = Family(name="Impasto", recipes=effects.painted(latin(), colors=5),
                   palettes={"Night": effects.paint_palette("#16233F", ["#1F3A6E", "#2F62A6", "#6FA3D8",
                                                                        "#E9D36B", "#F6EDB2"])})

Effects that change the shape of the outline give static fonts only: a
variable font needs the same points in every master. Color effects set
``g.layers``; give the family ``palettes`` with a color for every key.

To write your own, pass a function to :func:`wrapped`.
"""

from __future__ import annotations

import math
import random
import zlib

import pathops

from .geom import (
    contour_area,
    contour_bounds,
    flatten_contour,
    left,
    reverse_contour,
    seg_length,
    seg_point,
    seg_tangent,
    split_seg,
    transform_contour,
    unit,
)
from .glyph import G, Recipe, Recipes
from .outline import circle, difference, dilate, from_path, intersection, rect, to_path, union
from .stroke import FixedPen

K = 0.5523


# --------------------------------------------------------------------------
# Wrapping a recipe set
# --------------------------------------------------------------------------

def ink(g: G) -> list:
    """What the glyph looks like so far: merged outlines, with its cutouts removed."""
    c = union(g.outlines())
    return difference(c, g.cutouts) if g.cutouts and c else c


def seed_for(g: G, seed: int = 0) -> random.Random:
    """A random source that gives one glyph the same marks in every build."""
    return random.Random(zlib.crc32(g.name.encode()) ^ (seed * 7919))


def wrapped(recipes: Recipes, effect, names=None, static: bool = True) -> Recipes:
    """A copy of ``recipes`` in which ``effect(g, ink)`` runs after each glyph is drawn.

    ``g`` is the builder after the plain recipe ran, and ``ink`` is its merged
    outline. The effect may set ``g.layers`` (color), add to ``g.cutouts``,
    or replace the drawing with :func:`redraw`. ``names`` limits the effect to
    some glyphs; by default it skips combining marks and empty glyphs.
    ``static`` says the result cannot be a master of a variable font.

    An accented letter is drawn plain and gets the effect once, as a whole. A retraced font is different:
    its accented letters are composites, so its marks get the effect as glyphs of their own
    (``recipes.parts``).
    """
    out = recipes.copy()
    parts = getattr(recipes, "parts", False)
    for name in (names or [n for n in recipes if parts or "comb" not in n]):
        if name not in recipes:
            continue
        rec = recipes[name]
        plain = rec.plain or rec.fn

        def draw(g: G, plain=plain):
            plain(g)
            shape = ink(g)
            if shape:
                effect(g, shape)
                g.static_only = g.static_only or static

        out[name] = Recipe(name, draw, rec.unicode, rec.case, plain)
    return out


def redraw(g: G, contours: list):
    """Replace the drawing of ``g`` with finished contours. The width and the spacing stay."""
    if g._frame is None or g._frame[0] is None:
        b = contour_bounds(union(g.outlines()))
        if b:
            # keep the measured width: the new drawing may be larger than the letter
            sides = g._frame[1:] if g._frame is not None else ("s", "s")
            contours = [transform_contour(c, lambda q: q - b[0]) for c in contours]
            g.layers = [(k, [transform_contour(c, lambda q: q - b[0]) for c in cs]) for k, cs in g.layers]
            g._frame = (b[2] - b[0], *sides)
    elif g.p.serif > 0 and g.slab_reach is None:
        # the slabs go with the strokes, so keep how far they reach past the frame
        g.slab_reach = g._past_frame(g._frame[0], contour_bounds(g.outlines()))
    g.strokes = []
    g.cutouts = []
    g.shapes = [("shape", c, None) for c in contours]


def band(contours: list, width: float) -> list:
    """A band ``width`` wide, centered on the outline."""
    path = to_path(contours)
    path.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4.0)
    return union(from_path(path))


def erode(contours: list, amount: float) -> list:
    """Shrink a shape by ``amount`` on every side."""
    if amount <= 0:
        return contours
    cut = band(contours, 2 * amount)
    try:
        return difference(contours, cut)
    except pathops.PathOpsError:
        # Skia sometimes cannot subtract the band from a long, wavy outline (a ribbon-printed Ш). The
        # band's own contours hold the answer: by depth, the outside of the band, its inner edge (the
        # edge of what is left), the outer edge of the band round a counter (a hole in what is left),
        # the middle of the counter, and so on. Depths 1 and 2 of every 4 are what is left.
        from .outline import depths
        return [reverse_contour(c) for c, d in zip(cut, depths(cut)) if d % 4 in (1, 2)]


def inside(contours: list):
    """A function that says whether a point is inside merged contours."""
    polys = [flatten_contour(c, 2.0) for c in contours]
    boxes = [(min(p.real for p in poly), max(p.real for p in poly), min(p.imag for p in poly),
              max(p.imag for p in poly)) for poly in polys]

    def test(q) -> bool:
        hit = False
        x, y = (q.real, q.imag) if isinstance(q, complex) else q
        for poly, (x0, x1, y0, y1) in zip(polys, boxes):
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            n = len(poly)
            for i in range(n):
                a, b = poly[i], poly[(i + 1) % n]
                if (a.imag > y) != (b.imag > y) and x < a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag):
                    hit = not hit
        return hit
    return test


# --------------------------------------------------------------------------
# Shape effects: one color, static fonts
# --------------------------------------------------------------------------

def stencil(recipes: Recipes, gap: float = 0.30, least: float = 20.0, names=None) -> Recipes:
    """Cut a vertical bridge through every closed counter, as a stencil needs.

    ``gap`` is the bridge width as a share of the stem, and ``least`` its minimum in units.
    """
    def effect(g: G, shape: list):
        w = max(least, gap * g.sw)
        b = contour_bounds(shape)
        centers: list = []
        for hole in (c for c in shape if contour_area(c) > 0):
            hb = contour_bounds([hole])
            cx = (hb[0] + hb[2]) / 2
            if all(abs(cx - other) > w * 1.5 for other in centers):
                centers.append(cx)
        for cx in centers:
            g.cutouts.append(rect(cx - w / 2, b[1] - 60, cx + w / 2, b[3] + 60))
    return wrapped(recipes, effect, names)


def inline(recipes: Recipes, width: float = 0.20, rim: float = 0.22, names=None) -> Recipes:
    """Engrave a white line down the middle of every stroke.

    ``width`` is the line and ``rim`` the least ink left around it, both as a share of the stem.
    Use it on heavy weights: the stem must be wider than the line and two rims.
    """
    def effect(g: G, shape: list):
        half = max(4.0, width * g.sw / 2)
        lines = []
        for s in g.strokes:
            for seg in s.segments():
                lines.append(_ribbon(seg, half))
        keep = erode(shape, max(6.0, rim * g.sw))
        if lines and keep:
            cut = intersection(union(lines), keep)
            g.cutouts += [c for c in cut if abs(contour_area(c)) > 40]
    return wrapped(recipes, effect, names)


def _ribbon(seg, half: float) -> list:
    """One skeleton segment as a thin band with round ends."""
    return _mark(seg[0], seg[-1], seg_tangent(seg, 0), seg_tangent(seg, 1), half, half, half,
                 seg if len(seg) == 4 else None)


def outlined(recipes: Recipes, width: float = 0.24, least: float = 12.0, names=None) -> Recipes:
    """Hollow letters: only a line around the edge is left. ``width`` is a share of the stem."""
    def effect(g: G, shape: list):
        t = max(least, width * g.sw)
        g.cutouts += erode(shape, t)
    return wrapped(recipes, effect, names)


def shadow(recipes: Recipes, dx: float = 34.0, dy: float = -34.0, gap: float = 12.0, names=None) -> Recipes:
    """A block shadow, drawn in the same color and kept apart from the letter by a thin white line."""
    def effect(g: G, shape: list):
        side = difference(extrusion(shape, dx, dy), dilate(shape, gap)) if gap > 0 else extrusion(shape, dx, dy)
        redraw(g, union(shape + [c for c in side if abs(contour_area(c)) > 30]))
    return wrapped(recipes, effect, names)


def extrusion(contours: list, dx: float, dy: float) -> list:
    """The area a shape sweeps when it slides by (dx, dy): the side of a block letter."""
    d = complex(dx, dy)
    # The shape at both ends of the slide, counters included: a counter larger than the slide stays open.
    parts = list(contours) + [transform_contour(c, lambda q: q + d) for c in contours]
    for c in contours:
        pts = flatten_contour(c, 1.5)
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            quad = [(a, b), (b, b + d), (b + d, a + d), (a + d, a)]
            if abs(contour_area(quad)) < 1.0:
                continue
            parts.append(reverse_contour(quad) if contour_area(quad) > 0 else quad)
    return union(parts)


def stripes(recipes: Recipes, count: int = 5, gap: float = 0.34, low: float = 0.0, high: float = 0.52,
            names=None) -> Recipes:
    """Cut ``count`` horizontal white lines through the letters, between two heights.

    ``low`` and ``high`` are shares of the cap height. ``gap`` is the white as a share of each step.
    The lines get thicker toward the bottom, like the speed lines of a 1970s logo.
    """
    def effect(g: G, shape: list):
        b = contour_bounds(shape)
        y0, y1 = g.cap * low, g.cap * high
        step = (y1 - y0) / count
        for i in range(count):
            t = step * gap * (1.35 - 0.7 * i / max(1, count - 1))
            y = y0 + step * (i + 0.5)
            g.cutouts.append(rect(b[0] - 20, y - t / 2, b[2] + 20, y + t / 2))
    return wrapped(recipes, effect, names)


def rough(recipes: Recipes, amount: float = 5.0, scale: float = 130.0, seed: int = 0, names=None) -> Recipes:
    """Wobble the outline a little, as if the letters were cut by hand and printed.

    ``amount`` is how far a point may move, and ``scale`` the length of one wave, in units.
    """
    def effect(g: G, shape: list):
        rng = seed_for(g, seed)
        ph = [rng.uniform(0, math.tau) for _ in range(6)]
        f = math.tau / scale

        def warp(q: complex) -> complex:
            x, y = q.real, q.imag
            dx = math.sin(x * f * 0.9 + y * f * 1.3 + ph[0]) + 0.5 * math.sin(x * f * 2.3 - y * f * 1.7 + ph[1])
            dy = math.sin(x * f * 1.2 - y * f * 0.8 + ph[2]) + 0.5 * math.sin(x * f * 1.9 + y * f * 2.6 + ph[3])
            return q + complex(dx, dy) * amount * 0.66

        out = []
        for c in shape:
            pieces = []
            for seg in c:
                n = max(1, int(seg_length(seg) / (scale * 0.35)))
                rest = seg
                for k in range(n, 1, -1):          # cut long segments so that they can bend
                    head, rest = split_seg(rest, 1.0 / k)
                    pieces.append(head)
                pieces.append(rest)
            out.append([tuple(warp(q) for q in (seg if len(seg) == 4 else
                                                (seg[0], seg[0] + (seg[1] - seg[0]) / 3,
                                                 seg[0] + (seg[1] - seg[0]) * 2 / 3, seg[1])))
                        for seg in pieces])
        redraw(g, out)
    return wrapped(recipes, effect, names)


# --------------------------------------------------------------------------
# Color effects
# --------------------------------------------------------------------------

def glow(recipes: Recipes, size: float = 80.0, names=None) -> Recipes:
    """A lit tube: the letter, a bright halo, and three rings of light. Keys: glow1-3, halo, tube."""
    def effect(g: G, shape: list):
        g.layers = [("glow1", dilate(shape, size)), ("glow2", dilate(shape, size * 0.65)),
                    ("glow3", dilate(shape, size * 0.38)), ("halo", dilate(shape, size * 0.16)), ("tube", shape)]
    return wrapped(recipes, effect, names)


def glow_palette(color: str, tube: str = "#FFFFFF") -> dict:
    """Colors for :func:`glow`: rings of ``color`` that get more solid toward the tube."""
    return {"glow1": color + "24", "glow2": color + "38", "glow3": color + "5C", "halo": color + "E6",
            "tube": tube}


def layered_shadow(recipes: Recipes, dx: float = 30.0, dy: float = -30.0, names=None) -> Recipes:
    """A block shadow in its own color. Keys: side, face."""
    def effect(g: G, shape: list):
        g.layers = [("side", extrusion(shape, dx, dy)), ("face", shape)]
    return wrapped(recipes, effect, names)


def banded(recipes: Recipes, bands: int = 5, low: float = -0.02, high: float = 1.02, names=None) -> Recipes:
    """Horizontal bands of color, bottom to top. Keys: band0 (the lowest) to band{n-1}."""
    def effect(g: G, shape: list):
        b = contour_bounds(shape)
        y0, y1 = g.cap * low, g.cap * high
        step = (y1 - y0) / bands
        g.layers = []
        for i in range(bands):
            lo = b[1] - 5 if i == 0 else y0 + step * i
            hi = b[3] + 5 if i == bands - 1 else y0 + step * (i + 1)
            part = intersection(shape, [rect(b[0] - 5, lo, b[2] + 5, hi)])
            if part:
                g.layers.append((f"band{i}", part))
    return wrapped(recipes, effect, names)


def mosaic(recipes: Recipes, cell: float = 64.0, gap: float = 7.0, colors: int = 4, jitter: float = 0.22,
           tone="random", seed: int = 0, names=None) -> Recipes:
    """Letters set with small tiles. Keys: grout, and c0 to c{colors-1}.

    ``cell`` is the tile size, ``gap`` the grout between tiles, ``jitter`` how uneven the tiles are.
    """
    def effect(g: G, shape: list):
        rng = seed_for(g, seed)
        b = contour_bounds(shape)
        nx = max(1, round((b[2] - b[0]) / cell))
        ny = max(1, round((b[3] - b[1]) / cell))
        sx, sy = (b[2] - b[0]) / nx, (b[3] - b[1]) / ny
        # jittered corners, shared between neighbors, so the grout keeps one width
        corner = {}
        for i in range(nx + 1):
            for j in range(ny + 1):
                jx = 0.0 if i in (0, nx) else rng.uniform(-jitter, jitter) * sx
                jy = 0.0 if j in (0, ny) else rng.uniform(-jitter, jitter) * sy
                corner[i, j] = complex(b[0] + i * sx + jx, b[1] + j * sy + jy)
        marks = []
        for i in range(nx):
            for j in range(ny):
                q = [corner[i, j], corner[i, j + 1], corner[i + 1, j + 1], corner[i + 1, j]]
                mid = sum(q) / 4
                q = [p + unit(mid - p) * min(gap * 0.7, abs(mid - p) * 0.45) for p in q]
                t = _tone(tone, 0.0, 0.0, (mid.real - b[0]) / max(1.0, b[2] - b[0]),
                          (mid.imag - b[1]) / max(1.0, b[3] - b[1]), rng)
                marks.append(([(q[k], q[(k + 1) % 4]) for k in range(4)], t))
        g.layers = [("grout", shape)] + paint_layers(marks, colors, rng, passes=1, clip=shape, jitter=0.0)
    return wrapped(recipes, effect, names)


def dotted(recipes: Recipes, size: float = 30.0, spacing: float = 1.12, colors: int = 4, tone="random",
           base: bool = True, seed: int = 0, names=None) -> Recipes:
    """Letters made of whole dots, like a pointillist painting. Keys: base, and c0 to c{colors-1}."""
    def effect(g: G, shape: list):
        rng = seed_for(g, seed)
        b = contour_bounds(shape)
        within = inside(erode(shape, size * 0.30) or shape)
        step = size * spacing
        marks = []
        row = 0
        y = b[1] + step / 2
        while y < b[3]:
            x = b[0] + (step / 2 if row % 2 else step)
            while x < b[2]:
                q = complex(x + rng.uniform(-0.16, 0.16) * step, y + rng.uniform(-0.16, 0.16) * step)
                if within(q):
                    t = _tone(tone, 0.0, 0.0, (q.real - b[0]) / max(1.0, b[2] - b[0]),
                              (q.imag - b[1]) / max(1.0, b[3] - b[1]), rng)
                    marks.append((circle(q.real, q.imag, size / 2 * rng.uniform(0.86, 1.1)), t))
                x += step
            y += step * 0.87
            row += 1
        g.layers = ([("base", shape)] if base else []) + paint_layers(marks, colors, rng, passes=1, jitter=0.0)
    return wrapped(recipes, effect, names)


# --------------------------------------------------------------------------
# Paint
# --------------------------------------------------------------------------

def _mark(a: complex, b: complex, d0: complex, d1: complex, r0: float, rm: float, r1: float, cubic=None) -> list:
    """One brush mark from ``a`` to ``b``: a bent band with round ends, drawn clockwise.

    ``d0`` and ``d1`` are the directions at the two ends, and r0, rm, r1 the half-widths at the start,
    the middle and the end.
    """
    length = abs(b - a)
    if cubic is None:
        h1, h2 = a + d0 * length / 3, b - d1 * length / 3
    else:
        h1, h2 = cubic[1], cubic[2]
    n0, n1 = left(d0), left(d1)
    nm = left(unit(b - a) or d0)
    return [
        (a + n0 * r0, h1 + nm * rm, h2 + nm * rm, b + n1 * r1),
        (b + n1 * r1, b + n1 * r1 + d1 * K * r1, b + d1 * r1 + n1 * K * r1, b + d1 * r1),
        (b + d1 * r1, b + d1 * r1 - n1 * K * r1, b - n1 * r1 + d1 * K * r1, b - n1 * r1),
        (b - n1 * r1, h2 - nm * rm, h1 - nm * rm, a - n0 * r0),
        (a - n0 * r0, a - n0 * r0 - d0 * K * r0, a - d0 * r0 - n0 * K * r0, a - d0 * r0),
        (a - d0 * r0, a - d0 * r0 + n0 * K * r0, a + n0 * r0 - d0 * K * r0, a + n0 * r0),
    ]


def brush_mark(center: complex, direction: complex, length: float, width: float, bend: float = 0.0,
               taper: tuple = (0.72, 1.0, 0.55)) -> list:
    """A single brush mark. ``bend`` turns it by that many degrees from its start to its end."""
    d = unit(direction) or 1 + 0j
    turn = complex(math.cos(math.radians(bend / 2)), math.sin(math.radians(bend / 2)))
    d0, d1 = d / turn, d * turn
    r = width / 2
    reach = max(1.0, length / 2 - r)
    return _mark(center - d * reach, center + d * reach, d0, d1, r * taper[0], r * taper[1], r * taper[2])


def _tone(tone, along: float, across: float, x: float, y: float, rng) -> float:
    """A number from 0 (the first color) to 1 (the last) for a mark.

    ``along`` is the distance along the stroke in units, ``across`` runs from -1 to 1 over its
    width, and x, y run from 0 to 1 over the glyph.
    """
    if callable(tone):
        return tone(along, across, x, y, rng)
    if tone == "light":                      # lit from the top left
        return 0.5 + 0.55 * (y - 0.5) - 0.35 * (x - 0.5)
    if tone == "across":                     # bright in the middle of the stroke
        return 1.0 - abs(across)
    if tone == "along":                      # streaks that follow the stroke
        return 0.5 + 0.5 * math.sin(along / 46.0 + across * 2.4)
    if tone == "rise":                       # dark at the foot, bright at the head
        return y
    return rng.random()


def stroke_marks(g: G, dab: tuple = (84.0, 30.0), density: float = 1.0, wobble: float = 10.0, tone="along",
                 rng=None, bend: float = 14.0) -> list:
    """Brush marks laid along the skeleton of a glyph, in rows across each stroke.

    Returns a list of (contour, tone). The marks follow the pen, so a round letter is painted round.
    """
    rng = rng or seed_for(g)
    length, width = dab
    b = contour_bounds(g.outlines()) or (0.0, 0.0, 1.0, 1.0)
    bw, bh = max(1.0, b[2] - b[0]), max(1.0, b[3] - b[1])
    out = []
    for s in g.strokes:
        pen = FixedPen(s.fixed) if s.fixed is not None else g.pen
        n = len(s.nodes)
        traveled = rng.uniform(0, 200)
        for i, seg in enumerate(s.segments()):
            wa, wb = s.nodes[i].w, s.nodes[(i + 1) % n].w
            seg_len = seg_length(seg)
            steps = max(1, round(seg_len * density / (length * 0.46)))
            for k in range(steps):
                u = (k + rng.uniform(0.2, 0.8)) / steps
                p = seg_point(seg, u)
                t = seg_tangent(seg, u) or 1 + 0j
                half = pen.half(t) * s.scale * (wa + (wb - wa) * u)
                rows = max(1, round(2 * half * density / (width * 0.62)))
                for r in range(rows):
                    v = ((r + 0.5) / rows) * 2 - 1
                    reach = max(0.0, half - width * 0.30)
                    c = p + left(t) * v * reach + complex(rng.gauss(0, 3), rng.gauss(0, 3))
                    turn = math.radians(rng.gauss(0, wobble))
                    d = t * complex(math.cos(turn), math.sin(turn))
                    out.append((brush_mark(c, d, length * rng.uniform(0.7, 1.2), width * rng.uniform(0.8, 1.2),
                                           rng.gauss(0, bend)),
                                _tone(tone, traveled + seg_len * u, v, (c.real - b[0]) / bw,
                                      (c.imag - b[1]) / bh, rng)))
            traveled += seg_len
    # dots and other filled shapes: short marks around their middle
    for _, contour, _ in g.shapes:
        sb = contour_bounds([contour])
        if sb is None:
            continue
        mid = complex((sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2)
        r = max(sb[2] - sb[0], sb[3] - sb[1]) / 2
        for k in range(max(4, round((r / (width * 0.42)) ** 2 * density))):
            a = rng.uniform(0, math.tau)
            c = mid + complex(math.cos(a), math.sin(a)) * r * math.sqrt(rng.uniform(0.0, 0.62))
            out.append((brush_mark(c, complex(-math.sin(a), math.cos(a)), min(length, r * 1.5), min(width, r),
                                   rng.gauss(0, bend)),
                        _tone(tone, a * r, 0.0, (c.real - b[0]) / bw, (c.imag - b[1]) / bh, rng)))
    return out


def field_marks(box: tuple, flow, spacing: tuple = (52.0, 30.0), dab: tuple = (78.0, 26.0), tone="random",
                rng=None, bend: float = 12.0, keep=None) -> list:
    """Brush marks that fill a rectangle and follow a direction field: a sky, water, a field of wheat.

    ``box`` is (x0, y0, x1, y1). ``flow(p)`` returns the direction at a point. ``tone`` may be a
    function of (along, across, x, y, rng) with x and y from 0 to 1 over the box. ``keep(p)`` says
    whether to put a mark at a point.
    """
    rng = rng or random.Random(0)
    x0, y0, x1, y1 = box
    out = []
    row = 0
    y = y0 + spacing[1] / 2
    while y < y1:
        x = x0 + (spacing[0] / 2 if row % 2 else 0.0)
        while x < x1 + spacing[0] / 2:
            c = complex(x + rng.uniform(-0.3, 0.3) * spacing[0], y + rng.uniform(-0.3, 0.3) * spacing[1])
            if keep is None or keep(c):
                d = unit(flow(c)) or 1 + 0j
                # the bend follows the field: look a little ahead
                ahead = unit(flow(c + d * dab[0] * 0.5)) or d
                turn = math.degrees(math.atan2(d.real * ahead.imag - d.imag * ahead.real,
                                               d.real * ahead.real + d.imag * ahead.imag))
                out.append((brush_mark(c, d, dab[0] * rng.uniform(0.75, 1.2), dab[1] * rng.uniform(0.8, 1.2),
                                       turn * 2 + rng.gauss(0, bend * 0.4)),
                            _tone(tone, x, 0.0, (c.real - x0) / max(1.0, x1 - x0), (c.imag - y0) / max(1.0, y1 - y0), rng)))
            x += spacing[0]
        y += spacing[1]
        row += 1
    return out


def paint_layers(marks: list, colors: int, rng=None, passes: int = 2, clip=None, jitter: float = 0.16,
                 prefix: str = "c") -> list:
    """Sort marks into color layers. Returns [(key, contours)] with keys c0 to c{colors-1}.

    Each mark is (contour, tone); the tone picks the color, with a little chance mixed in. The marks
    go down in ``passes`` rounds, so the colors lie over and under one another as wet paint does.
    ``clip`` keeps the paint inside a shape.
    """
    rng = rng or random.Random(0)
    sorted_marks: dict = {}
    for contour, t in marks:
        idx = int(max(0.0, min(0.999, t + (rng.gauss(0, jitter) if jitter else 0.0))) * colors)
        sorted_marks.setdefault((rng.randrange(passes), idx), []).append(contour)
    layers = []
    for key in sorted(sorted_marks):
        shape = union(sorted_marks[key])
        if clip is not None and shape:
            shape = intersection(shape, clip)
        shape = [c for c in shape if abs(contour_area(c)) > 30]
        if shape:
            layers.append((f"{prefix}{key[1]}", shape))
    return layers


def painted(recipes: Recipes, colors: int = 5, dab: tuple = (84.0, 30.0), density: float = 1.0,
            wobble: float = 10.0, tone="along", passes: int = 2, edge: float = 7.0, base: bool = True,
            seed: int = 0, names=None) -> Recipes:
    """Letters painted with short brush marks that follow the pen. Keys: base, and c0 to c{colors-1}.

    ``dab`` is the length and the width of a mark. ``tone`` picks the color of each mark: "along"
    (streaks that follow the stroke), "across" (bright in the middle), "light" (lit from the top
    left), "rise" (dark feet, bright heads), "random", or a function. ``edge`` lets the paint pass
    the outline by that many units, which gives the letter a painted edge. ``base`` puts the plain
    letter under the paint, so no gap shows the page.
    """
    def effect(g: G, shape: list):
        rng = seed_for(g, seed)
        marks = stroke_marks(g, dab, density, wobble, tone, rng)
        clip = dilate(shape, edge) if edge > 0 else shape
        g.layers = ([("base", shape)] if base else []) + paint_layers(marks, colors, rng, passes, clip)
    return wrapped(recipes, effect, names)


def paint_palette(base: str, colors: list) -> dict:
    """A palette for :func:`painted`, :func:`dotted` or :func:`mosaic`: the under-color, then c0, c1, ..."""
    out = {"base": base, "grout": base}
    out.update({f"c{i}": c for i, c in enumerate(colors)})
    return out
