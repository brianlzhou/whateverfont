"""Cut paper: letters and leaves cut by hand out of painted paper.

A pair of scissors does not wobble along an edge. It makes long straight snips, turns a curve in a few flat
facets, and leaves stems that lean and taper a little. So the effect (1) closes the small notches that a
pen leaves, (2) bends the whole letter with a slow wave, (3) leans and lifts it a little, and (4) replaces
every curve with a few straight cuts.

`scissors(recipes)` gives a one-color font. `painted_paper(recipes)` gives the same shapes as a color
font in which every letter is one sheet of paper. `add_leaves(recipes)` puts leaf and seaweed shapes on
`* ^ ~ { }`.
"""

import cmath
import math

from whateverfont import effects
from whateverfont.outline import dilate, flatten_contour

# ---------------------------------------------------------------------------------------------- the cut


def _field(rng, scale):
    """A slow vector field: a few sine waves with random directions."""
    waves = []
    for _ in range(3):
        angle = rng.uniform(0, math.tau)
        k = math.tau / (scale * rng.uniform(0.75, 1.5))
        waves.append((k * math.cos(angle), k * math.sin(angle), rng.uniform(0, math.tau), rng.uniform(0, math.tau)))

    def at(p):
        dx = sum(math.sin(kx * p.real + ky * p.imag + a) for kx, ky, a, _ in waves) / 3
        dy = sum(math.sin(kx * p.real + ky * p.imag + b) for kx, ky, _, b in waves) / 3
        return complex(dx, dy)

    return at


def _rdp(pts, tol):
    """Ramer-Douglas-Peucker on an open run of points: keep only the points that a straight cut would miss."""
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    ab = b - a
    square = abs(ab) ** 2 or 1.0
    far, where = 0.0, 0
    for i in range(1, len(pts) - 1):
        ap = pts[i] - a
        t = min(1.0, max(0.0, (ap.real * ab.real + ap.imag * ab.imag) / square))
        d = abs(ap - t * ab)                      # distance to the cut, not to the endless line through it
        if d > far:
            far, where = d, i
    if far <= tol:
        return [a, b]
    return _rdp(pts[: where + 1], tol)[:-1] + _rdp(pts[where:], tol)


def _snip(pts, tol):
    """A closed run of points, cut again in straight snips."""
    if len(pts) < 4:
        return pts
    start = max(range(len(pts)), key=lambda i: abs(pts[i] - pts[0]))
    first, second = pts[: start + 1], pts[start:] + pts[:1]
    return _rdp(first, tol)[:-1] + _rdp(second, tol)[:-1]


def _split_long(pts, longest, rng):
    """Put one extra point on a long straight edge, so that a tall stem can bend once."""
    out = []
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        out.append(p)
        if abs(q - p) > longest:
            out.append(p + (q - p) * rng.uniform(0.35, 0.65))
    return out


def cut(g, ink, wobble=14.0, scale=420.0, facet=6.0, lean=2.8, lift=11.0, heal=10.0, pinhole=2200.0, seed=1):
    """The outline of one glyph, cut by hand. Returns contours of straight segments.

    ``wobble`` is how far the slow wave moves a point and ``scale`` the length of the wave, in units.
    ``facet`` is how far a straight snip may leave the true curve. ``lean`` (degrees) and ``lift`` (units)
    are the most a glyph may turn and rise. ``heal`` closes notches narrower than twice its value, and a
    hole smaller than ``pinhole`` square units is left out.
    """
    rng = effects.seed_for(g, seed)
    field = _field(rng, scale)
    turn = cmath.rect(1.0, math.radians(rng.uniform(-lean, lean)))
    rise = complex(0, rng.uniform(-lift, lift))
    if heal:
        ink = effects.erode(dilate(ink, heal, miter=True), heal)
    points = [p for contour in ink for p in flatten_contour(contour, 0.5)]
    if not points:
        return []
    center = complex((min(p.real for p in points) + max(p.real for p in points)) / 2,
                     (min(p.imag for p in points) + max(p.imag for p in points)) / 2)
    tol = facet * rng.uniform(0.8, 1.25)
    out = []
    for contour in ink:
        pts = flatten_contour(contour, 0.5)
        if len(pts) > 1 and abs(pts[0] - pts[-1]) < 1e-6:
            pts = pts[:-1]
        pts = _split_long(pts, 330.0, rng)
        pts = [center + (p - center) * turn + rise + wobble * field(p) for p in pts]
        pts = _snip(pts, tol)
        if len(pts) < 3:
            continue
        area = sum(pts[i].real * pts[(i + 1) % len(pts)].imag - pts[(i + 1) % len(pts)].real * pts[i].imag
                   for i in range(len(pts))) / 2
        if 0 < area < pinhole:
            continue          # a hole too small to cut (holes run counter-clockwise, so their area is positive)
        out.append([(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))])
    return out


def scissors(recipes, **options):
    """One color: every glyph cut by hand."""

    def effect(g, ink):
        effects.redraw(g, cut(g, ink, **options))

    return effects.wrapped(recipes, effect)


# ------------------------------------------------------------------------------------------- the colors

# Five sheets of paper. Each letter is cut from one sheet. The letters are sorted so that neighbors in
# English words seldom share a sheet: a search over the bigrams of a word list and of running text left
# about 2% of neighboring pairs on the same sheet (a random choice leaves 20%). Doubled letters (ll, ee)
# always match, because a font gives one letter one drawing.
SHEETS = {
    "sheet0": "bcdgptw",
    "sheet1": "fhkmnvy",
    "sheet2": "lrsz",
    "sheet3": "ejoq",
    "sheet4": "aiux",
}
FIGURES = {"zero": 3, "one": 0, "two": 1, "three": 2, "four": 4, "five": 0, "six": 2, "seven": 4, "eight": 1,
           "nine": 3}
OTHER = {"asterisk": 2, "braceleft": 0, "braceright": 1, "asciicircum": 3, "asciitilde": 2,
         "ampersand": 1, "at": 0, "numbersign": 2, "percent": 1, "dollar": 2, "plus": 1, "equal": 0,
         "exclam": 1, "question": 0}


def sheet_of(name):
    """The palette key for a glyph name."""
    letter = name.lower()
    for key, letters in SHEETS.items():
        if letter in letters:
            return key
    if name in FIGURES:
        return f"sheet{FIGURES[name]}"
    if name in OTHER:
        return f"sheet{OTHER[name]}"
    return "sheet4"            # points, quotes, dashes and brackets: the darkest sheet


def paper_palette(*colors):
    """A palette from five colors, in the order of the sheets."""
    return {f"sheet{i}": color for i, color in enumerate(colors)}


def painted_paper(recipes, **options):
    """A color font: every glyph is one sheet of painted paper, cut by hand."""

    def effect(g, ink):
        shape = cut(g, ink, **options)
        effects.redraw(g, shape)                  # the same shape where a program cannot show color
        g.layers = [(sheet_of(g.name), shape)]

    return effects.wrapped(recipes, effect)


# -------------------------------------------------------------------------------------------- the leaves


def _closed(pts):
    """A clockwise contour of straight segments through ``pts``."""
    area = sum(pts[i].real * pts[(i + 1) % len(pts)].imag - pts[(i + 1) % len(pts)].real * pts[i].imag
               for i in range(len(pts)))
    if area > 0:                                                  # counter-clockwise: turn it round
        pts = pts[::-1]
    return [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]


def _oval(center, long, short, angle, steps=28):
    """An oval as straight segments. ``long`` and ``short`` are radii; ``angle`` is in degrees."""
    turn = cmath.rect(1.0, math.radians(angle))
    return _closed([center + turn * complex(long * math.cos(math.tau * i / steps),
                                            short * math.sin(math.tau * i / steps)) for i in range(steps)])


def _frond(height, lobes, reach, thick, lean=0.0, sway=0.0):
    """A frond like a piece of seaweed: a stem with pairs of round fingers that point up and out.

    Returns ovals that overlap; the engine merges them.
    """
    ovals = []

    def spine(t):                                   # a point on the stem, t from 0 (foot) to 1 (tip)
        return complex(sway * math.sin(t * math.pi * 1.3), height * t)

    # uneven on purpose: a hand does not cut two fingers alike
    longer = [1.00, 0.86, 1.06, 0.80, 0.94, 0.90]
    wider = [1.00, 1.12, 0.92, 1.05, 0.96, 1.08]
    for k in range(lobes):
        t = 0.16 + 0.60 * k / max(1, lobes - 1)
        for i, side in enumerate((-1, 1)):
            n = 2 * k + i
            length = reach * (1.0 - 0.50 * t) * longer[n % 6]
            angle = 90 - side * (58 - 14 * t) + (5 if n % 3 == 0 else -4)
            root = spine(t + 0.03 * i)
            ovals.append(_oval(root + cmath.rect(length * 0.52, math.radians(angle)), length * 0.60,
                               thick * 0.5 * wider[n % 6] * (1.0 - 0.30 * t), angle))
    ovals.append(_oval(spine(0.86), height * 0.15, thick * 0.40, 90))                   # the tip
    for i in range(7):                                                                  # the stem
        ovals.append(_oval(spine(i / 6 * 0.8), height * 0.09, thick * 0.42, 90))
    turn = cmath.rect(1.0, math.radians(-lean))
    return [_closed([seg[0] * turn for seg in oval]) for oval in ovals]


def _leaf(length, width, lean):
    """One pointed leaf with a short stalk."""
    steps = 18
    right, left = [], []
    for i in range(steps + 1):
        t = i / steps
        half = width * 0.5 * math.sin(math.pi * t ** 0.85) ** 0.9
        right.append(complex(half, length * t))
        left.append(complex(-half * 0.86, length * t))
    turn = cmath.rect(1.0, math.radians(-lean))
    stalk = [complex(-16, -length * 0.20), complex(-10, length * 0.12), complex(14, length * 0.12),
             complex(20, -length * 0.20)]
    return [_closed([p * turn for p in right + left[-2:0:-1]]), _closed([p * turn for p in stalk])]


def _ribbon(length, wave, thick, waves=2.5):
    """A strand of seaweed that lies on its side: a wavy band, fat in the middle, with pointed ends."""
    steps = 60
    top, bottom = [], []
    for i in range(steps + 1):
        t = i / steps
        slope = wave * math.tau * waves / length * math.cos(math.tau * waves * t)
        normal = complex(-slope, 1.0) / abs(complex(-slope, 1.0))
        half = thick * 0.5 * math.sin(math.pi * t) ** 0.8 * (1.0 + 0.18 * math.sin(math.tau * 2.3 * t + 0.6))
        middle = complex(length * t, wave * math.sin(math.tau * waves * t))
        top.append(middle + normal * half)
        bottom.append(middle - normal * half)
    return [_closed(top + bottom[-2:0:-1])]


def _place(g, contours, baseline=0.0, side=0.45):
    """Put contours on the glyph with their left edge at x = 0 and their foot at ``baseline``."""
    xs = [p.real for c in contours for seg in c for p in seg]
    ys = [p.imag for c in contours for seg in c for p in seg]
    move = complex(-min(xs), baseline - min(ys))
    for contour in contours:
        g.shape([tuple(p + move for p in seg) for seg in contour])
    g.frame(max(xs) - min(xs), side, side)


def close_one(recipes):
    """Give the figure 1 its own width. In a fixed cell it leaves a hole in a year or a time on a poster.

    The engine's 1 ends with ``g.fixed_advance``, and a later ``g.frame`` does not undo that, so this draws
    a new 1: a stem and a flag, as wide as it is.
    """

    @recipes.add("one", "1", "figure")
    def one(g):
        reach = g.cw * 0.50                              # how far the flag reaches to the left of the stem
        thick = g.sw * 0.95                              # the flag, measured up and down
        g.stem(reach + g.L, 0, g.cap, t=0)
        low = g.cap * 0.66
        g.shape(_closed([complex(0, low), complex(0, low + thick * 0.8), complex(reach + g.L, g.cap),
                         complex(reach + g.L, g.cap - thick * 1.25)]))
        g.frame(reach + g.sw, 0.7, "s")

    return recipes


def roomy_dots(recipes, names=("Idieresis", "idieresis")):
    """Make a narrow letter as wide as the two dots above it, so heavy dots do not touch its neighbors."""
    for name in names:
        if name not in recipes:
            continue
        plain = recipes[name].fn

        @recipes.add(name, recipes[name].unicode, recipes[name].case)
        def wide(g, plain=plain):
            plain(g)
            g.frame(None, 0.5, 0.5)

    return recipes


def add_leaves(recipes):
    """Put leaf and seaweed shapes on ``* ^ ~ { }``. Returns the same recipe set."""

    @recipes.add("asterisk", "*", "upper")
    def asterisk(g):                                   # a tall frond, as high as a capital
        _place(g, _frond(g.cap * 1.04, 4, g.cap * 0.56, g.cap * 0.145, sway=g.cap * 0.035), baseline=-g.o)

    @recipes.add("braceleft", "{", "upper")
    def braceleft(g):                                  # a frond that leans away from the word it opens
        _place(g, _frond(g.cap * 0.98, 3, g.cap * 0.50, g.cap * 0.165, lean=-20, sway=-g.cap * 0.05),
               baseline=-g.o)

    @recipes.add("braceright", "}", "upper")
    def braceright(g):                                 # its partner, leaning the other way
        _place(g, _frond(g.cap * 0.98, 3, g.cap * 0.50, g.cap * 0.165, lean=20, sway=g.cap * 0.05),
               baseline=-g.o)

    @recipes.add("asciicircum", "^", "upper")
    def asciicircum(g):                                # one leaf
        _place(g, _leaf(g.cap * 0.74, g.cap * 0.44, 24), baseline=g.cap * 0.06)

    @recipes.add("asciitilde", "~", "upper")
    def asciitilde(g):                                 # a strand of seaweed on its side
        _place(g, _ribbon(g.cap * 1.55, g.cap * 0.13, g.cap * 0.25), baseline=g.cap * 0.12)

    return recipes
