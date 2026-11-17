"""Aviary: a picture font of birds, built from circles and straight lines.

The system
----------
- A bird is a stack of flat pieces. Each piece is a disc, a hull of two discs (a teardrop when one disc
  is a point), a lens or crescent of two arcs, Moss's egg, a ring sector, a polygon or a band, or a
  boolean of those. There are no free curves.
- A piece that sits on another leaves a gap of paper ``GAP`` units wide around itself, as if it were cut
  from colored paper and inlaid. Cut lines (feather edges) are ``GAP`` wide too.
- Every color is one of a shared set of palette keys (``birds.KEYS``).
- One eye: a cream disc with an ink pupil. One leg: a straight band ``LEG`` wide with one foot.

``Bird`` collects the pieces. ``Bird.layers()`` gives the color layers (one per key and tier),
``Bird.mono()`` the one-color drawing, in which pale marks inside the bird are cut out, and
``bird_recipes(..., style="line")`` draws every piece as an outline.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from functools import lru_cache

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, reverse_contour, transform_contour
from whateverfont.glyph import Recipe, Recipes
from whateverfont.outline import circle, difference, dilate, intersection, union

GAP = 12.0          # the paper between two pieces, and the width of a cut line
LEG = 13.0          # legs and toes
SIDE = 46.0         # white on each side of a bird

# --------------------------------------------------------------------------------------------- geometry


def pol(deg: float, r: float = 1.0) -> complex:
    """The point at ``deg`` degrees on a circle of radius ``r`` around the origin."""
    return cmath.rect(r, math.radians(deg))


def ang(v: complex) -> float:
    return math.degrees(cmath.phase(v))


def P(x, y=None) -> complex:
    if y is None:
        return x if isinstance(x, complex) else complex(*x)
    return complex(x, y)


def cw(contour):
    """The contour running clockwise (ink)."""
    return reverse_contour(contour) if contour_area(contour) > 0 else contour


def _arc(c: complex, r: float, a0: float, sweep: float):
    """Cubic segments of an arc of radius ``r`` from angle ``a0``, turning ``sweep`` degrees (+ is ccw)."""
    n = max(1, math.ceil(abs(sweep) / 90 - 1e-9))
    t = sweep / n
    k = 4 / 3 * math.tan(math.radians(t) / 4)
    out = []
    for i in range(n):
        a, b = a0 + t * i, a0 + t * (i + 1)
        p0, p3 = c + pol(a, r), c + pol(b, r)
        out.append((p0, p0 + pol(a + 90, r * k), p3 - pol(b + 90, r * k), p3))
    return out


class Path:
    """A closed contour made of straight lines and circular arcs."""

    def __init__(self, start):
        self.start = self.p = P(start)
        self.segs = []

    def to(self, q):
        q = P(q)
        if abs(q - self.p) > 1e-6:
            self.segs.append((self.p, q))
        self.p = q
        return self

    def arc(self, c, sweep: float):
        """Turn around center ``c`` by ``sweep`` degrees (+ is counter-clockwise)."""
        c = P(c)
        segs = _arc(c, abs(self.p - c), ang(self.p - c), sweep)
        segs[0] = (self.p,) + segs[0][1:]
        self.segs += segs
        self.p = segs[-1][-1]
        return self

    def close(self):
        if self.segs:
            last = self.segs[-1]
            if abs(last[-1] - self.start) < 0.5:
                self.segs[-1] = last[:-1] + (self.start,)
            else:
                self.segs.append((self.p, self.start))
        return cw(self.segs)


def disc(c, r: float):
    c = P(c)
    return circle(c.real, c.imag, r)


def poly(*pts):
    pts = [P(p) for p in pts]
    return cw([(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))])


def hull(c1, r1: float, c2, r2: float = 0.0):
    """Two discs joined by their outer tangents. With ``r2 = 0`` it is a teardrop pointing at ``c2``."""
    c1, c2 = P(c1), P(c2)
    d = c2 - c1
    if abs(d) <= abs(r1 - r2) + 1e-6:
        return disc(c1, r1) if r1 >= r2 else disc(c2, r2)
    phi = ang(d)
    beta = math.degrees(math.acos((r1 - r2) / abs(d)))
    path = Path(c1 + pol(phi + beta, r1)).to(c2 + pol(phi + beta, r2))
    if r2 > 0:
        path.arc(c2, -2 * beta)
    path.to(c1 + pol(phi - beta, r1))
    path.arc(c1, -(360 - 2 * beta))
    return path.close()


def lens(p, q, left: float, right: float | None = None):
    """A shape between two points made of two circular arcs.

    ``left`` and ``right`` are how far each arc bulges from the chord, on the left and on the right of the
    direction p -> q. A bulge of 0 is a straight side (a segment of a disc). A negative bulge is concave:
    ``lens(p, q, 60, -25)`` is a crescent, the shape of a swept wing.
    """
    p, q = P(p), P(q)
    right = left if right is None else right
    a = abs(q - p) / 2
    path = Path(p)
    for (s, e), h in (((p, q), left), ((q, p), right)):
        if abs(h) <= 1e-6:
            path.to(e)
            continue
        sign = 1 if h > 0 else -1
        h = abs(h)
        d = (e - s) / abs(e - s)
        n = d * 1j * sign
        R = (a * a + h * h) / (2 * h)
        c = (s + e) / 2 + n * (h - R)
        theta = math.degrees(math.atan2(a, R - h))
        path.arc(c, -2 * theta * sign)
    return path.close()


def ring(c, r0: float, r1: float, a0: float, a1: float):
    """A ring sector between radii r0 < r1, from angle a0 to a1 (counter-clockwise if a1 > a0)."""
    c = P(c)
    path = Path(c + pol(a0, r1)).arc(c, a1 - a0).to(c + pol(a1, r0)).arc(c, a0 - a1)
    return path.close()


def band(p, q, w: float):
    """A straight band from p to q, ``w`` wide, with square ends."""
    p, q = P(p), P(q)
    n = (q - p) / abs(q - p) * 1j * w / 2
    return poly(p + n, q + n, q - n, p - n)


def rod(p, q, w: float):
    """A straight band with round ends."""
    return hull(p, w / 2, q, w / 2)


def egg(c, r: float, deg: float = 90.0):
    """Moss's egg: four tangent arcs on a circle of radius ``r`` at ``c``, its point toward ``deg``.

    A half circle below the diameter, two arcs of radius 2r from the ends of the diameter, and a small
    arc of radius r(2 - sqrt 2) on top. It is 2r wide and 2.59r long.
    """
    c = P(c)
    u = pol(deg - 90)                         # along the diameter, so the point is at +90 from it
    a, b, d = c - u * r, c + u * r, c + u * 1j * r
    path = Path(a).arc(b, -45).arc(d, -90).arc(a, -45).arc(c, -180)
    return path.close()


def leg(hip, foot, toe: float = 40.0, back: float = 20.0, w: float = LEG):
    """A straight leg from the hip down to a foot standing on y = foot.imag: one toe forward, one back."""
    hip, foot = P(hip), P(foot)
    f = complex(foot.real, foot.imag + w / 2)
    return [band(hip, f, w), rod(f - back, f + toe, w)]


def wedge(c, r: float, a0: float, a1: float):
    """A slice of a disc, from angle a0 to a1 counter-clockwise."""
    c = P(c)
    return Path(c).to(c + pol(a0, r)).arc(c, a1 - a0).close()


def side(p, deg: float, size: float = 4000.0):
    """The half-plane to the left of the line through ``p`` in direction ``deg``."""
    p = P(p)
    d, n = pol(deg, size), pol(deg + 90, size)
    return poly(p - d, p + d, p + d + n, p - d + n)


def crescent(c1, r1: float, c2, r2: float):
    """Disc 1 with disc 2 taken away."""
    return difference([disc(c1, r1)], [disc(c2, r2)])


def lines(region, origin, deg: float, step: float, width: float = GAP, count: int = 40):
    """Parallel bands in direction ``deg``, ``step`` apart, through ``origin``, clipped to ``region``."""
    origin = P(origin)
    d, n = pol(deg), pol(deg + 90)
    out = []
    for i in range(-count, count + 1):
        o = origin + n * step * i
        out.append(band(o - d * 3000, o + d * 3000, width))
    return intersection(shapes(region), union(out))


def shapes(x) -> list:
    """A list of contours from a contour, a list of contours, or nested lists of them."""
    if not x:
        return []
    if isinstance(x[0], tuple):
        return [x]
    out = []
    for item in x:
        out += shapes(item)
    return out


def clip(a, b):
    return intersection(shapes(a), shapes(b))


def cut(a, b):
    return difference(shapes(a), shapes(b))


def merge(*xs):
    return union(shapes(list(xs)))


# ------------------------------------------------------------------------------------------------ a bird


@dataclass
class Piece:
    shape: list
    key: str | None        # palette key; None for a cut line, which is not drawn
    gap: bool = True       # leave paper around this piece in the pieces under it
    mono: bool | str = True  # in the one-color font: ink (True), cut out (False) or an outline ("line")
    pattern: bool = False  # dots, bars or scallops: printed solid on the outline style


class Bird:
    """Pieces in drawing order, bottom first. Coordinates are font units, facing right, ground at y = 0."""

    def __init__(self, name: str):
        self.name = name
        self.pieces: list[Piece] = []

    def add(self, shape, key: str, gap: bool = True, mono: bool | str = True, pattern: bool = False):
        s = union(shapes(shape))
        if s:
            self.pieces.append(Piece(s, key, gap, mono, pattern))
        return s

    def cut(self, shape):
        """A cut line: paper through every piece under it."""
        s = union(shapes(shape))
        if s:
            self.pieces.append(Piece(s, None, False))
        return s

    def eye(self, c, r: float = 19.0, pupil: float | None = None, ring_key: str = "cream"):
        c = P(c)
        self.add(disc(c, r), ring_key, gap=False, mono=False)
        self.add(disc(c + r * 0.12, pupil or r * 0.56), "ink", gap=False)

    def shift(self, dx: float, dy: float):
        """Move every piece drawn so far (a flying bird to its height)."""
        move = lambda q: q + complex(dx, dy)
        for pc in self.pieces:
            pc.shape = [transform_contour(c, move) for c in pc.shape]

    # -- assembly -------------------------------------------------------------------------------------
    def flat(self):
        """[(piece, visible contours, tier)], bottom first. Pieces of tier 0 overlap nothing."""
        out, cutters = [], []
        for pc in reversed(self.pieces):
            vis = difference(pc.shape, cutters) if cutters else pc.shape
            vis = [c for c in vis if abs(contour_area(c)) > 6]
            out.append([pc, vis, 0])
            if pc.key is None:
                cutters = union(cutters + pc.shape)
            elif pc.gap:
                cutters = union(cutters + dilate(pc.shape, GAP))
        out.reverse()
        placed = []
        for item in out:
            pc, vis, _ = item
            if pc.key is None or not vis:
                continue
            tier = 0
            if not pc.gap:
                box = contour_bounds(vis)
                for other, otier in placed:
                    ob = contour_bounds(other)
                    if ob[0] > box[2] or ob[2] < box[0] or ob[1] > box[3] or ob[3] < box[1]:
                        continue
                    if intersection(vis, other):
                        tier = max(tier, otier + 1)
            item[2] = tier
            placed.append((vis, tier))
        return [tuple(i) for i in out if i[0].key is not None and i[1]]

    def layers(self, flat=None):
        flat = flat or self.flat()
        out = []
        for tier in range(max(t for _, _, t in flat) + 1):
            groups: dict = {}
            for pc, vis, t in flat:
                if t == tier:
                    groups.setdefault(pc.key, []).extend(vis)
            out += [(k, union(cs)) for k, cs in groups.items()]
        return out

    def mono(self, flat=None, patterns: bool = True):
        """One color: pieces are ink, cut out (``mono=False``) or drawn as an outline (``mono="line"``)."""
        flat = flat or self.flat()
        ink: list = []
        for pc, vis, _ in flat:
            if pc.pattern and not patterns:
                continue
            if pc.mono == "line":
                ink = difference(ink, vis)
                ink = union(ink + intersection(vis, effects.band(vis, 2 * LEG)))
            elif pc.mono:
                ink = union(ink + vis)
            else:
                ink = difference(ink, vis)
        return ink


# ---------------------------------------------------------------------------------------------- recipes


LINE = 11.0        # the pen of the outline style


@lru_cache(maxsize=None)
def _bird(name: str, build):
    bird = Bird(name)
    build(bird)
    return bird, bird.flat()


@lru_cache(maxsize=None)
def _drawn(name: str, build):
    bird, flat = _bird(name, build)
    return bird.layers(flat), bird.mono(flat)


@lru_cache(maxsize=None)
def _outlined(name: str, build):
    """Every piece of the one-color drawing as an outline, with the patterns printed solid: a coloring book."""
    bird, flat = _bird(name, build)
    plain = bird.mono(flat, patterns=False)
    rims = intersection(plain, effects.band(plain, 2 * LINE))
    marks = [c for pc, vis, _ in flat if pc.pattern for c in vis]
    return union(rims + marks)


def _recipe(name: str, build, mirror: bool, style: str):
    def recipe(g):
        layers, mono = _drawn(name, build)
        if style == "line":
            mono = _outlined(name, build)
        x0, _, x1, _ = contour_bounds(mono + [c for _, cs in layers for c in cs])
        width = x1 - x0 + 2 * SIDE
        if mirror:
            f = lambda c: reverse_contour(transform_contour(c, lambda q: complex(x1 + SIDE - q.real, q.imag)))
        else:
            f = lambda c: transform_contour(c, lambda q: complex(q.real - x0 + SIDE, q.imag))
        for c in mono:
            g.shape(f(c))
        if style == "color":
            g.layers = [(k, [f(c) for c in cs]) for k, cs in layers]
        g.frame(width, 0, 0)
    return recipe


FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


def bird_recipes(birds: dict, extras: dict | None = None, style: str = "color") -> Recipes:
    """A to Z facing right and a to z facing left, from {letter: (name, build function)}.

    ``style`` is "color" (layers, over the one-color drawing), "solid" (one color) or "line" (outlines).
    ``extras`` draws other characters the same way, facing one way only: {"0": (name, build), ...}.
    """
    r = Recipes()

    def space(g):
        g.frame(0, 0, 0)
        g.fixed_advance(320)
    r["space"] = Recipe("space", space, 0x20, "lower")
    for letter, (name, build) in birds.items():
        r[letter] = Recipe(letter, _recipe(name, build, False, style), ord(letter), "lower")
        lo = letter.lower()
        r[lo] = Recipe(lo, _recipe(name, build, True, style), ord(lo), "lower")
    for ch, (name, build) in (extras or {}).items():
        glyph = FIGURES[int(ch)] if ch.isdigit() else name
        r[glyph] = Recipe(glyph, _recipe(name, build, False, style), ord(ch), "figure")
    return r
