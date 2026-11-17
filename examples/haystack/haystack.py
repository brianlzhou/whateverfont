"""Paint for Haystack: letters that stand in a field like stacks of hay, in changing light.

The idea comes from a series of paintings of one motif at many hours and seasons. The
drawing never changes. Only the palette does: noon, sunset, snow, dusk.
"""

from __future__ import annotations

import math

from whateverfont import effects
from whateverfont.geom import contour_bounds, transform_contour
from whateverfont.glyph import G, Recipe, Recipes
from whateverfont.outline import difference, dilate, rect, union

HAY = 5        # the stack, shadow side to lit side: keys h0 to h4
SKY = 4        # keys k0 (high) to k3 (at the horizon)
LAND = 4       # keys f0 (near) to f3 (far)


def lit(along, across, x, y, rng):
    """Lit from the upper left: the right side and the foot of every letter fall into shadow."""
    return 0.52 + 0.50 * (y - 0.5) - 0.62 * (x - 0.5) + 0.10 * math.sin(along / 40.0)


def painted(recipes: Recipes) -> Recipes:
    """Letters in short, broken touches. Keys: base, c0 to c4 (shadow to light)."""
    return effects.painted(recipes, colors=HAY, dab=(62, 29), density=1.12, wobble=24, tone=lit, passes=3, edge=10)


def field_tile(fn, index: int, size: float = 900.0, heavier: float = 1.14, horizon: float = 0.40):
    """Wrap a capital recipe: the letter as a stack standing in a field, under a band of sky."""

    def recipe(g: G):
        p = g.p
        rng = effects.seed_for(g, 5)
        gl = G(p.but(weight=p.weight * heavier), g.name, "upper")
        gl.recipes = g.recipes
        fn(gl)
        letter = union(gl.outlines())
        b = contour_bounds(letter)
        if b is None:
            return
        y0 = -(size - p.cap) / 2
        y1 = y0 + size
        yh = y0 + size * horizon
        scale = min(1.0, (size - 200) / (b[2] - b[0]))
        mid = complex((b[0] + b[2]) / 2, 0.0)
        to_tile = lambda q: complex(size / 2 - 20, 0.0) + (q - mid) * scale
        letter = [transform_contour(c, to_tile) for c in letter]
        marks = [(transform_contour(c, to_tile), t)
                 for c, t in effects.stroke_marks(gl, (64, 30), 1.1, 24, lit, rng)]
        # the shadow the stack throws on the ground, to the right and toward us
        shadow = union([transform_contour(c, lambda q: complex(q.real + 0.24 * q.imag + 16, -0.125 * q.imag - 4))
                        for c in letter])
        in_letter = effects.inside(dilate(letter, 8))
        in_shadow = effects.inside(shadow)

        sky = effects.field_marks(
            (0, yh, size, y1), lambda q: complex(1.0, 0.10 * math.sin(q.real / 120.0 + q.imag / 60.0)),
            spacing=(54, 28), dab=(70, 27), rng=rng, keep=lambda q: not in_letter(q),
            tone=lambda a, v, x, y, r: 0.92 - 0.80 * y + 0.10 * math.sin(x * 9.0 + y * 5.0))
        land = effects.field_marks(
            (0, y0, size, yh), lambda q: complex(1.0, -0.22 + 0.12 * math.sin(q.real / 90.0)),
            spacing=(52, 26), dab=(66, 26), rng=rng, keep=lambda q: not in_letter(q) and not in_shadow(q),
            tone=lambda a, v, x, y, r: 0.10 + 0.80 * y + 0.12 * math.sin(x * 11.0))
        shade = effects.field_marks(
            (0, y0, size, yh), lambda q: complex(1.0, -0.30), spacing=(40, 20), dab=(54, 20), rng=rng,
            keep=in_shadow, tone=lambda a, v, x, y, r: 0.5)

        tile = [rect(0, y0, size, y1, 34)]
        open_tile = difference(tile, dilate(letter, 5))
        g.layers = [("ground", tile)]
        g.layers += effects.paint_layers(sky, SKY, rng, passes=2, clip=open_tile, prefix="k", jitter=0.12)
        g.layers += effects.paint_layers(land, LAND, rng, passes=2, clip=open_tile, prefix="f", jitter=0.12)
        g.layers += effects.paint_layers(shade, 1, rng, passes=1, clip=open_tile, prefix="sh", jitter=0.0)
        g.layers.append(("base", letter))
        g.layers += effects.paint_layers(marks, HAY, rng, passes=3, clip=dilate(letter, 8), prefix="c")
        for c in difference(tile, letter):
            g.shapes.append(("shape", c, None))
        g.frame(size, 0.25, 0.25)
        g.static_only = True

    return recipe


def initials(recipes: Recipes) -> Recipes:
    """Capitals as stacks in a field. Every other glyph is painted like the text face."""
    out = painted(recipes)
    names = [n for n, r in recipes.items() if r.case == "upper" and len(n) == 1 and n.isalpha()]
    for i, name in enumerate(names):
        rec = recipes[name]
        out[name] = Recipe(name, field_tile(rec.plain or rec.fn, i), rec.unicode, rec.case, rec.plain or rec.fn)
    return out


def light(ground: str, sky: list, land: list, hay: list, shadow: str, under: str) -> dict:
    """A palette: one hour of the day. ``hay`` runs from the shadow side to the lit side."""
    pal = {"ground": ground, "base": under, "sh0": shadow}
    pal.update({f"k{i}": c for i, c in enumerate(sky)})
    pal.update({f"f{i}": c for i, c in enumerate(land)})
    pal.update({f"c{i}": c for i, c in enumerate(hay)})
    return pal
