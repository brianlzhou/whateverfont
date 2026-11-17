"""Decorated capitals: a letter on a colored field with holly and vine work.

``illuminate`` wraps capital recipes. Each wrapped recipe draws the letter,
places it on a framed field, grows ornament in the corners, and keeps the
ornament clear of the letter. The parts come out as color layers.
"""

from __future__ import annotations

import math
import random

from .geom import contour_area, contour_bounds, reverse_contour, transform_contour
from .glyph import G, Recipe, Recipes
from .outline import circle, difference, dilate, intersection, rect, union
from .stroke import FixedPen, Node, Stroke, expand


# --------------------------------------------------------------------------
# Motifs
# --------------------------------------------------------------------------

def spiral(cx: float, cy: float, r0: float, quadrant: int, clockwise: bool, quarters: int = 6,
           decay: float = 0.80, half: float = 7.0) -> list:
    """A curl that winds inward from radius ``r0``. Returns outline contours."""
    k = 0.5523
    step = -1 if clockwise else 1
    nodes, handles = [], []
    r = r0
    a = quadrant * 90.0
    p = complex(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    nodes.append(Node(p, 1.25))
    for i in range(quarters):
        r1 = r * decay
        a1 = a + 90 * step
        t0 = complex(-math.sin(math.radians(a)), math.cos(math.radians(a))) * step
        t1 = complex(-math.sin(math.radians(a1)), math.cos(math.radians(a1))) * step
        q = complex(cx + r1 * math.cos(math.radians(a1)), cy + r1 * math.sin(math.radians(a1)))
        handles.append((p + t0 * r * k, q - t1 * r1 * k))
        nodes.append(Node(q, 1.25 - 0.75 * (i + 1) / quarters, corner=False))
        p, r, a = q, r1, a1
    s = Stroke(nodes, handles, round_joins=False)
    out = expand(s, FixedPen(half), roundness=1.0)
    # a bud at the center of the curl
    out.append(circle(p.real, p.imag, half * 1.5))
    return out


def holly_leaf(base: complex, angle: float, length: float, width: float, spikes: int = 3) -> list:
    """One holly leaf: scalloped edges between sharp points. Returns one contour."""
    d = complex(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    n = d * 1j

    def env(t):
        return math.sin(math.pi * t) ** 0.7 * width

    tips_t = [(i + 0.5) / spikes for i in range(spikes)]
    left = [base + d * length * t + n * env(t) * 1.18 for t in tips_t]
    right = [base + d * length * t - n * env(t) * 1.18 for t in tips_t]
    tip = base + d * length
    order = [base] + left + [tip] + list(reversed(right))
    axis_pts = [base + d * length * t for t in [0.0] + tips_t + [1.0]]
    contour = []
    m = len(order)
    for i in range(m):
        a, b = order[i], order[(i + 1) % m]
        # pull each edge toward the leaf's axis, which makes the scallop
        mid = (a + b) / 2
        t = max(0.0, min(1.0, ((mid - base).real * d.real + (mid - base).imag * d.imag) / length))
        inward = base + d * length * t
        c = mid + (inward - mid) * 0.52
        contour.append((a, a + (c - a) * 0.7, b + (c - b) * 0.7, b))
    if contour_area(contour) > 0:
        contour = reverse_contour(contour)
    return contour


def sprig(base: complex, angle: float, size: float, rng: random.Random) -> tuple:
    """Holly: three leaves fanning out from ``base``, and berries. Returns (leaves, berries)."""
    leaves = []
    for da, ln in ((-45, 1.0), (0, 0.72), (45, 1.0)):
        a = angle + da + rng.uniform(-4, 4)
        leaves.append(holly_leaf(base, a, size * ln * rng.uniform(0.94, 1.04), size * 0.17))
    r = size * 0.10
    back = complex(math.cos(math.radians(angle + 180)), math.sin(math.radians(angle + 180)))
    side = back * 1j
    berries = [circle(*_xy(base + back * r * 0.2), r),
               circle(*_xy(base + back * r * 1.5 + side * r * 1.05), r * 0.9),
               circle(*_xy(base + back * r * 1.5 - side * r * 1.05), r * 0.9)]
    return leaves, berries


def _xy(p: complex) -> tuple:
    return p.real, p.imag


# --------------------------------------------------------------------------
# The decorated capital
# --------------------------------------------------------------------------

def _letter(fn, p, name: str, heavier: float, flare: float, recipes=None) -> list:
    """The capital, a little heavier than in text, as merged outlines."""
    lp = p.but(weight=p.weight * heavier, flare=max(p.flare, flare), spacing=p.spacing)
    gl = G(lp, name, "upper")
    gl.recipes = recipes
    fn(gl)
    return union(gl.outlines())


def decorated(fn, index: int, height: float = 880.0, min_width: float = 600.0, pad: float = 118.0,
              heavier: float = 1.22, flare: float = 0.42, width=None):
    """Wrap a capital recipe ``fn`` so it draws a decorated initial.

    ``width`` makes every tile the same width: a number in font units, or a
    callable that returns one for the parameters. A letter too wide for the
    tile first gives up some padding, then shrinks to fit.
    """
    fixed = width

    def recipe(g: G):
        p = g.p
        # 1. the letter, a little heavier than in text
        letter = _letter(fn, p, g.name, heavier, flare, g.recipes)
        b = contour_bounds(letter)
        if b is None:
            return
        lw = b[2] - b[0]
        y0 = -(height - p.cap) / 2
        y1 = y0 + height
        if fixed is None:
            tile = max(min_width, lw + 2 * pad)
        else:
            tile = fixed(p) if callable(fixed) else float(fixed)
            room = tile - 2 * pad * 0.55
            if lw > room:
                k = room / lw
                mid = complex((b[0] + b[2]) / 2, p.cap / 2)
                letter = [transform_contour(c, lambda q: mid + (q - mid) * k) for c in letter]
                b = contour_bounds(letter)
                lw = b[2] - b[0]
        dx = (tile - lw) / 2 - b[0]
        letter = [transform_contour(c, lambda q: q + dx) for c in letter]

        # 2. field and frame
        width = tile
        outer = rect(0, y0, width, y1, 26)
        f0, f1 = 20.0, 46.0
        ring = difference([rect(f0, y0 + f0, width - f0, y1 - f0, 14)],
                          [rect(f1, y0 + f1, width - f1, y1 - f1, 6)])
        inner = [rect(f1 + 10, y0 + f1 + 10, width - f1 - 10, y1 - f1 - 10, 4)]

        # 3. ornament in the corners, kept clear of the letter
        rng = random.Random(1000 + index * 7919)
        halo = dilate(letter, 24)
        s = min(width, height)
        leaves, berries, curls = [], [], []
        inset = 62.0 + f1
        corners = {"tl": (complex(inset, y1 - inset), -45), "tr": (complex(width - inset, y1 - inset), 225),
                   "bl": (complex(inset, y0 + inset), 45), "br": (complex(width - inset, y0 + inset), 135)}
        holly = ("tr", "bl") if index % 2 == 0 else ("tl", "br")
        for key, (pt, toward) in corners.items():
            if key in holly:
                # the leaves fan inward: one along each edge and one between them
                inward = complex(math.cos(math.radians(toward)), math.sin(math.radians(toward)))
                lv, br = sprig(pt + inward * 26, toward + rng.uniform(-5, 5), s * 0.29, rng)
                leaves += lv
                berries += br
            else:
                quad = {"tl": 0, "tr": 2, "bl": 0, "br": 2}[key]
                cw = (key in ("tl", "br")) ^ (index % 3 == 0)
                curls += spiral(pt.real, pt.imag, s * 0.085, quad, cw, half=6.5)
                # a smaller curl beside it, and buds
                side = complex(math.cos(math.radians(toward - 45)), math.sin(math.radians(toward - 45)))
                c2 = pt + side * s * 0.19
                curls += spiral(c2.real, c2.imag, s * 0.05, (quad + 1) % 4, not cw, quarters=5, half=5.5)
                for k in range(3):
                    a = math.radians(toward + (-62, 62, 0)[k])
                    c = pt + complex(math.cos(a), math.sin(a)) * s * (0.17 if k < 2 else 0.20)
                    curls.append(circle(c.real, c.imag, 8.5))

        def tidy(shapes, least=700.0):
            if not shapes:
                return []
            kept = difference(intersection(union(shapes), inner), halo)
            # clipping leaves crumbs; drop them
            return [c for c in kept if abs(contour_area(c)) >= least]

        leaves, berries, curls = tidy(leaves, 1500.0), tidy(berries, 500.0), tidy(curls, 180.0)
        shade = difference([transform_contour(c, lambda q: q + complex(9, -9)) for c in letter], letter)

        variant = "a" if index % 2 == 0 else "b"
        g.layers = [(f"field_{variant}", [outer])]
        if curls:
            g.layers.append(("vine", curls))
        if leaves:
            g.layers.append((f"leaf_{variant}", leaves))
        if berries:
            g.layers.append((f"berry_{variant}", berries))
        g.layers += [("frame", ring), ("shade", shade), ("letter", letter)]
        # Without color support the glyph is a solid tile with the letter cut out.
        # Its bounding box covers every layer, which some renderers rely on.
        for c in difference([outer], letter):
            g.shapes.append(("shape", c, None))
        g.frame(width, 0.3, 0.3)

    return recipe


def illuminate(recipes: Recipes, names=None, equal: bool | float = False, **options) -> Recipes:
    """A copy of ``recipes`` in which the capitals are decorated initials.

    ``equal=True`` gives every tile one width: the width of the widest
    capital's tile. A number sets that width instead (``equal=880`` makes
    square tiles, and the widest letters shrink a little to fit).
    """
    out = recipes.copy()
    names = names or [n for n, r in recipes.items() if r.case == "upper" and len(n) == 1 and n.isalpha()]
    if equal is True:
        cache: dict = {}
        heavier, flare = options.get("heavier", 1.22), options.get("flare", 0.42)
        pad, min_width = options.get("pad", 118.0), options.get("min_width", 600.0)

        def widest(p):
            if p not in cache:
                widths = []
                for n in names:
                    bb = contour_bounds(_letter(recipes[n].fn, p, n, heavier, flare))
                    if bb:
                        widths.append(bb[2] - bb[0])
                cache[p] = max(min_width, max(widths) + 2 * pad)
            return cache[p]
        options["width"] = widest
    elif equal:
        options["width"] = float(equal)
    for i, name in enumerate(names):
        rec = recipes[name]
        # plain: an accented capital (Á) is built on the plain A, not on the tile
        out[name] = Recipe(name, decorated(rec.fn, i, **options), rec.unicode, rec.case, rec.plain or rec.fn)
    return out


# Palettes: each maps a layer key to a color. Pigment names follow medieval practice.
CHRISTMAS = {
    "field_a": "#9E1B24",   # vermilion, deepened
    "field_b": "#1F5B3A",   # holly green
    "vine": "#F0E2B6",      # parchment
    "leaf_a": "#2E7D4F",
    "leaf_b": "#D9B44A",
    "berry_a": "#F6EBD0",
    "berry_b": "#C8202C",
    "frame": "#C9A227",     # gold leaf
    "shade": "#3A0F12",
    "letter": "#F2C94C",
}
ULTRAMARINE = {
    "field_a": "#243B8A", "field_b": "#7A1F2B", "vine": "#F0E2B6", "leaf_a": "#C9A227", "leaf_b": "#C9A227",
    "berry_a": "#E34234", "berry_b": "#F0E2B6", "frame": "#C9A227", "shade": "#121A3D", "letter": "#F7E7A6",
}
FROST = {
    "field_a": "#F4F1E8", "field_b": "#E3ECE6", "vine": "#B9C4BD", "leaf_a": "#1F5B3A", "leaf_b": "#1F5B3A",
    "berry_a": "#B3202A", "berry_b": "#B3202A", "frame": "#B08D2E", "shade": "#D8D2C0", "letter": "#8E1B22",
}
