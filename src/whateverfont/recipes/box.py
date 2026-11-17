"""Box drawings and block elements for a monospaced font (U+2500 to U+259F).

These glyphs are not letters. Each one fills its cell, from x = 0 to the cell
width and from the bottom of the line to its top, so that a row of them joins
up, and so do the lines of a text. Every recipe sets ``g.full_cell``: the
engine then leaves the drawing where it is.

Each glyph is drawn from its Unicode name. A junction is four arms (up, down,
left, right), and each arm is missing, light, heavy or double. Dashes, arcs,
diagonals, blocks, shades and quadrants have a drawing of their own.

The shapes are rectangles and polygons, not pen strokes, so a line has one
thickness in every direction. A glyph has the same contours at every weight,
so the masters of a variable font match.
"""

from __future__ import annotations

import math
import unicodedata

from ..geom import polygon_area, reverse_contour, transform_contour
from ..glyph import G, Recipes

BOX = Recipes()

#: The cell width when the font is not monospaced.
CELL = 600.0
#: Handle length of a quarter circle, as a share of the radius.
ARC = 0.5523
#: The white between two dashes, as a share of one dash and its white.
DASH_GAP = 0.32

NONE, LIGHT, HEAVY, DOUBLE = 0, 1, 2, 3


class _Cell:
    """The cell of one glyph, the thickness of a light line, and the contours drawn so far.

    Every position is a whole number of units, so the font file holds exactly what is drawn here.
    """

    def __init__(self, g: G):
        p = g.p
        self.w = p.mono if p.mono > 0 else CELL
        self.bottom = float(round(p.line_bottom))        # the descent and the ascent of the font
        self.top = float(round(p.line_top))
        self.h = self.top - self.bottom
        self.cx = float(round(self.w / 2))
        self.cy = float(round((self.bottom + self.top) / 2))
        # an even number, so that both edges of a centered line are whole
        self.t = 2.0 * round(max(36.0, min(p.weight * 0.9, self.w * 0.14)) / 2)
        self.contours: list = []

    def x(self, share: float) -> float:
        return self.w if share == 1 else float(round(self.w * share))

    def y(self, share: float) -> float:
        return float(round(self.bottom + self.h * share))

    def polygon(self, pts, hole: bool = False):
        """A filled polygon. It is turned clockwise (or the other way, to cut a hole)."""
        pts = [complex(x, y) for x, y in pts]
        if (polygon_area(pts) > 0) != hole:
            pts.reverse()
        n = len(pts)
        self.contours.append([(pts[i], pts[(i + 1) % n]) for i in range(n)])

    def rect(self, x0, y0, x1, y1, hole: bool = False):
        self.polygon([(x0, y0), (x0, y1), (x1, y1), (x1, y0)], hole)

    def span(self, arm: str) -> tuple:
        """The two edges of the cell along an arm, and the center between them."""
        return (0.0, self.cx, self.w) if arm in "lr" else (self.bottom, self.cy, self.top)

    def line(self, arm: str, a0, a1, b0, b1):
        """A line along an arm, from ``a0`` to ``a1``. ``b0`` and ``b1`` are its sides, measured from the center."""
        if arm in "lr":
            self.rect(a0, self.cy + b0, a1, self.cy + b1)
        else:
            self.rect(self.cx + b0, a0, self.cx + b1, a1)


# --------------------------------------------------------------------------
# Junctions: four arms
# --------------------------------------------------------------------------

_DIRECTIONS = {"UP": "u", "DOWN": "d", "LEFT": "l", "RIGHT": "r", "VERTICAL": "ud", "HORIZONTAL": "lr"}
_WEIGHTS = {"LIGHT": LIGHT, "SINGLE": LIGHT, "HEAVY": HEAVY, "DOUBLE": DOUBLE}
_OPPOSITE = {"l": "r", "r": "l", "u": "d", "d": "u"}
#: The arms that cross an arm: the one on its upper or right side, then the one on its lower or left side.
_ACROSS = {"l": "ud", "r": "ud", "u": "rl", "d": "rl"}


def _arms(name: str) -> dict:
    """The four arms of a junction, from its Unicode name without ``BOX DRAWINGS``.

    The name is a list of groups joined by AND. A group names directions and may name a
    weight, before or after them; a group without a weight has the weight of the group before.
    """
    arms = dict.fromkeys("udlr", NONE)
    weight = NONE
    for group in name.split(" AND "):
        words = group.split()
        for word in words:
            weight = _WEIGHTS.get(word, weight)
        for word in words:
            for arm in _DIRECTIONS.get(word, ""):
                arms[arm] = weight
    return arms


def _lines(arms: dict, arm: str, t: float) -> list:
    """The lines of one arm: (side, side, stop) for each.

    The sides are measured from the center of the cell. ``stop`` is where the line ends,
    measured from the center along the arm: above zero it ends before the center, below
    zero it runs past it. None means that it runs on into the arm opposite.
    """
    w, opposite = arms[arm], arms[_OPPOSITE[arm]]
    upper, lower = (arms[a] for a in _ACROSS[arm])
    if DOUBLE not in arms.values():
        # light and heavy lines: an arm runs to the far edge of the lines it meets, which makes a square corner
        if opposite == w:
            return [(-w * t / 2, w * t / 2, None)]
        stop = -max(upper, lower) * t / 2
        if opposite > w:
            stop = min(stop, -t / 2)             # a light arm ends inside the heavy arm opposite
        return [(-w * t / 2, w * t / 2, stop)]
    if w == LIGHT:
        # a single line that meets double lines: it stops at the first of a pair that runs through,
        # and runs to the far side of a pair that turns a corner with it
        if opposite:
            return [(-t / 2, t / 2, None)]
        return [(-t / 2, t / 2, (0.5 if upper and lower else -1.5) * t)]
    out = []
    for side, near, far in ((1, upper, lower), (-1, lower, upper)):
        if near == DOUBLE:
            stop = 0.5 * t                       # turn the corner into the double arm on this side
        elif opposite:
            stop = None
        elif near == LIGHT:
            stop = -0.5 * t                      # the far edge of a single line
        else:
            stop = {DOUBLE: -1.5, LIGHT: -0.5, NONE: 0.0}[far] * t      # the outside of a corner
        out.append((side * t - t / 2, side * t + t / 2, stop))
    return out


def _junction(c: _Cell, arms: dict):
    for first, second in ("lr", "du"):
        edge0, center, edge1 = c.span(first)
        if arms[first]:
            for b0, b1, stop in _lines(arms, first, c.t):
                if stop is None:
                    c.line(first, edge0, edge1, b0, b1)          # one line for both arms
                else:
                    c.line(first, edge0, center - stop, b0, b1)
        if arms[second]:
            for b0, b1, stop in _lines(arms, second, c.t):
                if stop is not None:
                    c.line(second, center + stop, edge1, b0, b1)


# --------------------------------------------------------------------------
# Dashes, arcs and diagonals
# --------------------------------------------------------------------------

def _dashes(c: _Cell, count: int, heavy: bool, vertical: bool):
    """``count`` dashes with half a gap at each end of the cell, so a row of cells has an even rhythm."""
    arm = "u" if vertical else "r"
    edge0, _, edge1 = c.span(arm)
    step = (edge1 - edge0) / count
    gap = step * DASH_GAP
    half = c.t * (2 if heavy else 1) / 2
    for i in range(count):
        c.line(arm, round(edge0 + i * step + gap / 2), round(edge0 + (i + 1) * step - gap / 2), -half, half)


def _arc(c: _Cell, right: bool, up: bool):
    """A light line that turns a round corner between a vertical and a horizontal arm.

    The radius is half the cell width, so the curve ends at the edge of the cell, where
    it is level. The vertical arm is straight from the curve to its edge.
    """
    half = c.t / 2
    sx, sy = (1 if right else -1), (1 if up else -1)
    rx = (c.w - c.cx) if right else c.cx
    reach = (c.top - c.cy) if up else (c.cy - c.bottom)
    ry = min(rx, reach)

    def at(h, v):
        # h runs from the center toward the edge of the horizontal arm, v toward the edge of the vertical arm
        return complex(c.cx + sx * h, c.cy + sy * v)

    contour = [
        (at(-half, reach), at(-half, ry)),
        (at(-half, ry), at(-half, ry - ARC * (ry + half)), at(rx - ARC * (rx + half), -half), at(rx, -half)),
        (at(rx, -half), at(rx, half)),
        (at(rx, half), at(rx - ARC * (rx - half), half), at(half, ry - ARC * (ry - half)), at(half, ry)),
        (at(half, ry), at(half, reach)),
        (at(half, reach), at(-half, reach)),
    ]
    c.contours.append(contour if sx * sy < 0 else reverse_contour(contour))


def _diagonal(c: _Cell, rising: bool):
    """A light line from corner to corner, cut off at the edges of the cell."""
    half = c.t / 2
    length = math.hypot(c.w, c.h)
    dx, dy = round(half * length / c.h), round(half * length / c.w)
    x0, x1 = (0.0, c.w) if rising else (c.w, 0.0)
    s = 1 if rising else -1
    c.polygon([(x0, c.bottom), (x0, c.bottom + dy), (x1 - s * dx, c.top),
               (x1, c.top), (x1, c.top - dy), (x0 + s * dx, c.bottom)])


# --------------------------------------------------------------------------
# Blocks, shades and quadrants
# --------------------------------------------------------------------------

_SHARES = {"ONE EIGHTH": 1 / 8, "ONE QUARTER": 2 / 8, "THREE EIGHTHS": 3 / 8, "HALF": 4 / 8,
           "FIVE EIGHTHS": 5 / 8, "THREE QUARTERS": 6 / 8, "SEVEN EIGHTHS": 7 / 8}
_SHADES = {"LIGHT": 0.25, "MEDIUM": 0.50, "DARK": 0.75}
#: The shades are drawn on this many sub-cells across and up. Even numbers, so the pattern goes on in the next cell.
SHADE_GRID = (4, 8)


def _block(c: _Cell, side: str, share: float):
    """A block that fills ``share`` of the cell from one side."""
    x0, y0, x1, y1 = {"LOWER": (0, 0, 1, share), "UPPER": (0, 1 - share, 1, 1),
                      "LEFT": (0, 0, share, 1), "RIGHT": (1 - share, 0, 1, 1)}[side]
    c.rect(c.x(x0), c.y(y0), c.x(x1), c.y(y1))


def _shade(c: _Cell, share: float):
    """A regular pattern that covers ``share`` of the cell.

    Light: one small square in every sub-cell. Dark: the full cell with the same squares
    cut out. Medium: a checkerboard of squares of that size.
    """
    cols, rows = SHADE_GRID
    if share == 0.50:
        for j in range(rows * 2):
            for i in range(j % 2, cols * 2, 2):
                c.rect(c.x(i / (cols * 2)), c.y(j / (rows * 2)), c.x((i + 1) / (cols * 2)), c.y((j + 1) / (rows * 2)))
        return
    dark = share > 0.5
    if dark:
        c.rect(0, c.bottom, c.w, c.top)
    w, h = round(c.w / cols / 2), round(c.h / rows / 2)
    dx, dy = round((c.w / cols - w) / 2), round((c.h / rows - h) / 2)
    for j in range(rows):
        for i in range(cols):
            x, y = round(c.w * i / cols) + dx, c.y(j / rows) + dy
            c.rect(x, y, x + w, y + h, hole=dark)


def _quadrants(c: _Cell, parts: frozenset):
    """Quarters of the cell. Three of them are drawn as one shape."""
    xs = {"LEFT": (0.0, c.cx), "RIGHT": (c.cx, c.w)}
    ys = {"LOWER": (c.bottom, c.cy), "UPPER": (c.cy, c.top)}
    if len(parts) == 3:
        (v, h), = {(v, h) for v in ys for h in xs} - parts          # the empty quarter
        full_x, cut_x = (0.0, c.w) if h == "RIGHT" else (c.w, 0.0)
        full_y, cut_y = (c.bottom, c.top) if v == "UPPER" else (c.top, c.bottom)
        c.polygon([(full_x, full_y), (full_x, cut_y), (c.cx, cut_y), (c.cx, c.cy), (cut_x, c.cy), (cut_x, full_y)])
        return
    for v, h in sorted(parts):
        c.rect(xs[h][0], ys[v][0], xs[h][1], ys[v][1])


# --------------------------------------------------------------------------
# From a Unicode name to a recipe
# --------------------------------------------------------------------------

def _plan(name: str):
    """The drawing for one character: a function of the cell."""
    words = name.split()
    if name.startswith("BOX DRAWINGS "):
        words = words[2:]
        if "DASH" in words:
            count = {"DOUBLE": 2, "TRIPLE": 3, "QUADRUPLE": 4}[words[1]]
            return lambda c: _dashes(c, count, words[0] == "HEAVY", words[-1] == "VERTICAL")
        if "ARC" in words:
            return lambda c: _arc(c, "RIGHT" in words, "UP" in words)
        if "DIAGONAL" in words:
            # "upper right to lower left" rises from left to right; the cross is both lines
            both = "CROSS" in words
            rising = both or words[2:4] == ["UPPER", "RIGHT"]
            falling = both or words[2:4] == ["UPPER", "LEFT"]
            return lambda c: [_diagonal(c, r) for r, on in ((True, rising), (False, falling)) if on]
        arms = _arms(" ".join(words))
        return lambda c: _junction(c, arms)
    if words[-1] == "SHADE":
        return lambda c: _shade(c, _SHADES[words[0]])
    if words[0] == "QUADRANT":
        parts = frozenset(tuple(part.split()) for part in " ".join(words[1:]).split(" AND "))
        return lambda c: _quadrants(c, parts)
    if name == "FULL BLOCK":
        return lambda c: _block(c, "LOWER", 1)
    return lambda c: _block(c, words[0], _SHARES[" ".join(words[1:-1])])


def _recipe(draw):
    def recipe(g: G):
        c = _Cell(g)
        draw(c)
        lean = math.tan(math.radians(g.p.slant)) if g.p.slant else 0.0
        for contour in c.contours:
            if lean:
                # the engine slants every glyph; a box stays upright, or it would not join its neighbors
                contour = transform_contour(
                    contour, lambda q: complex(q.real - lean * (q.imag - g.p.xh / 2), q.imag))
            g.shape(contour)
        g.full_cell = True
        g.frame(c.w, 0, 0)
    return recipe


for _cp in range(0x2500, 0x25A0):
    BOX.add(f"uni{_cp:04X}", _cp)(_recipe(_plan(unicodedata.name(chr(_cp)))))
del _cp
