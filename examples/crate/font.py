"""Crate Stencil: a heavy, slightly condensed stencil face for labels on shipping crates.

whateverfont has no stencil option, so this file wraps the Latin recipes. Each wrapped recipe draws the
letter as usual, then adds vertical bridges to the drawing's cutouts. A bridge is a strip of the
stencil sheet that holds a counter in place, so every closed counter must be crossed by one.
"""

import dataclasses

from whateverfont import Axis, Family, latin
from whateverfont.ornament import contour_bounds, rect
from whateverfont.presets import preset

SAMPLE = "FRAGILE — THIS SIDE UP — CRATE 07 OF 12 — PORT OF ROTTERDAM"

# Where each glyph gets a bridge. "L": just right of the left stem. "R": just left of the right stem.
# "M": through the middle of the drawing. A number: that fraction of the drawing's width. A tuple (where, low, high) limits the bridge to a band of
# heights, as fractions of the letter's own height (cap height or x-height); None means no limit.
BRIDGES = {
    # capitals
    "A": "M", "B": "L", "C": "M", "D": "L", "E": "L", "F": "L", "H": "LR", "K": "L",
    "L": "L", "M": "LR", "N": "LR", "O": "M", "P": "L", "Q": "M", "R": "L", "U": "M",
    "G": [("M", 0.62, None), ("M", None, 0.30)],   # top and bottom arcs only: keep the crossbar whole
    "Oslash": "M", "Aring": "M",                   # Aring does not inherit the A bridge
    # lowercase ("r" has no counter, and a bridge would leave its arm floating)
    "a": "R", "b": "L", "c": "M", "d": "R", "e": "M", "h": "L", "k": "L", "m": "L",
    "n": "L", "o": "M", "p": "L", "q": "R", "u": "R", "oslash": "M",
    "g": [("R", -0.12, None)],
    "aring": [("R", None, None), ("M", 1.08, None)],   # the a, then the ring                     # the bowl only: keep the tail on the stem
    # figures and signs
    "zero": "M", "four": "M", "six": "M", "eight": "M", "nine": "M",
    "ampersand": [("M", 0.62, None), ("M", None, 0.25)], "at": "M", "degree": "M", "numbersign": "M",
    "percent": [(0.22, 0.5, None), (0.78, None, 0.5)],   # one bridge through each ring
}


# Accented letters do not inherit the bridges of their base letter, so give each one the base letter's
# bridges, stopped just above the letter (1.03 of its height covers the overshoot) so the accent stays whole.
ACCENTS = ("grave", "acute", "circumflex", "tilde", "dieresis", "ring", "cedilla", "caron")


def with_accents(bridges, names):
    out = dict(bridges)
    for name in names:
        for accent in ACCENTS:
            base = name[: -len(accent)]
            if name.endswith(accent) and base in bridges and name not in bridges:
                cuts = bridges[base]
                if isinstance(cuts, str):
                    cuts = [(kind, None, None) for kind in cuts]
                out[name] = [(kind, low, 1.03 if high is None else high) for kind, low, high in cuts]
    return out


def stencil(recipes, bridges, gap=0.30, least=20):
    """A copy of ``recipes`` in which the glyphs named in ``bridges`` are cut by vertical bridges.

    ``gap`` is the bridge width as a fraction of the stem, with ``least`` units as the minimum.
    """
    out = recipes.copy()
    for name, cuts in with_accents(bridges, list(recipes.keys())).items():
        if name not in out:
            continue
        inner = out[name].fn
        if isinstance(cuts, str):
            cuts = [(kind, None, None) for kind in cuts]

        def cut(g, inner=inner, cuts=cuts):
            inner(g)
            x0, y0, x1, y1 = contour_bounds(g.outlines())
            height = g.cap if g.case == "upper" else g.xh
            w = max(least, gap * g.sw)
            for kind, low, high in cuts:
                if kind == "L":
                    cx = x0 + g.sw + w / 2
                elif kind == "R":
                    cx = x1 - g.sw - w / 2
                elif kind == "M":
                    cx = (x0 + x1) / 2
                else:
                    cx = x0 + kind * (x1 - x0)
                lo = y0 - 60 if low is None else low * height
                hi = y1 + 60 if high is None else high * height
                g.cutouts.append(rect(cx - w / 2, lo, cx + w / 2, hi))

        out[name] = dataclasses.replace(out[name], fn=cut)
    return out


RECIPES = stencil(latin(), BRIDGES)
WIDE_BRIDGES = stencil(latin(), BRIDGES, gap=0.45, least=30)

AXES = [
    Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 78}, 800: {"weight": 172, "counter": 300}}),
]
STYLES = {"Regular": {}, "Bold": {"wght": 700}}

# 1. The classic crate stencil: condensed grotesque, flat cuts, closed apertures.
FAMILY = Family(
    name="Crate Stencil",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="A heavy condensed grotesque with flat cuts and a bridge through every bowl, like a stencil "
                "cut for a shipping crate.",
    base=preset("condensed", weight=116, width=0.82, counter=292, xh=540, cap=696, cut="square", aperture=0.5, apex=0.4),
    recipes=RECIPES,
    axes=AXES,
    styles=STYLES,
    sample=SAMPLE,
)

# 2. Machine labels: squared rounds, wider, more technical.
SQUARE = Family(
    name="Crate Stencil Square",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Wider, with squared rounds and flat ends, like letters cut from sheet metal for machine "
                "markings.",
    base=preset("technical", weight=116, width=0.95, superness=0.85, counter=280, xh=540, cap=694, cut="square", aperture=0.45),
    recipes=RECIPES,
    axes=AXES,
    styles=STYLES,
    sample=SAMPLE,
)

# 3. Sprayed: round ends, open apertures, softer, as if the paint bled at the edges.
SPRAYED = Family(
    name="Crate Stencil Sprayed",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Narrower, with round ends, open curves and wide bridges, as if sprayed through a "
                "hand-cut card stencil.",
    base=preset("rounded", weight=116, width=0.70, roundness=1.0, aperture=0.65, counter=300, xh=530, cap=688),
    recipes=WIDE_BRIDGES,
    axes=AXES,
    styles=STYLES,
    sample=SAMPLE,
)

DIRECTIONS = [FAMILY, SQUARE, SPRAYED]
