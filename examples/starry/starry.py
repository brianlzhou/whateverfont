"""Paint for Starry: letters made of brush marks, and capitals set in a turning night sky.

Nothing here copies the painting. It uses three of its habits: short loaded marks that
follow the form, rings of light around every bright thing, and blues laid beside yellows.
"""

from __future__ import annotations

import math

from whateverfont import effects
from whateverfont.geom import contour_bounds, cross, dot, flatten_contour, left, transform_contour, unit
from whateverfont.glyph import G, Recipe, Recipes
from whateverfont.outline import circle, difference, dilate, intersection, rect, union

SKY = 6        # sky colors, dark to light: keys s0 to s5
GOLD = 4       # letter colors, deep to pale: keys g0 to g3


def letter_tone(along, across, x, y, rng):
    """Pale down the middle of each stroke, deep at its edges, with a slow pulse along it."""
    return 0.80 * (1 - abs(across)) ** 0.8 + 0.16 * math.sin(along / 70.0) + 0.08


def night_tone(along, across, x, y, rng):
    """For letters painted in blues: currents of light and dark that run with the stroke."""
    band = 0.5 + 0.5 * math.sin(across * 3.4 + along / 95.0)
    spark = 0.30 if (1 - abs(across)) > 0.72 and math.sin(along / 38.0) > 0.55 else 0.0
    return min(0.99, 0.10 + 0.52 * band + spark)


def painted(recipes: Recipes) -> Recipes:
    """Letters in the blues of the sky, with sparks of yellow down the middle. Keys: base, c0 to c5."""
    return effects.painted(recipes, colors=SKY, dab=(92, 27), density=1.15, wobble=6, tone=night_tone,
                           passes=3, edge=9)


def _nearest(points: list, p: complex) -> complex:
    best, best_d = points[0], 1e18
    for q in points:
        d = (q.real - p.real) ** 2 + (q.imag - p.imag) ** 2
        if d < best_d:
            best, best_d = q, d
    return best


def sky_tile(fn, index: int, size: float = 900.0, heavier: float = 1.12):
    """Wrap a capital recipe: the letter in gold on a square of turning sky."""

    def recipe(g: G):
        p = g.p
        rng = effects.seed_for(g, 11)
        # 1. the letter, a little heavier than in text, with its skeleton
        gl = G(p.but(weight=p.weight * heavier), g.name, "upper")
        gl.recipes = g.recipes
        fn(gl)
        letter = union(gl.outlines())
        b = contour_bounds(letter)
        if b is None:
            return
        y0 = -(size - p.cap) / 2
        y1 = y0 + size
        scale = min(1.0, (size - 190) / (b[2] - b[0]))
        mid = complex((b[0] + b[2]) / 2, p.cap / 2)
        to_tile = lambda q: complex(size / 2, p.cap / 2) + (q - mid) * scale
        letter = [transform_contour(c, to_tile) for c in letter]
        marks = [(transform_contour(c, to_tile), t)
                 for c, t in effects.stroke_marks(gl, (96, 30), 1.1, 6, letter_tone, rng)]

        # 2. the lights: the letter, and two or three stars in the corners
        edge = [q for c in letter for q in flatten_contour(c, 5.0)]
        in_letter = effects.inside(dilate(letter, 10))
        spots = [(0.16, 0.84), (0.85, 0.83), (0.84, 0.14), (0.15, 0.17)]
        rng.shuffle(spots)
        stars = []
        for fx, fy in spots:                              # try every corner until enough are free
            c = complex(size * (fx + rng.uniform(-0.04, 0.04)), y0 + size * (fy + rng.uniform(-0.04, 0.04)))
            if len(stars) < 2 + index % 2 and not in_letter(c) and abs(_nearest(edge, c) - c) > 62:
                stars.append((c, rng.uniform(26, 40), rng.choice((-1.0, 1.0))))
        wave = rng.uniform(0, math.tau)

        def sense(q: complex):
            """(direction, tone) of the sky at a point."""
            base = complex(1.0, 0.42 * math.sin(q.real / 150.0 + q.imag / 260.0 + wave))
            near = _nearest(edge, q)
            d = abs(q - near)
            w_letter = math.exp(-(d / 105.0) ** 2)
            around = left(unit(q - near))
            if dot(around, base) < 0:
                around = -around
            flow = base * (1 - w_letter) + around * w_letter * 2.2
            tone = 0.26 + 0.24 * math.sin(q.imag / 46.0 + 1.9 * math.sin(q.real / 170.0 + wave))
            if d < 118:                                   # rings of light around the letter
                tone = max(tone, 0.93 - 0.60 * (d / 118.0) + 0.10 * math.sin(d / 9.0))
            for c, r, spin in stars:
                ds = abs(q - c)
                w = math.exp(-(ds / (r * 4.2)) ** 2)
                flow = flow * (1 - w) + left(unit(q - c)) * spin * w * 2.2
                if ds < r * 4.4:
                    tone = max(tone, 0.99 - 0.70 * (ds / (r * 4.4)) + 0.10 * math.sin(ds / 8.0))
            return flow, tone

        sky = effects.field_marks((0, y0, size, y1), lambda q: sense(q)[0], spacing=(56, 28), dab=(92, 27),
                                  tone=lambda a, v, x, y, r: sense(complex(x * size, y0 + y * size))[1],
                                  rng=rng, keep=lambda q: not in_letter(q))
        tile = [rect(0, y0, size, y1, 34)]
        halo = dilate(letter, 16)
        g.layers = [("night", tile)]
        g.layers += effects.paint_layers(sky, SKY, rng, passes=3, clip=difference(tile, halo), prefix="s", jitter=0.10)
        cores = [circle(c.real, c.imag, r) for c, r, _ in stars]
        if cores:
            g.layers.append(("glow", [circle(c.real, c.imag, r * 1.55) for c, r, _ in stars]))
            g.layers.append(("star", cores))
        g.layers.append(("gold", letter))
        g.layers += effects.paint_layers(marks, GOLD, rng, passes=2, clip=dilate(letter, 7), prefix="g")
        # without color support: a dark square with the letter cut out of it
        for c in difference(tile, letter):
            g.shapes.append(("shape", c, None))
        g.frame(size, 0.25, 0.25)
        g.static_only = True

    return recipe


def initials(recipes: Recipes) -> Recipes:
    """Capitals on tiles of sky. Every other glyph is painted like the text face."""
    out = painted(recipes)
    names = [n for n, r in recipes.items() if r.case == "upper" and len(n) == 1 and n.isalpha()]
    for i, name in enumerate(names):
        rec = recipes[name]
        out[name] = Recipe(name, sky_tile(rec.plain or rec.fn, i), rec.unicode, rec.case, rec.plain or rec.fn)
    return out


def night(base: str, sky: list, gold: list, star: str = "#FFF3B0", glow: str = "#F2C84B") -> dict:
    """A palette: the dark under everything, six sky colors, four letter colors, the stars."""
    pal = {"base": base, "night": base, "gold": gold[0], "star": star, "glow": glow}
    pal.update({f"c{i}": c for i, c in enumerate(sky)})
    pal.update({f"s{i}": c for i, c in enumerate(sky)})
    pal.update({f"g{i}": c for i, c in enumerate(gold)})
    return pal
