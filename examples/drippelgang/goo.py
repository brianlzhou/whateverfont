"""Goo poured over the letters: the color effect of Drippelgang (see font.py and BRIEF.md).

Each letter is dipped head first in goo. The top of every part of the letter (the stem and the dot of
an i are two parts) is coated down to a wavy line. Goo runs down the strokes from that line in drips.
A drip that reaches the bottom of a stroke hangs off it as a drop, if there is room below. Small parts
(a dot, an accent, a period, a dash) are coated whole.

Keys, bottom layer first:

- ``shade``: the whole silhouette, letter and goo. It shows as a thin shadow under the goo, and the
  engine kerns by this layer, so a drop keeps its distance from the next letter.
- ``letter``: the letter, less the shadow of the goo.
- ``goo``: the coat, the drips and the drops.
- ``shine``: a gloss streak on each coat and a spot on each drop.

``dipped(..., layered=False)`` gives one color: the letter and the goo as one silhouette.
"""

from __future__ import annotations

import math

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, flatten_contour, reverse_contour, transform_contour
from whateverfont.outline import circle, depths, difference, dilate, intersection, rect, union

#: The lowest a drop may reach, in font units: above the default bottom of the line (-260), so the
#: family needs no ``descent``.
FLOOR = -250.0


def polygon(points: list) -> list:
    """A closed polygon as a clockwise (ink) contour."""
    c = [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]
    return c if contour_area(c) < 0 else reverse_contour(c)


def moved(contours: list, dx: float, dy: float) -> list:
    return [transform_contour(c, lambda q: q + complex(dx, dy)) for c in contours]


def _inside(poly: list, q: complex) -> bool:
    hit = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a.imag > q.imag) != (b.imag > q.imag) and \
                q.real < a.real + (b.real - a.real) * (q.imag - a.imag) / (b.imag - a.imag):
            hit = not hit
    return hit


def parts(ink: list) -> list:
    """The separate parts of a letter, each as its outside contour with its counters."""
    level = depths(ink)
    polys = [flatten_contour(c, 2.0) for c in ink]
    outers = [i for i in range(len(ink)) if level[i] % 2 == 0 and polys[i]]
    groups = {i: [ink[i]] for i in outers}
    for i in range(len(ink)):
        if level[i] % 2 and polys[i]:
            owners = [j for j in outers if level[j] == level[i] - 1 and _inside(polys[j], polys[i][0])]
            if owners:
                groups[min(owners, key=lambda j: abs(contour_area(ink[j])))].append(ink[i])
    return list(groups.values())


def spans(polys: list, x: float) -> list:
    """The stretches of the vertical line at ``x`` that lie in the shape, from the bottom up."""
    ys = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (a.real <= x) != (b.real <= x):
                ys.append(a.imag + (b.imag - a.imag) * (x - a.real) / (b.real - a.real))
    ys.sort()
    return [(ys[i], ys[i + 1]) for i in range(0, len(ys) - 1, 2)]


def hspans(polys: list, y: float) -> list:
    """The stretches of the horizontal line at ``y`` that lie in the shape, from the left."""
    xs = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if (a.imag <= y) != (b.imag <= y):
                xs.append(a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def closed(contours: list, amount: float) -> list:
    """The shape grown and shrunk by the same amount: inside corners get round fillets."""
    try:
        return effects.erode(dilate(contours, amount), amount)
    except Exception:
        return contours


def _length(rng) -> float:
    """How far a drip runs down a stroke, before it is cut to the stroke: mostly short, a few long."""
    r = rng.random()
    if r < 0.40:
        return rng.uniform(40, 110)
    if r < 0.75:
        return rng.uniform(110, 260)
    return rng.uniform(260, 420)


def dipped(recipes, depth: float = 0.32, wave: float = 0.22, every: tuple = (120.0, 200.0),
           chance: float = 0.78, width: tuple = (0.42, 0.58), through: float = 0.3, hang: float = 120.0,
           foot: float = 45.0, puff: float = 7.0, shadow: tuple = (5.0, -13.0), cut: tuple = (0.0, -18.0),
           gloss: bool = True, layered: bool = True, seed: int = 0, names=None):
    """Letters dipped in goo. Keys: shade, letter, goo, shine (see the module).

    ``depth`` is how far the coat reaches down, as a share of the height of the part above the
    baseline. ``wave`` is how much its lower edge waves, as a share of that depth. A part gets about
    one drip for every ``every`` units of width (a range), times ``chance``, and ``width`` is the width
    of a drip as a share of the stem. A drip runs all the way down a stem, covers it, and hangs off
    its foot with probability ``through``. ``hang`` is the longest drop below an arm or a bar, and
    ``foot`` the longest below the baseline. ``puff`` swells the coat past the edge of the letter,
    ``shadow`` is where the goo's shadow falls on the letter, and ``cut`` is where the white line
    under the goo falls in the one-color letter.
    """

    def effect(g, ink):
        rng = effects.seed_for(g, seed)
        sw = g.sw
        whole = [flatten_contour(c, 2.0) for c in ink]
        coats, runs, drops, joins, spots = [], [], [], [], []

        for part in parts(ink):
            box = contour_bounds(part)
            if box is None:
                continue
            x0, y0, x1, y1 = box
            above = y1 - max(y0, min(0.0, y1 - 1))           # a descender does not count
            if y1 - y0 < 0.40 * g.xh and x1 - x0 < 2.6 * g.xh:
                coats.extend(part)                           # a dot, an accent, a period, a dash
                continue

            # The coat: the part above a wavy line, below the top of the part. In a lowercase letter
            # with an ascender, the line also follows the tops that stand at the x-height (the bowl of
            # b, the arch of h), so that they get the same coat as the n and o beside them.
            part_polys = [flatten_contour(c, 2.0) for c in part]
            period, phase = rng.uniform(150, 230), rng.uniform(0, 2 * math.pi)
            ripple, phase2 = rng.uniform(55, 85), rng.uniform(0, 2 * math.pi)
            tall = g.case == "lower" and y1 > 1.2 * g.xh
            low, high = 0.84 * g.xh, 1.1 * g.xh

            def edge(x):
                ref = y1
                if tall:
                    tops = [hi for _, hi in spans(part_polys, x)]
                    if tops and low <= max(tops) <= high:
                        ref = max(tops)
                reach = min(max(depth * (ref - max(y0, min(0.0, ref - 1))), 105.0), 215.0)
                return ref - reach * (1 + wave * math.sin(2 * math.pi * x / period + phase)
                                      + 0.35 * wave * math.sin(2 * math.pi * x / ripple + phase2))

            line = [complex(x, edge(x)) for x in _steps(x0 - 30, x1 + 30, 8)]
            line += [complex(x1 + 30, y1 + 400), complex(x0 - 30, y1 + 400)]
            coat = intersection(part, [polygon(line)])
            # a thin sliver where the wavy line just grazes a lower stroke reads as a glitch
            coat = [c for c in coat if contour_area(c) > 0 or not _thin(c, 0.11 * sw)]
            if not coat:
                coats.extend(part)
                continue
            coats.extend(coat)
            coat_polys = [flatten_contour(c, 2.0) for c in coat]

            def plan(here, w):
                """Where a drip at ``here`` starts, where it leaves the stroke, and whether that edge is flat.

                The whole width of the drip must be on the coat, and on the stroke below it: a drip
                at the edge of a stroke reads as an outline, not as goo.
                """
                xs = (here - 0.5 * w, here, here + 0.5 * w)
                lows = []
                for xx in xs:
                    s = spans(coat_polys, xx)
                    if not s:
                        return None
                    lows.append(min(lo for lo, _ in s))
                if max(lows) - min(lows) > 0.5 * w:
                    return None                              # a steep edge: goo slides off it
                exits = []
                for xx, low in zip(xs, lows):
                    run = [s for s in spans(part_polys, xx) if s[0] < low - 2 < s[1]]
                    exits.append(run[0][0] if run else low)
                inside = [e < low - 1 for e, low in zip(exits, lows)]
                if inside[1] != inside[0] or inside[1] != inside[2]:
                    return None                              # half on the stroke, half off it
                start = lows[1]
                # A round foot counts as flat: the drop hangs from its lowest point.
                return start, (max(exits) if inside[1] else start), max(exits) - min(exits) < 0.7 * w

            # Drips run down from the lowest coat at their x. Find every x a drip could start from,
            # then take a few of them, set apart: about one for every ``every`` units of width.
            w_mid = sum(width) / 2 * sw
            sites = [x for x in _steps(x0 + 0.3 * w_mid, x1 - 0.3 * w_mid, 10) if plan(x, w_mid)]
            want = (x1 - x0) / rng.uniform(*every) * chance
            want = int(want) + (rng.random() < want - int(want))
            chosen = []
            rng.shuffle(sites)
            for here in sites:
                if len(chosen) >= max(1, want):
                    break
                w = rng.uniform(*width) * sw
                if any(abs(here - x) < 0.5 * (w + v) + 0.35 * sw for x, v in chosen):
                    continue
                found = plan(here, w)
                if not found:
                    continue
                chosen.append((here, w))
                start, exit_y, flat = found
                inner = start - exit_y
                # Goo that runs all the way down a stroke covers its whole width: a narrow stream in
                # the middle of a stem split it in two at text sizes (the i and d read as two thin
                # strokes). The stroke is its narrowest span at a few heights, since where an arm
                # joins the stem of a k the span at one height holds the arm too.
                span = None
                if inner > 0 and flat and x1 - x0 >= 1.6 * sw:
                    # (not on a lone stem: an i, l, I or 1 with goo down to its foot read as a j)
                    across = [s for t in (0.25, 0.5, 0.75) for s in hspans(part_polys, exit_y + t * inner)
                              if s[0] - 1 < here < s[1] + 1]
                    if across:
                        span = min(across, key=lambda s: s[1] - s[0])
                        if span[1] - span[0] > 1.45 * sw:
                            span = None                      # a bar, not a stem (the bar of e)
                if inner <= 0 or (span and rng.random() < through):
                    length = inner + rng.uniform(0.45, 1.0) * hang     # down the stroke and off its foot
                else:
                    length = min(_length(rng) * (above / 700.0) ** 0.5, inner - 0.3 * w)

                if not flat and length > inner - 0.6 * w:
                    length = inner - 0.6 * w                 # a round edge: the drip stops above it
                if length < 0.3 * w:
                    continue
                if length <= inner - 0.3 * w:                # the drip ends on the stroke
                    runs.extend(intersection(union([rect(here - w / 2, start - length, here + w / 2, start + 6),
                                                    circle(here, start - length, 0.54 * w)]), part))
                    continue
                if inner > 0:
                    left, right = span
                    # up to the top of the part: the wavy coat leaves no sliver of letter at the sides
                    # and down past the exit, which is the highest point of a round foot: all of it
                    runs.extend(intersection([rect(left - 2, exit_y - 0.5 * sw, right + 2, y1 + 10)], part))
                    w = min(max(w, 0.72 * (right - left)), 0.85 * sw)

                # A drop below the stroke: how much room is there, down to the next ink or the floor?
                ceiling = FLOOR
                inside_letter = False
                for d in (-0.6 * w, 0, 0.6 * w):
                    for lo, hi in spans(whole, here + d):
                        if hi < exit_y - 2:
                            if hi > ceiling:
                                ceiling, inside_letter = hi, True
                free = exit_y - ceiling
                rb = w * rng.uniform(0.56, 0.64)
                if inside_letter:
                    room = 0.24 * free - rb                  # a counter: keep most of it open
                else:
                    room = free - rb - 24
                # Under the baseline a long drop reads as a descender (an i becomes a j at text
                # sizes), so a drop from a foot stays short.
                limit = foot if exit_y < 0.3 * g.xh else hang
                drop = min(length - inner, limit, room)
                if drop >= 0.35 * w:
                    yb = exit_y - drop
                    # The stream keeps the width of the drip, narrows a little, and ends in a round drop.
                    stream = polygon([complex(here - 0.5 * w, exit_y + 4), complex(here + 0.5 * w, exit_y + 4),
                                      complex(here + 0.4 * w, yb), complex(here - 0.4 * w, yb)])
                    drops.extend(closed(union([stream, circle(here, yb, rb)]), 0.25 * w))
                    joins.append(circle(here, exit_y, 0.95 * w))
                    if rb >= 22:
                        spots.append(circle(here - 0.36 * rb, yb + 0.30 * rb, 0.22 * rb))
                elif room >= 0.3 * w:
                    bead = 0.40 * w
                    drops.append(circle(here, exit_y - 0.15 * bead, bead))    # a drop about to fall
                    joins.append(circle(here, exit_y, 0.8 * w))

        if not coats:
            return
        coat = union(coats)
        if puff:
            coat = union(coat + intersection(dilate(coat, puff), dilate(ink, puff)))
        goo = union(coat + runs + drops)
        if joins:
            # Where a drop leaves a stroke, the goo flows into the corner.
            body = union(ink + goo)
            for amount in (0.24, 0.21, 0.18):
                try:
                    fill = intersection(difference(closed(body, amount * sw), body), union(joins))
                except Exception:
                    continue                     # Skia failed on this outline (the c): try a little less
                if fill:
                    goo = union(goo + fill)
                break
        silhouette = union(ink + goo)

        # In one color, the edge of the goo is a thin white line where its shadow would fall.
        line = difference(intersection(moved(goo, *cut), ink), goo)
        # Where the goo has a vertical edge the line has no width: Skia leaves hairlines there, alone
        # or on the end of a real line. Shrink and grow the line to drop them.
        if line:
            try:
                line = intersection(dilate(effects.erode(line, 3.0), 3.0), line)
            except Exception:
                pass
        line = [c for c in line if contour_area(c) < 0 and abs(contour_area(c)) > 60]
        plain = difference(silhouette, line) if line else silhouette
        if not layered:
            effects.redraw(g, plain)
            return

        shine = []
        if gloss:
            shine = _gloss(coat, sw, rng) + spots
        # The letter stops under the goo too, so the edge of the goo has no fringe of letter color.
        cast = union(moved(goo, *shadow) + goo)
        layers = [("shade", silhouette), ("letter", difference(ink, cast)), ("goo", goo)]
        if shine:
            shine = intersection(union(shine), goo)
            if shine:
                layers.append(("shine", shine))
        g.layers = layers
        # Programs that show no color get the one-color letter, and its box holds every layer.
        effects.redraw(g, plain)

    return effects.wrapped(recipes, effect, names=names)


def _thin(contour: list, amount: float) -> bool:
    """Whether a piece of ink vanishes when it is shrunk by ``amount``."""
    try:
        return not effects.erode([contour], amount)
    except Exception:
        return False


def _steps(a: float, b: float, step: float) -> list:
    n = max(1, int(math.ceil((b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def _gloss(coat: list, sw: float, rng) -> list:
    """A short gloss streak near the top left of each piece of coat that is large enough."""
    out = []
    for piece in coat:
        if contour_area(piece) >= 0 or abs(contour_area(piece)) < 3.2 * sw * sw:
            continue
        x0, y0, x1, y1 = contour_bounds([piece])
        try:
            room = effects.erode([piece], 0.24 * sw)
        except Exception:
            continue
        if not room:
            continue
        test = effects.inside(room)
        best, score = None, -1e9
        for x in _steps(x0, x1, 9):
            for y in _steps(y0, y1, 9):
                q = complex(x, y)
                s = y - 0.55 * (x - x0)
                if s > score and test(q):
                    best, score = q, s
        if best is None:
            continue
        length = min(max(0.30 * (x1 - x0), 0.30 * sw), 0.62 * sw)
        out.append(effects.brush_mark(best, complex(1, rng.uniform(0.05, 0.25)), length, 0.17 * sw, bend=-14))
    return out


def palette(letter: str, goo: str, shade: str, shine: str) -> dict:
    return {"shade": shade, "letter": letter, "goo": goo, "shine": shine}


# Each palette has the ground it is made for; BRIEF.md lists them.
PALETTES = {
    "Slime": palette(letter="#8D5CE0", goo="#8FE23C", shade="#3E1F6E", shine="#EEFFD2"),     # on #1C0E2B
    "Pumpkin": palette(letter="#F27E1A", goo="#FFD650", shade="#8E3407", shine="#FFF8DA"),   # on #120A05
    "Black Cat": palette(letter="#1D1622", goo="#FF7A18", shade="#000000", shine="#FFE3BD"),  # on white
    "Ghost": palette(letter="#EEEBE2", goo="#5EDDC8", shade="#3E6F78", shine="#F2FFFC"),     # on #0F1A2C
}
