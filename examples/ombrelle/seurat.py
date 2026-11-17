"""Dots for Ombrelle: letters painted the way the pointillists painted, in whole dots of pure color.

Nothing here copies a painting. The effect follows what is known about the method:

- a local color, with dots of its neighbors on the color wheel mixed in;
- warm light on the side of a form that faces the sun, cool violet-blue shadow on the other side;
- dots of the complementary color sprinkled into the shadow (orange in blue);
- a soft edge where the form meets the ground: the edge is a row of dots, and a few pale dots
  spill out on the shadow side;
- for the initials, a painted border of dots around the picture, whose color answers the color
  next to it.

Every dot is whole: its center lies in the letter shrunk by the dot's radius, so no edge cuts it.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, flatten_contour, left, transform_contour, unit
from whateverfont.glyph import G, Recipe, Recipes
from whateverfont.outline import circle, difference, dilate, rect, union

SUN = complex(-0.55, 0.835)      # toward the light: the upper left, as in an afternoon park
HALO = complex(0.958, -0.287)    # the halo lies on the sides that face away from the sun, mostly the right
LADDER = 7                       # shadow to light: keys d0 (deep shadow) to d6 (full sun)


# --------------------------------------------------------------------------
# Rasters: fast answers to "is this point inside?" and "which way does the form turn?"
# --------------------------------------------------------------------------

class Field:
    """A shape drawn into a small gray image, with the font's y-up coordinates."""

    def __init__(self, contours: list, box: tuple, px: float = 2.0, blur: float = 0.0):
        x0, y0, x1, y1 = box
        pad = 3 + int(2.5 * blur / px)
        self.x0, self.y1, self.px, self.pad = x0, y1, px, pad
        self.w = int((x1 - x0) / px) + 2 * pad + 1
        self.h = int((y1 - y0) / px) + 2 * pad + 1
        img = Image.new("L", (self.w, self.h), 0)
        draw = ImageDraw.Draw(img)
        polys = []
        for c in contours:
            pts = flatten_contour(c, 1.0)
            if len(pts) >= 3:
                polys.append((abs(contour_area(c)), contour_area(c) < 0, pts))
        for _, solid, pts in sorted(polys, key=lambda t: -t[0]):     # counters punch holes
            draw.polygon([self._pix(p) for p in pts], fill=255 if solid else 0)
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur / px))
        self.data = img.load()

    def _pix(self, q: complex) -> tuple:
        return ((q.real - self.x0) / self.px + self.pad, (self.y1 - q.imag) / self.px + self.pad)

    def value(self, q: complex) -> float:
        """0 outside, 1 inside, in between near a blurred edge (bilinear)."""
        x, y = self._pix(q)
        x, y = x - 0.5, y - 0.5
        i, j = int(math.floor(x)), int(math.floor(y))
        if i < 0 or j < 0 or i + 1 >= self.w or j + 1 >= self.h:
            return 0.0
        fx, fy = x - i, y - j
        d = self.data
        top = d[i, j] * (1 - fx) + d[i + 1, j] * fx
        bottom = d[i, j + 1] * (1 - fx) + d[i + 1, j + 1] * fx
        return (top * (1 - fy) + bottom * fy) / 255.0

    def inside(self, q: complex) -> bool:
        x, y = self._pix(q)
        i, j = int(x), int(y)
        return 0 <= i < self.w and 0 <= j < self.h and self.data[i, j] > 127

    def slope(self, q: complex) -> complex:
        """The direction in which the field grows: into the ink, strongest at the edge."""
        h = self.px
        return complex(self.value(q + h) - self.value(q - h), self.value(q + 1j * h) - self.value(q - 1j * h)) / (2 * h)


class Spots:
    """Dots placed so far, in a grid of buckets, so that a new dot can check its neighbors quickly."""

    def __init__(self, cell: float):
        self.cell = cell
        self.grid: dict = {}
        self.all: list = []

    def free(self, q: complex, rad: float, gap: float) -> bool:
        cx, cy = int(math.floor(q.real / self.cell)), int(math.floor(q.imag / self.cell))
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for p, r in self.grid.get((i, j), ()):
                    if abs(p - q) < r + rad + gap:
                        return False
        return True

    def add(self, q: complex, rad: float):
        key = (int(math.floor(q.real / self.cell)), int(math.floor(q.imag / self.cell)))
        self.grid.setdefault(key, []).append((q, rad))
        self.all.append((q, rad))


# --------------------------------------------------------------------------
# Placing the dots
# --------------------------------------------------------------------------

def _components(ink: list) -> list:
    """The letter split into its separate parts (an outside with its counters): the dot of an i, an accent."""
    outers = [c for c in ink if contour_area(c) < 0]
    holes = [c for c in ink if contour_area(c) > 0]
    parts = [[c] for c in sorted(outers, key=lambda c: abs(contour_area(c)))]
    for h in holes:
        hb = contour_bounds([h])
        for part in parts:                         # the smallest outside that holds the counter
            ob = contour_bounds([part[0]])
            if ob[0] <= hb[0] and ob[1] <= hb[1] and ob[2] >= hb[2] and ob[3] >= hb[3]:
                part.append(h)
                break
    return parts


def _walk(contour: list, spacing: float, rng) -> list:
    """Points spaced evenly along a contour."""
    pts = flatten_contour(contour, 1.0)
    if len(pts) < 2:
        return []
    lens = [abs(pts[(i + 1) % len(pts)] - pts[i]) for i in range(len(pts))]
    total = sum(lens)
    n = max(1, round(total / spacing))
    step = total / n
    out = []
    target = rng.uniform(0, step)
    run = 0.0
    for i, seg in enumerate(lens):
        while target <= run + seg and len(out) < n:
            t = (target - run) / seg if seg else 0.0
            out.append(pts[i] + (pts[(i + 1) % len(pts)] - pts[i]) * t)
            target += step
        run += seg
    return out


def _safe_erode(contours: list, amount: float) -> list:
    try:
        return effects.erode(contours, amount)
    except Exception:          # Skia could not shrink this outline: no dot fits there
        return []


def place(part: list, r: float, rng, gap: float = 0.22, small: float = 0.58) -> list:
    """Whole dots that fill one part of a letter: a row along its edge, then the inside.

    Returns [(center, radius)]. ``gap`` is the least space between two dots, as a share of ``r``.
    ``small`` is the radius of the dots that fill what is left, as a share of ``r``.
    """
    margin = 3.0                                   # every dot stays this far inside the edge
    core = _safe_erode(part, r + margin)
    box = contour_bounds(part)
    spots = Spots(2.4 * r)
    if core:
        inside = Field(core, box, px=2.0)
        # 1. a row of dots along the edge: it draws the letter, as an outline drawn in dots would
        for c in core:
            for q in _walk(c, 2 * r * 1.16, rng):      # on the shrunk edge: whole by construction
                rad = r * rng.uniform(0.93, 1.0)
                if spots.free(q, rad, gap * r):
                    spots.add(q, rad)
        # 2. the inside, from the edge inward: each new dot near one already placed, never touching it
        active = list(range(len(spots.all)))
        while active:
            k = rng.randrange(len(active))
            p, pr = spots.all[active[k]]
            for _ in range(16):
                rad = r * rng.uniform(0.86, 1.0)
                turn = rng.uniform(0, math.tau)
                q = p + (pr + rad + gap * r) * rng.uniform(1.0, 1.3) * complex(math.cos(turn), math.sin(turn))
                if inside.inside(q) and spots.free(q, rad, gap * r):
                    spots.add(q, rad)
                    active.append(len(spots.all) - 1)
                    break
            else:
                active.pop(k)
    # 3. smaller dots in what is left: the narrow parts, the corners, and the holes between dots
    rs = r * small
    core_s = _safe_erode(part, rs + margin)
    if core_s:
        inside_s = Field(core_s, box, px=2.0)
        x0, y0, x1, y1 = contour_bounds(core_s)
        step = rs * 1.3
        y = y0
        while y <= y1:
            x = x0 + rng.uniform(0, step)
            while x <= x1:
                q = complex(x + rng.uniform(-0.3, 0.3) * step, y + rng.uniform(-0.3, 0.3) * step)
                rad = rs * rng.uniform(0.9, 1.05)
                if inside_s.inside(q) and spots.free(q, rad, gap * r * 0.8):
                    spots.add(q, rad)
                x += step
            y += step
    return spots.all


def tone(q: complex, relief: Field, sigma: float, cap: float, box: tuple, rng, noise: float = 0.16,
         floor: float = 0.0) -> float:
    """From 0 (deep shadow) to 1 (full sun) for a dot at ``q``.

    The blurred letter is a relief: where it rises toward the sun, the form faces the light. The
    middle of a stroke keeps its local color. The right part of a letter is a little cooler than its
    left part, and low parts a little cooler than high ones, so that the whole letter is one lit form.
    """
    s = relief.slope(q)
    facing = max(-1.0, min(1.0, -(s.real * SUN.real + s.imag * SUN.imag) * sigma * 2.6))
    facing = math.copysign(abs(facing) ** 0.65, facing)          # broad lit and shaded sides
    across = (q.real - (box[0] + box[2]) / 2) / max(200.0, box[2] - box[0])
    height = (q.imag - floor) / cap - 0.45
    return 0.5 + 0.44 * facing - 0.20 * across + 0.08 * height + rng.gauss(0, noise)


def sort_dots(dots: list, relief: Field, sigma: float, cap: float, box: tuple, rng, sprinkle: float = 0.22,
              floor: float = 0.0) -> dict:
    """Give each dot a key: d0 to d6 by its tone, or x (the complement) for some dots in shadow."""
    keys: dict = {}
    for q, rad in dots:
        t = tone(q, relief, sigma, cap, box, rng, floor=floor)
        if t < 0.36 and rng.random() < sprinkle:
            key = "x"
        else:
            key = f"d{min(LADDER - 1, max(0, int(t * LADDER)))}"
        keys.setdefault(key, []).append(circle(q.real, q.imag, rad))
    return keys


def spill(ink: list, field: Field, r: float, rng, amount: float = 0.5) -> list:
    """Pale dots just outside the shadow side of the letter: the soft edge where it meets the ground."""
    out = Spots(2.0 * r)
    for c in ink:
        if contour_area(c) > 0:
            continue                               # not inside the counters
        pts = flatten_contour(c, 1.5)
        n = len(pts)
        for q in _walk(c, r * 1.3, rng):
            # the outward normal of the nearest stretch of the contour
            i = min(range(n), key=lambda k: abs(pts[k] - q))
            t = unit(pts[(i + 1) % n] - pts[i - 1])
            normal = left(t)
            shade = normal.real * HALO.real + normal.imag * HALO.imag
            if shade < 0.45 or rng.random() > amount * shade:
                continue
            rad = r * rng.uniform(0.42, 0.56)
            p = q + normal * (rad + 5 + rng.uniform(0, r * 0.45)) + left(normal) * rng.uniform(-0.3, 0.3) * r
            ring = [p + rad * 1.3 * complex(math.cos(a), math.sin(a)) for a in (0, 1.57, 3.14, 4.71)]
            if field.inside(p) or any(field.inside(z) for z in ring) or not out.free(p, rad, r * 0.35):
                continue
            out.add(p, rad)
    return [circle(p.real, p.imag, rad) for p, rad in out.all]


def under(part: list, amount: float) -> list:
    """The underpainting of one part: the part shrunk a little, so that the row of edge dots makes
    the edge. A part too small to shrink keeps its whole shape."""
    shrunk = _safe_erode(part, amount)
    keep = abs(sum(contour_area(c) for c in shrunk))
    whole = abs(sum(contour_area(c) for c in part))
    return shrunk if keep > 0.35 * whole else part


# --------------------------------------------------------------------------
# The effect
# --------------------------------------------------------------------------

def paint(ink: list, r: float, cap: float, stem: float, rng, halo: float = 0.5, inset: float = 0.55,
          floor: float = 0.0) -> list:
    """The layers of one painted shape: underpainting, dots by tone, the complement, the halo.

    ``cap`` is the height of a capital and ``floor`` the baseline, for the light that falls from above.
    """
    box = contour_bounds(ink)
    sigma = stem * 0.45
    relief = Field(ink, box, px=4.0, blur=sigma)
    solid = Field(ink, box, px=2.0)
    dots, base = [], []
    for part in _components(ink):
        pr = r
        got = place(part, pr, rng)
        if not got:                                # an accent or a period: smaller dots
            pr = r * 0.6
            got = place(part, pr, rng, small=0.75)
        dots += got
        base += under(part, pr * inset) if got else part
    layers = [("base", union(base) if base else ink)]
    keys = sort_dots(dots, relief, sigma, cap, box, rng, floor=floor)
    for i in range(LADDER):
        if f"d{i}" in keys:
            layers.append((f"d{i}", keys[f"d{i}"]))
    if "x" in keys:
        layers.append(("x", keys["x"]))
    if halo:
        pale = spill(ink, solid, r, rng, halo)
        if pale:
            layers.append(("halo", pale))
    return layers


def dotted(recipes: Recipes, r: float = 20.0, halo: float = 0.5, seed: int = 0, names=None) -> Recipes:
    """Letters in whole dots, lit from the upper left. Keys: base, d0 to d6, x, halo."""

    def effect(g: G, ink: list):
        rng = effects.seed_for(g, seed)
        stem = g.sw * (1.1 if g.case == "upper" else 1.0)
        g.layers = paint(ink, r, g.cap, stem, rng, halo)

    return effects.wrapped(recipes, effect, names=names)


# --------------------------------------------------------------------------
# Initials: a capital standing on a dotted lawn, inside a painted border of dots
# --------------------------------------------------------------------------

FIELD = 4      # the lawn, from its shaded colors to its sunlit ones: keys f0 to f3
BORDER = 4     # the painted border, from the color that answers shade to the one that answers sun: b0 to b3


def tile(fn, size: float = 900.0, band: float = 66.0, r: float = 20.0, seed: int = 7):
    """Wrap a capital recipe: the letter on a square of dotted lawn, with a painted border.

    The letter casts a long shadow to the lower right, as in an afternoon park. The border is a band
    of dots whose color answers the lawn next to it: blue beside sun, orange beside shade.
    """

    def recipe(g: G):
        p = g.p
        rng = effects.seed_for(g, seed)
        gl = G(p, g.name, "upper")
        gl.recipes = g.recipes
        fn(gl)
        letter = union(gl.outlines())
        b = contour_bounds(letter)
        if b is None:
            return
        y0 = -(size - p.cap) / 2 - 60                  # the tile reaches lower than the letters...
        y1 = y0 + size
        foot = y0 + band + 150                         # ...so that the shadow has room below the letter
        scale = min(0.80, (size - 2 * band - 76) / (b[2] - b[0]))   # wide capitals shrink a little
        mid = complex((b[0] + b[2]) / 2, 0.0)
        to_tile = lambda q: complex(size / 2 - 22, foot) + (q - mid) * scale
        letter = [transform_contour(c, to_tile) for c in letter]

        outer = [rect(0, y0, size, y1, 14)]
        inner = [rect(band, y0 + band, size - band, y1 - band)]
        # the shadow on the ground: the letter laid down toward the lower right
        lay = lambda q: complex(q.real + 0.62 * (q.imag - foot) + 6, foot - 0.20 * (q.imag - foot) - 4)
        shadow = [c for c in union([transform_contour(c, lay) for c in letter]) if contour_area(c) < 0]
        box = (0.0, y0, size, y1)
        in_shadow = Field(shadow, box, px=3.0) if shadow else None

        def light(q: complex) -> float:
            """How sunlit the lawn is at a point: bright at the upper left, dark in the shadow."""
            u, v = q.real / size, (q.imag - y0) / size
            t = 0.70 + 0.30 * (v - 0.5) - 0.22 * (u - 0.5)
            if in_shadow is not None and in_shadow.inside(q):
                t -= 0.62
            return t

        # the lawn: dots that fill the square around the letter, keeping a little away from it
        lawn = difference(inner, dilate(letter, 10))
        grass: dict = {}
        for q, rad in place(lawn, r, rng, small=0.55):
            t = light(q) + rng.gauss(0, 0.12)
            if t < 0.25:
                key = "x" if rng.random() < 0.18 else "shade"
            else:
                key = f"f{min(FIELD - 1, max(0, int((t - 0.25) / 0.75 * FIELD)))}"
            grass.setdefault(key, []).append(circle(q.real, q.imag, rad))

        # the border: its color answers the lawn just inside it
        frame: dict = {}
        ring = difference(outer, inner)
        for q, rad in place(ring, r * 0.9, rng, small=0.6):
            near = complex(min(max(q.real, band + 30), size - band - 30), min(max(q.imag, y0 + band + 30), y1 - band - 30))
            t = (light(near) - 0.2) / 0.8 + rng.gauss(0, 0.10)
            key = f"b{min(BORDER - 1, max(0, int(t * BORDER)))}"
            frame.setdefault(key, []).append(circle(q.real, q.imag, rad))

        stem = p.weight * p.cap_weight * scale
        g.layers = [("rim", outer), ("ground", inner)]
        for key in ["shade", "x"] + [f"f{i}" for i in range(FIELD)]:
            if key in grass:
                g.layers.append((key, grass[key]))
        for i in range(BORDER):
            if f"b{i}" in frame:
                g.layers.append((f"b{i}", frame[f"b{i}"]))
        g.layers += paint(letter, r, p.cap * scale, stem, rng, halo=0.0, floor=foot)
        # without color support: a dark square with the letter cut out of it
        for c in difference(outer, letter):
            g.shapes.append(("shape", c, None))
        g.frame(size, 0.25, 0.25)
        g.static_only = True

    return recipe


def initials(recipes: Recipes, r: float = 20.0) -> Recipes:
    """Capitals on tiles of dotted lawn. Every other glyph is dotted like the text face."""
    out = dotted(recipes, r=r)
    names = [n for n, rec in recipes.items() if rec.case == "upper" and len(n) == 1 and n.isalpha()]
    for name in names:
        rec = recipes[name]
        out[name] = Recipe(name, tile(rec.plain or rec.fn, r=r), rec.unicode, rec.case, rec.plain or rec.fn)
    return out


def palette(base: str, ladder: list, complement: str, halo: str, ground: str = "#F3EBD5",
            field: list = (), shade: str = "#8F86C8", rim: str = "#26285E", border: list = ()) -> dict:
    """A palette: the underpainting, seven colors from deep shadow to full sun, the complement that is
    sprinkled into the shadow, and the pale color of the halo.

    The initials also use ``ground`` (the lawn under its dots), ``field`` (four lawn colors, shaded to
    sunlit), ``shade`` (the dots of the cast shadow), ``rim`` (under the border) and ``border`` (four
    border colors: the one beside shade first, the one beside sun last). The paper each palette is made
    for is GROUNDS in font.py: it is not a layer of the letters."""
    pal = {"base": base, "x": complement, "halo": halo, "ground": ground, "shade": shade, "rim": rim}
    pal.update({f"d{i}": c for i, c in enumerate(ladder)})
    pal.update({f"f{i}": c for i, c in enumerate(field or [ground] * FIELD)})
    pal.update({f"b{i}": c for i, c in enumerate(border or [rim] * BORDER)})
    return pal
