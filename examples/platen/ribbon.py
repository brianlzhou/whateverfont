"""Typed through a cloth ribbon: the effect behind Platen Ribbon.

A typewriter prints by striking an inked fabric ribbon against the paper. Four things set that
print apart from a clean outline, and this effect draws each of them:

1. The ink spreads into the paper, so every stroke is a little heavier and corners fill in.
2. The edge is uneven: the weave of the ribbon and the grain of the paper break it up.
3. Each type slug is bent a little its own way, so a letter sits a few units off the line and
   leans a fraction of a degree. The same letter is off in the same way every time it is typed,
   which is what a real machine does.
4. Where the ribbon is dry, small voids show inside the strokes.

It only moves ink a few units, so the text still reads at 12 pixels.
"""

from __future__ import annotations

import math

from whateverfont import effects
from whateverfont.geom import contour_area, contour_bounds, rotate_about, apply_affine, seg_length, split_seg
from whateverfont.outline import difference, dilate, union


def _wobble(contours: list, rng, waves: list) -> list:
    """Move every point of the outline by a sum of smooth waves. ``waves`` is [(amount, length)]."""
    phases = [[rng.uniform(0, math.tau) for _ in range(4)] for _ in waves]
    step = min(length for _, length in waves) * 0.30

    def warp(q: complex) -> complex:
        x, y = q.real, q.imag
        dx = dy = 0.0
        for (amount, length), ph in zip(waves, phases):
            f = math.tau / length
            dx += amount * math.sin(x * f * 0.9 + y * f * 1.3 + ph[0]) * 0.7
            dx += amount * 0.4 * math.sin(x * f * 2.1 - y * f * 1.6 + ph[1])
            dy += amount * math.sin(x * f * 1.2 - y * f * 0.8 + ph[2]) * 0.7
            dy += amount * 0.4 * math.sin(x * f * 1.7 + y * f * 2.4 + ph[3])
        return q + complex(dx, dy)

    out = []
    for c in contours:
        pieces = []
        for seg in c:
            n = max(1, int(seg_length(seg) / step))
            rest = seg
            for k in range(n, 1, -1):              # cut long segments so that they can bend
                head, rest = split_seg(rest, 1.0 / k)
                pieces.append(head)
            pieces.append(rest)
        out.append([tuple(warp(q) for q in (s if len(s) == 4 else
                                            (s[0], s[0] + (s[1] - s[0]) / 3, s[0] + (s[1] - s[0]) * 2 / 3, s[1])))
                    for s in pieces])
    return out


def _speck(c: complex, rx: float, ry: float, angle: float) -> list:
    """A small ellipse, turned by ``angle`` degrees: a dry spot where a thread of the ribbon lay."""
    k = 0.5523
    pts = [complex(rx, 0), complex(0, ry), complex(-rx, 0), complex(0, -ry)]
    hs = [complex(0, ry * k), complex(-rx * k, 0), complex(0, -ry * k), complex(rx * k, 0)]
    turn = complex(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    out = []
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        out.append(tuple(c + q * turn for q in (a, a + hs[i], b - hs[(i + 1) % 4], b)))
    return out


def ribbon(recipes, spread: float = 7.0, edge: float = 3.2, grain: float = 1.4, drift: float = 7.0,
           lean: float = 0.9, voids: float = 1.0, seed: int = 0):
    """Letters typed through an inked ribbon.

    ``spread`` is how far the ink bleeds (units), ``edge`` and ``grain`` the coarse and the fine
    unevenness of the edge, ``drift`` how far a letter may sit off the line, ``lean`` how far it
    may turn (degrees), and ``voids`` how many dry spots it gets (1 is a used ribbon).
    """
    def effect(g, shape):
        rng = effects.seed_for(g, seed)
        b = contour_bounds(shape)
        ink = dilate(shape, spread) if spread > 0 else shape
        ink = _wobble(ink, rng, [(edge, 140.0), (grain, 34.0)])
        # the slug: off the line, and turned about its middle
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        m = rotate_about(rng.uniform(-lean, lean), cx, cy)
        dy = rng.uniform(-drift, drift)
        ink = [[tuple(apply_affine(m, q) + complex(0, dy) for q in seg) for seg in c] for c in ink]
        ink = union(ink)
        # dry spots: short specks along the weave of the ribbon, more of them in a large letter.
        # Most sit inside the stroke; a few bite into its edge.
        area = sum(-contour_area(c) for c in ink)
        n = int(rng.uniform(0.6, 1.4) * voids * area / 24000)
        deep = effects.inside(effects.erode(ink, g.sw * 0.30) or ink)
        near = effects.inside(effects.erode(ink, g.sw * 0.08) or ink)
        holes = []
        for i in range(n * 8):
            if len(holes) >= n:
                break
            q = complex(rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3]))
            if (near if i % 4 == 0 else deep)(q):
                r = rng.uniform(0.05, 0.11) * g.sw
                holes.append(_speck(q, r * rng.uniform(1.4, 2.6), r * rng.uniform(0.45, 0.8),
                                    rng.choice((28.0, -28.0)) + rng.uniform(-12, 12)))
        if holes:
            ink = difference(ink, holes)
        effects.redraw(g, [c for c in ink if abs(contour_area(c)) > 20])

    # Box drawings and block elements stay clean: they must join from one cell to the next.
    names = [n for n, rec in recipes.items()
             if "comb" not in n and not (rec.unicode is not None and 0x2500 <= rec.unicode <= 0x259F)]
    return effects.wrapped(recipes, effect, names)
