"""Snow that settles on letters: a color effect written for this project.

Snow lies where a letter faces the open sky: on the tops, on the shoulders of n and m, and in
the cup of a u. Nothing settles under a roof, so the inside of an o stays clear. Each glyph
gets two layers, ``letter`` and ``snow``.
"""

from __future__ import annotations

from whateverfont import effects
from whateverfont.geom import contour_bounds, flatten_contour, transform_contour
from whateverfont.outline import circle, difference, dilate, intersection, union

SKY = 1600.0  # farther than any letter is tall


def moved(contours: list, dy: float) -> list:
    return [transform_contour(c, lambda q: q + 1j * dy) for c in contours]


def settled(shape: list, depth: float, least: float) -> list:
    """The top ``depth`` of ``shape`` as the sky sees it, where that layer is at least ``least`` thick."""
    # everything a letter covers when it falls straight down: its upper edge is what the sky sees
    cover = union(shape + effects.extrusion(shape, 0, -SKY))
    band = intersection(difference(cover, moved(cover, -depth)), shape)
    # an opening: steep sides leave thin slivers, and snow slides off those
    core = effects.erode(band, least / 2) if band else []
    return dilate(core, least / 2) if core else []


def lowest(points: list, x: float):
    """The lowest point of a polygon on the vertical line at ``x``, or None."""
    hits = []
    for a, b in zip(points, points[1:] + points[:1]):
        if (a.real <= x) != (b.real <= x):
            hits.append(a.imag + (b.imag - a.imag) * (x - a.real) / (b.real - a.real))
    return min(hits) if hits else None


def capped(recipes, depth: float = 112.0, puff: float = 18.0, lift: float = 22.0, drips: float = 0.8, names=None):
    """Letters with snow on them. Keys: letter, snow.

    ``depth`` is how deep the snow lies, ``puff`` how far it swells past the letter, ``lift``
    how far it stands above it, and ``drips`` how many lumps hang from its lower edge
    (1 = about one for every 100 units of width).
    """
    def effect(g, shape):
        rng = effects.seed_for(g, 11)
        snow = []
        for piece in settled(shape, depth, depth * 0.6):
            b = contour_bounds([piece])
            if b is None or (b[2] - b[0]) * (b[3] - b[1]) < depth * depth * 0.6:
                continue
            snow.append(piece)
            points = flatten_contour(piece, 2.0)
            width = b[2] - b[0]
            count = int(width / 100 * drips + rng.random() * 0.8)
            for i in range(count):
                # a lump on the lower edge, like snow about to slide off
                x = b[0] + width * (i + rng.uniform(0.25, 0.75)) / count
                y = lowest(points, x)
                if y is not None:
                    r = depth * rng.uniform(0.2, 0.3)
                    snow.append(circle(x, y + r * 0.3, r))
        if snow:
            snow = moved(dilate(union(snow), puff), lift)
            # nothing hangs in the air: keep the snow close to the letter
            snow = intersection(snow, dilate(shape, puff + lift))
        g.layers = [("letter", shape)] + ([("snow", snow)] if snow else [])
        g.letter_layer = "letter"          # retrace keeps a small dot the letter's color, not all snow
    return effects.wrapped(recipes, effect, names)
