"""Lowslung: a wide, flat sans for the name of a studio."""

import unicodedata

from whateverfont import Axis, Family, H, V
from whateverfont.glyph import Recipe
from whateverfont.stroke import Cap
from whateverfont.presets import preset
from whateverfont.recipes import latin
from whateverfont.recipes.figures import fig_advance, fig_w
from whateverfont.recipes.lower import n_width

SAMPLE = "Coachwork Studio"

RECIPES = latin()


#: The family's aperture is below 0, so c, e, s, C, G and S curl in until their ends point up or down
#: and the horizontal cut is square to the stroke. The hooks of f, j and J would curl too far with it:
#: they are drawn with this much more aperture.
HOOK_APERTURE = 0.8


def _with(fn, cut, aperture=0.0):
    """Draw a stock recipe with its curved ends cut along ``cut``, and ``aperture`` more aperture."""
    def draw(g):
        p = g.p
        g.p = p.but(cut=cut, aperture=p.aperture + aperture)
        try:
            fn(g)
        finally:
            g.p = p
    return draw


# Hooks that end traveling sideways get a vertical cut. A horizontal cut there runs almost along the
# stroke and leaves a spike, which grows with the weight.
# The t gets more than the others: its hook then ends nearly flat, and the vertical cut stays short in
# the heavy weights.
for _name, _more in (("r", 0.0), ("g", 0.0), ("t", 2.0), ("f", HOOK_APERTURE), ("j", HOOK_APERTURE),
                     ("dotlessj", HOOK_APERTURE), ("J", HOOK_APERTURE), ("florin", HOOK_APERTURE)):
    _rec = RECIPES[_name]
    RECIPES[_name] = Recipe(_name, _with(_rec.fn, "vertical", _more), _rec.unicode, _rec.case)


def _smaller_dot(fn, k=0.86):
    """Draw a stock recipe, then shrink the dots it drew about their centers. The stock dot of i and j
    is 1.16 stems wide; under a tall x-height it comes too close to the stem in the bold."""
    def draw(g):
        first = len(g.shapes)
        fn(g)
        for i in range(first, len(g.shapes)):
            kind, contour, radii = g.shapes[i]
            if kind != "dot":
                continue
            pts = [a for a, _ in contour]
            c = sum(pts) / len(pts)
            move = lambda q: c + (q - c) * k
            g.shapes[i] = (kind, [(move(a), move(b)) for a, b in contour],
                           None if radii is None else [r * k for r in radii])
    return draw


for _name in ("i", "j"):
    _rec = RECIPES[_name]
    RECIPES[_name] = Recipe(_name, _smaller_dot(_rec.fn), _rec.unicode, _rec.case)


def _six(g):
    """A 6 with a flat top: the bowl, then a stroke that rises on the left, turns and runs flat to a
    vertical cut. The stock 6 ends on a slope, which is a spike in a wide, heavy figure."""
    x0 = g.rw / 2
    x1, bot, top = x0 + fig_w(g), g.bot, g.top(g.cap)
    ry = g.cap * 0.31
    g.ring(x0, bot, x1, bot + 2 * ry)
    rx = (x1 - x0) / 2
    rv = min(ry, (top - bot - 2 * ry) * 0.9 + g.hw)
    xt = x1 - (x1 - x0) * 0.08
    (g.path(x0, bot + ry, w=g.p.round_weight)
     .to(x0, top - rv, w=g.p.round_weight)
     .arc(x0 + rx, top, "v")
     .to(xt, top, fl=0.6)
     .done(end=V, tag="stroke"))
    return x0, x1


@RECIPES.add("six", "6", case="figure")
def six(g):
    _six(g)
    g.fixed_advance(fig_advance(g))


@RECIPES.add("nine", "9", case="figure")
def nine(g):
    x0, x1 = _six(g)
    g.rotate(180, (x0 + x1) / 2, g.cap / 2)
    g.fixed_advance(fig_advance(g))


@RECIPES.add("germandbls", "ß")
def germandbls(g):
    """The stock sharp s, with the round at the top kept low. In a wide face the stock round is as
    tall as it is wide, reaches down past the waist and folds."""
    w = n_width(g) * 0.92
    x0 = g.L
    top = g.top(g.asc)
    xr = w - g.rw / 2
    xw = x0 + (xr - x0) * 0.42
    yw = g.xh * 0.70
    rx = (xr - x0) * 0.44
    ry = min(rx, (top - yw) * 0.42)
    (g.path(x0, 0, fl=1.0)
     .flared_from(x0, g.asc * 0.5)
     .to(x0, top - ry)
     .arc(x0 + rx, top, "v")
     .arc(x0 + rx * 2, top - ry * 1.05, "h", w=g.p.round_weight)
     .curve((x0 + rx * 2, top - ry * 1.8), (xw + (xr - xw) * 0.3, yw + g.xh * 0.06), xw, yw, w=0.8)
     .curve((xr, yw), (xr, g.xh * 0.55), xr, g.xh * 0.32, w=g.p.round_weight)
     .curve((xr, g.xh * 0.08), (xw + (xr - xw) * 0.5, g.bot), xw, g.bot)
     .done(start=H, end=V, tag="sharp"))
    g.frame(w + g.rw * 0.1, "s", "r")


def _straight(s) -> bool:
    """True for an open stroke whose nodes lie on one straight line (an acute, a grave)."""
    if s.closed or any(h is not None for h in s.handles):
        return False
    a, b = s.nodes[0].p, s.nodes[-1].p
    d = b - a
    return abs(d) > 0 and all(abs(((n.p - a) * d.conjugate()).imag) / abs(d) < 1.0 for n in s.nodes)


def _flat_marks(fn):
    """Draw a recipe, then give its marks the family's flat ends.

    The acute, the grave and the double acute are short slanted strokes. With square ends they turn
    into diamonds in the heavy weights; cut horizontally, they end flat like the letters. The ring of
    Å and ů is drawn thinner and, if its counter would close, larger.
    """
    def draw(g):
        fn(g)
        done = g.__dict__.setdefault("_flat_marks_done", set())
        slanted = []
        for s in g.strokes:
            if s.tag != "mark" or id(s) in done:
                continue
            done.add(id(s))
            if _straight(s):
                d = s.nodes[-1].p - s.nodes[0].p
                if abs(d.imag) > abs(d.real) * 0.5:
                    s.start, s.end = Cap(H, s.start.round), Cap(H, s.end.round)
                    slanted.append(s)
            elif s.closed:
                xs = [n.p.real for n in s.nodes]
                ys = [n.p.imag for n in s.nodes]
                cx, yb = (min(xs) + max(xs)) / 2, min(ys)
                s.scale *= 0.8
                t = s.scale * g.sw
                f = max(1.0, t * 1.9 / (max(xs) - min(xs)))
                move = lambda q: complex(cx + (q.real - cx) * f, yb + (q.imag - yb) * f)
                for n in s.nodes:
                    n.p = move(n.p)
                s.handles = [None if h is None else (move(h[0]), move(h[1])) for h in s.handles]
        # A double acute: two strokes side by side. Cut flat, each one is wider; keep a gap between them
        # at least half as wide as one stroke.
        if len(slanted) == 2 and abs(slanted[0].nodes[0].p.imag - slanted[1].nodes[0].p.imag) < 1:
            a, b = sorted(slanted, key=lambda s: s.nodes[0].p.real)
            d = a.nodes[-1].p - a.nodes[0].p
            wide = 2 * g.dx(d) * a.scale / g.k
            apart = b.nodes[0].p.real - a.nodes[0].p.real
            push = max(0.0, (wide * 1.5 - apart) / 2)
            for s, sign in ((a, -1), (b, 1)):
                for n in s.nodes:
                    n.p += sign * push
    return draw


def _has_mark(rec) -> bool:
    """A letter with an accent, a spacing accent or a combining mark: what unicode composes from a mark."""
    u = rec.unicode
    return u is not None and (0x0300 <= u <= 0x036F or bool(unicodedata.decomposition(chr(u))))


for _name, _rec in list(RECIPES.items()):
    if _has_mark(_rec):
        RECIPES[_name] = Recipe(_name, _flat_marks(_rec.fn), _rec.unicode, _rec.case, _rec.plain)


BASE = preset("grotesk", weight=90, cap_weight=1.05, width=1.45, xh=560, cap=700, asc=760, superness=0.68,
              contrast=0.9, counter=275, aperture=-0.6, spacing=1.22, word_space=1.2, apex=0.9)

FAMILY = Family(
    name="Lowslung",
    description="A wide sans for wordmarks and short headings, with squarish rounds and flat ends.",
    base=BASE,
    axes=[
        Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 58},
                                               800: {"weight": 156, "counter": 285, "arm": 1.15,
                                                     "aperture": -0.25}}),
        Axis("wdth", "Width", 70, 100, 125, {70: {"width": 1.0, "aperture": -0.3}, 125: {"width": 1.8}}),
    ],
    styles={"Light": {"wght": 300}, "Regular": {}, "Medium": {"wght": 500}, "Bold": {"wght": 700},
            "Extrabold": {"wght": 800}},
    recipes=RECIPES,
    ascent=955,
    sample=SAMPLE,
    figures="proportional",
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)
