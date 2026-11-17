"""Print every letter with a 9-pin dot-matrix head: the effect behind Greenbar.

A 9-pin print head is a column of nine pins. It fires them as it travels across the paper, so a
letter is made of dots on fixed rows: seven for a capital, two more for descenders. A draft-mode
printer fires them on fixed columns too, five to a letter, with an empty column between letters.

A printer kept its letters as small drawings in a character ROM, and so does this effect: a
character with a drawing in ``bitmaps`` is printed from it. Any other character is traced: the
effect takes the skeleton of the letter (the centerline of its strokes), maps it onto the grid of
the head, and fires a pin wherever the skeleton passes close to a grid point. A traced letter is
five columns wide, three, or one, so its stems land on columns. Every letter uses the same grid,
so dots line up from letter to letter and from line to line.
"""

from __future__ import annotations

from whateverfont import effects
from whateverfont.geom import contour_bounds, flatten_seg
from whateverfont.outline import circle, dilate, union

#: Row pitch and column step, in font units. Rows run from -2 (the lowest descender pin) to 6 (the
#: top of the capitals): nine pins. Columns run from 100 to 500 in a 600-unit cell.
PITCH = 100.0
ROWS = range(-2, 7)
COLS = [100.0, 200.0, 300.0, 400.0, 500.0]
#: From this weight up, every dot is struck twice, half a step apart: the printer's emphasized mode.
EMPHASIZED = 75.0


def _y_map(g):
    """A function that takes a skeleton height to the grid: the centerlines of the descender, the
    baseline, the x-height and the cap height land on rows -2, 0, 4 and 6."""
    h = g.hw / 2
    # the capitals and the ascenders both end on the top row; the dot of i and j, which the
    # letter puts between the two, goes up there too, so a row of white separates it from the stem
    src = [g.desc + h, h, g.xh - h, g.cap - h, g.asc - h]
    dst = [-2 * PITCH, 0.0, 4 * PITCH, 6 * PITCH, 6 * PITCH]

    def f(y: float) -> float:
        for i in range(len(src) - 1):
            if y <= src[i + 1] or i == len(src) - 2:
                a, b = src[i], src[i + 1]
                return dst[i] + (y - a) * (dst[i + 1] - dst[i]) / (b - a)
        return y
    return f


def _polylines(g) -> list:
    """The skeleton as polylines, and the filled shapes (dots) as single points."""
    lines = []
    for s in g.strokes:
        segs = s.segments()
        pts = [segs[0][0]] if segs else []
        for seg in segs:
            pts.extend(flatten_seg(seg, 2.0))           # every point but the first
        lines.append(pts)
    for _, contour, _ in g.shapes:
        b = contour_bounds([contour])
        if b:
            lines.append([complex((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)])
    return lines


def _distance(q: complex, line: list) -> float:
    if len(line) == 1:
        return abs(q - line[0])
    best = float("inf")
    for a, b in zip(line, line[1:]):
        d = b - a
        n = abs(d) ** 2
        t = 0.0 if n < 1e-9 else max(0.0, min(1.0, ((q - a) * d.conjugate()).real / n))
        best = min(best, abs(q - (a + d * t)))
    return best


def fire(g, reach: float = 0.5) -> list:
    """The dots the head prints for what ``g`` has drawn, as points in the 600-unit cell."""
    lines = _polylines(g)
    pts = [q for line in lines for q in line]
    if not pts:
        return []
    x0, x1 = min(q.real for q in pts), max(q.real for q in pts)
    # One scale for every letter, from the n, decides how many columns a letter wants: 5, 3 or 1.
    n = g.sw / g.k + g.p.n_counter                     # the n, from stem center to stem center
    span = min(400.0, 200.0 * round((x1 - x0) * 400.0 / n / 200.0))
    sx = span / (x1 - x0) if x1 - x0 > 1e-6 else 0.0
    fy = _y_map(g)
    mapped = [[complex(300.0 + (q.real - (x0 + x1) / 2) * sx, fy(q.imag)) for q in line] for line in lines]
    near = PITCH * reach
    out = []
    for r in ROWS:
        for x in COLS:
            q = complex(x, r * PITCH)
            if min(_distance(q, line) for line in mapped) < near + 1e-6:
                out.append(q)
    return out


def from_bitmap(rows: str) -> list:
    """Dots from a drawing of the character, as a printer's character ROM holds it.

    ``rows`` are words separated by spaces, one per pin row from the top (row 6) down: "#" fires
    a pin, "." does not. A row of five covers the columns 100 to 500; a row of six starts at the
    edge of the cell (0), so that a row of underscores prints as one unbroken line.
    """
    out = []
    for i, row in enumerate(rows.split()):
        x0 = 0.0 if len(row) == 6 else 100.0
        out += [complex(x0 + PITCH * j, (6 - i) * PITCH) for j, c in enumerate(row) if c == "#"]
    return out


def _beams(fired: list, height: float, spread: float) -> list:
    """What an electron beam draws for the same dots on a screen: on each scanline, pixels that
    touch fuse into one bar with round ends, and dark lines remain between the scanlines."""
    from whateverfont.outline import rect
    rows: dict = {}
    for q in fired:
        rows.setdefault(round(q.imag), []).append(q.real)
    out = []
    for y, xs in rows.items():
        xs.sort()
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x - prev <= PITCH + 1e-6:
                prev = x
                continue
            out.append(rect(start - spread, y - height / 2, prev + spread, y + height / 2, radius=height / 2))
            if x is not None:
                start = prev = x
    return union(out)


def screen(recipes, bitmaps: dict, glow: float = 56.0, height: float = 0.66, spread: float = 0.40,
           names=None):
    """The same character ROM on a phosphor screen: scanlines of light with a glow around them.

    A color effect. Keys: ``glow1`` to ``glow3`` (rings of light, faintest first), ``halo`` and
    ``beam`` (the lit phosphor). ``height`` is a scanline as a share of the pitch, ``spread`` how
    far a lit pixel reaches to each side (a share of the pitch), and ``glow`` the reach of the
    outer ring in units.
    """
    by_name = {n: bitmaps[chr(r.unicode)] for n, r in recipes.items()
               if r.unicode is not None and chr(r.unicode) in bitmaps}

    def effect(g, shape):
        fired = from_bitmap(by_name[g.name]) if g.name in by_name else fire(g)
        if not fired:
            return
        beam = _beams(fired, PITCH * height, PITCH * spread)
        g._frame = (g.p.mono, 0.5, 0.5)
        g.full_cell = True
        effects.redraw(g, beam)
        g.layers = [("glow1", dilate(beam, glow)), ("glow2", dilate(beam, glow * 0.6)),
                    ("glow3", dilate(beam, glow * 0.32)), ("halo", dilate(beam, glow * 0.12)), ("beam", beam)]
    return effects.wrapped(recipes, effect, names)


def matrix(recipes, bitmaps: dict | None = None, dot: float = 0.96, reach: float = 0.5, names=None):
    """Letters printed by a 9-pin head on a fixed grid. ``bitmaps`` maps a character to its drawing
    (see :func:`from_bitmap`); a character without one is traced from its skeleton. ``dot`` is the
    dot size as a share of the pitch, and ``reach`` how close the skeleton must pass a grid point
    to fire it."""
    bitmaps = bitmaps or {}
    by_name = {n: bitmaps[chr(r.unicode)] for n, r in recipes.items()
               if r.unicode is not None and chr(r.unicode) in bitmaps}

    def effect(g, shape):
        fired = from_bitmap(by_name[g.name]) if g.name in by_name else fire(g, reach)
        if not fired:
            return
        if g.p.weight >= EMPHASIZED:
            # emphasized print: the head goes over the line again half a step to the right
            fired = fired + [q + PITCH / 2 for q in fired]
        # The dots are already where the head put them: the glyph is the whole cell. The frame is
        # declared before the redraw, which would otherwise move the dots to the old drawing's edge.
        g._frame = (g.p.mono, 0.5, 0.5)
        g.full_cell = True
        effects.redraw(g, union([circle(q.real, q.imag, PITCH * dot / 2) for q in fired]))
    return effects.wrapped(recipes, effect, names)
