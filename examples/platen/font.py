"""Platen: a monospaced slab serif after the portable typewriters of the 1960s.

The engine gives the slabs (``serif``), the round ends (``roundness``) and the cell. This file adds
what makes it a portable rather than an office machine: ball terminals on the curved strokes of
a c f j r and of some figures, and a typed @.
"""

from whateverfont import Axis, Family, H, mono
from whateverfont.geom import seg_tangent
from whateverfont.presets import preset
from ribbon import ribbon

SAMPLE = "Dear Margaret, the carriage return sticks again. Ribbon $2.95 & 12 sheets @ 4c."

# The typewriter preset: 600-unit cell, slabs 56 units long, round ends, low contrast.
# Weight 84 (the preset has 74) prints blacker, like a fresh ribbon; width 1.08 widens the
# letters that do not fill the cell (o, a, e, s, c), which is where a portable looks friendly.
BASE = preset("typewriter", weight=84, width=1.08)

RECIPES = mono()


# --------------------------------------------------------------------------
# Ball terminals
# --------------------------------------------------------------------------

#: glyph -> (stroke tag, which end): the terminals that end in a ball.
BALLS = {
    "a": ("roof", "end"), "c": ("c", "start"), "f": ("hook", "end"), "j": ("tail", "end"),
    "r": ("arm", "end"), "two": ("two", "start"), "three": ("upper", "end"),
    "six": ("stroke", "start"), "nine": ("stroke", "start"), "question": ("hook", "start"),
}
BALL = 1.34     #: the ball, in stems


def ball(g, tag: str, end: str):
    """A round ball on one end of the last stroke tagged ``tag``, set back so it caps the stroke."""
    stroke = [s for s in g.strokes if s.tag == tag][-1]
    if end == "end":
        p, u = stroke.nodes[-1].p, seg_tangent(stroke.segments()[-1], 1.0)
    else:
        p, u = stroke.nodes[0].p, -seg_tangent(stroke.segments()[0], 0.0)
    d = g.sw * BALL
    c = p - u * d * 0.52
    g.dot(c.real, c.imag, d, shape="round")


def with_ball(fn, tag, end):
    def recipe(g):
        fn(g)
        ball(g, tag, end)
    return recipe


for _name, (_tag, _end) in BALLS.items():
    _rec = RECIPES[_name]
    RECIPES[_name] = type(_rec)(_name, with_ball(_rec.fn, _tag, _end), _rec.unicode, _rec.case)


# --------------------------------------------------------------------------
# A typed @: a round a inside a ring that is drawn in one turn
# --------------------------------------------------------------------------

@RECIPES.add("at", "@", case="upper")
def at(g):
    k = max(0.64, min(0.95, 0.86 - 0.0065 * (g.p.weight - 84)))     # the ring is lighter than a stem, more so in bold
    t = g.sw * k
    w = 0.86 * g.p.mono
    top, bot = g.top(g.cap) - g.o, g.desc * 0.30
    cx, cy = w / 2, (top + bot) / 2
    rx, ry = (w - t) / 2, (top - bot) / 2
    # the a: a bowl and a stem, about half the size of the ring
    irx, iry = rx * 0.40, ry * 0.43
    icx = cx - rx * 0.06
    g.ring(icx - irx, cy - iry, icx + irx, cy + iry, scale=k)
    xs = icx + irx
    a0 = -18
    hook = g.epoint(cx, cy, rx, ry, a0)
    (g.path(xs, cy + iry, w=1.0)
     .to(xs, cy - iry * 0.55)
     .curve((xs, cy - iry * 1.25), (hook.real - rx * 0.14, cy - iry * 1.3), hook.real, hook.imag)
     .ellipse(cx, cy, rx, ry, a0, 360 - 58)
     .done(start=H, scale=k, tag="outer"))
    g.frame(w, 0.5, 0.5)


FAMILY = Family(
    name="Platen",
    description="A typewriter face: even strokes with round ends, slab serifs, ball terminals, and the wide, friendly letters of a portable.",
    base=BASE,
    recipes=RECIPES,
    # Bold slabs are shorter and lighter, so the counters of m, M and W keep some white.
    axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 56, "serif": 60},
                                                 700: {"weight": 112, "serif": 44, "serif_weight": 0.84}})],
    styles={"Regular": {}, "Light": {"wght": 300}, "Bold": {"wght": 700}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

# The same letters typed through a used cloth ribbon (ribbon.py): the ink spreads, the edges are
# uneven, each letter sits a little off the line in its own way, and dry spots show. Drawn a
# little lighter than the Regular, because the spread of the ink adds weight back.
INKED = Family(
    name="Platen Ribbon",
    description="Platen typed through an inked ribbon: heavier, softer edges, letters a little off the line.",
    base=BASE.but(weight=78),
    recipes=ribbon(RECIPES),
    styles={"Regular": {}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

DIRECTIONS = [FAMILY, INKED]
