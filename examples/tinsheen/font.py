"""Tinsheen: heavy, slanted letters of polished chrome, for a logo of one or two words.

The effect in chrome.py, next to this file, stacks flat color layers on every glyph: a dark outline,
bands of ground and sky that meet at one horizon, and a bright rim. Its palettes are the chrome itself,
gold, and two loud ones; chrome.GROUNDS names the ground each one is drawn for.
"""

import math

from whateverfont import H, Family, latin
from whateverfont.geom import contour_bounds
from whateverfont.presets import preset
from whateverfont.recipes.accents import mark
from whateverfont.recipes.figures import fig_advance, fig_w
from whateverfont.recipes.lower import SPUR, open_angle

from chrome import PALETTES, chrome, chrome_line

STOCK = latin()
SET = latin()


def ringed_capital(base):
    """A capital with a ring above it, drawn with a lighter stroke than the stock ring, which closes up
    in a heavy weight (Å would read as Ȧ)."""
    def recipe(g):
        g.base(base, STOCK[base].fn)(g)
        b = contour_bounds(g.outlines())
        mark(g, "ring", (b[0] + b[2]) / 2, True, box=(g.cap * 1.10, g.cap * 0.18, 0, 0.5))
    return recipe


SET.add("Aring", "Å", case="upper")(ringed_capital("A"))
SET.add("Uring", "Ů", case="upper")(ringed_capital("U"))


@SET.add("ampersand", "&", case="upper")
def ampersand(g):
    """The stock ampersand with a wider upper loop drawn at one even width.

    In a heavy weight the stock loop is tight, its stroke swells at the sides and thins at the ends,
    and the inside of the loop gets small steps. Here every node of the upper loop has the same width,
    and the stroke that enters the loop arrives along the loop's own tangent.
    """
    w = g.capw(1.22, 1.22) + g.sw
    top, bot = g.top(g.cap), g.bot
    ux0, ux1 = w * 0.17, w * 0.64                      # stock: 0.20 and 0.62
    uy0 = g.cap * 0.55
    ucx, ucy = (ux0 + ux1) / 2, (top + uy0) / 2
    urx, ury = (ux1 - ux0) / 2, (top - uy0) / 2
    lx0 = g.rw / 2
    lcy = bot + g.cap * 0.25
    lrx, lry = w * 0.40, g.cap * 0.25
    lcx = lx0 + lrx
    pe = g.epoint(ucx, ucy, urx, ury, -40)
    ps = complex(w * 0.98, g.cap * 0.02)
    loop = 0.8
    side = g.p.round_weight
    (g.path(ps.real, ps.imag, fl=0.8)
     .curve((w * 0.74, g.cap * 0.28), (ux0, ucy - ury * 0.9), ux0, ucy, w=loop)
     .ellipse(ucx, ucy, urx, ury, 180, -40, w=loop, w_side=loop, w_top=loop)
     .curve((pe.real - urx * 0.5, pe.imag - ury * 0.6), (lx0, lcy + lry * 1.3), lx0, lcy, w=side)
     .ellipse(lcx, lcy, lrx, lry, 180, 360 + 40, fl=0.8, w_top=side)
     .done(start=H, end=g.curved_cut(), tag="amp"))
    g.frame(None, 0.5, 0.3)


@SET.add("a", "a")
def a(g):
    """The stock two-story a, with a longer handle where the bowl reaches its left side. With the stock
    handle the curve turns so fast there that, in a heavy weight, the inside of the bowl gets a step."""
    w = g.sw + g.cw * 0.86 * (1 + (g.p.round_width - 1) * 0.6) + g.rw * 0.9
    R = w - g.L
    top, bot = g.top(g.xh), g.bot
    ry = g.xh * 0.33
    ysh = top - ry
    rx = (R - g.rw * 0.5) * 0.5
    at = 180 - open_angle(g, 22, 44)
    (g.path(R, 0, fl=1.0)
     .flared_from(R, ysh)
     .ellipse(R - rx, ysh, rx, ry, 0, at, fl=1.0)
     .done(start=H, end=g.curved_cut(), round_start=0.0 if g.serifed else None, tag="roof"))
    g.slab(R, 0, 0, SPUR, half=g.sw / 2 * g.fl)
    xl = g.rw / 2
    ytj = g.xh * 0.585
    ybj = g.xh * 0.16
    yc = (ytj + bot) / 2 - g.xh * 0.02
    xm = xl + (R - xl) * 0.5
    (g.path(R, ytj, g.p.join)
     .arc(xl, yc, "h", w=0.9, k0=0.62, k1=0.78)          # stock: w=round_weight, k0=0.72, k1=0.6
     .arc(xm, bot, "v", k0=0.70)
     .arc(R, ybj, "h", w=g.p.join, k0=0.62, k1=0.42)
     .done(tag="bowl"))
    g.frame(w, 0.6, "s")


def s_spine(g, x0, x1, y0, y1, side=0.86):
    """The stock spine of S, s and $, a little lighter where each bowl turns into the spine.

    In a wide, heavy letter the stroke turns faster than it is thick there, and the inside of each bowl
    gets a small spur. ``side`` is the width at those two points (stock: 1.0 and round_weight).
    """
    wbox = x1 - x0
    ym = (y0 + y1) / 2 + (y1 - y0) * 0.012
    ux0, ux1 = x0 + wbox * 0.035, x1 - wbox * 0.035
    ucx, ury = (ux0 + ux1) / 2, (y1 - ym) / 2
    urx = (ux1 - ux0) / 2
    ucy = y1 - ury
    lcx, lry = (x0 + x1) / 2, (ym - y0) / 2
    lrx = wbox / 2
    lcy = y0 + lry
    a0 = open_angle(g, 28, 48)
    a1 = open_angle(g, 26, 44)
    slope = math.atan2(lry + ury, wbox) * 0.62
    d = complex(math.cos(slope), -math.sin(slope))
    spine = g.sw * (0.96 - 0.0022 * max(0.0, g.p.weight - 82.0))
    ws = min(1.5, spine / g.thick(d))
    boost = 1 + (g.p.superk / 0.5523 - 1) * 0.45
    k = 0.5523 * boost
    p0 = g.epoint(ucx, ucy, urx, ury, a0)
    mid = (ux0 + ux1 + x0 + x1) / 4
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(ucx, ucy, urx, ury, a0, 180, w=side, boost=boost, boost_all=True)
     .curve((ux0, ucy - ury * k), (lcx - d.real * wbox * 0.30, ym - d.imag * wbox * 0.30), mid, ym, w=ws)
     .curve((mid + d.real * wbox * 0.30, ym + d.imag * wbox * 0.30), (x1, lcy + lry * k), x1, lcy, w=side)
     .ellipse(lcx, lcy, lrx, lry, 0, -(180 - a1), fl=1.0, boost=boost, boost_all=True)
     .done(start=g.curved_cut(), end=g.curved_cut(), tag="s"))


@SET.add("S", "S", case="upper")
def S(g):
    x0 = g.rw / 2
    s_spine(g, x0, x0 + g.capw(0.92, 0.80) + g.sw * 0.3, g.bot, g.top(g.cap))
    g.frame(None, 0.45, 0.45)


@SET.add("s", "s")
def s(g):
    x0 = g.rw / 2
    s_spine(g, x0, x0 + g.cw * 0.86 * g.p.round_width + g.sw * 0.32, g.bot, g.top(g.xh), side=0.76)
    g.frame(None, 0.42, 0.42)


@SET.add("dollar", "$", case="figure")
def dollar(g):
    x0 = g.rw / 2
    x1 = x0 + g.cw * 0.92 + g.sw * 0.3
    s_spine(g, x0, x1, g.bot, g.top(g.cap))
    g.stem((x0 + x1) / 2, -g.cap * 0.11, g.cap * 1.11, b=0, t=0, w=0.62)
    g.fixed_advance(fig_advance(g))


@SET.add("three", "3", case="figure")
def three(g):
    """The stock 3 with a short bar where its two bowls meet. In a heavy weight the square ends of the two
    bowls stick out of each other there, as a stepped point and a notch in the lower counter."""
    x0 = g.rw / 2
    x1 = x0 + fig_w(g)
    bot, top = g.bot, g.top(g.cap)
    ym = g.cap * 0.53
    urx, ury = (x1 - x0) / 2 * 0.90, (top - ym) / 2
    lrx, lry = (x1 - x0) / 2, (ym - bot) / 2
    ucx = x1 - (x1 - x0) * 0.06 - urx
    lcx = x1 - lrx
    a0 = 180 - open_angle(g, 26, 42)
    a1 = -(180 - open_angle(g, 24, 40))
    ps = g.epoint(ucx, top - ury, urx, ury, -104)
    (g.path(ps.real, ps.imag, 0.85)
     .ellipse(ucx, top - ury, urx, ury, -104, a0, fl=1.0, w_side=1.0)
     .done(end=g.curved_cut(), tag="upper"))
    qs = g.epoint(lcx, bot + lry, lrx, lry, 104)
    (g.path(qs.real, qs.imag, 0.85)
     .ellipse(lcx, bot + lry, lrx, lry, 104, a1, fl=1.0, w_side=1.0)
     .done(end=g.curved_cut(), tag="lower"))
    g.bar(min(ps.real, qs.real) - g.sw * 0.05, max(ucx, lcx), ym, w=0.9)
    g.fixed_advance(fig_advance(g))


def six_shape(g, share=0.29):
    """The stock 6 with a smaller bowl (``share`` of the cap height; stock: 0.315). In a heavy weight the
    stock hook touches the bowl and leaves a narrow closed slot; here the slot stays open."""
    x0 = g.rw / 2
    x1 = x0 + fig_w(g)
    bot, top = g.bot, g.top(g.cap)
    ry = g.cap * share
    g.ring(x0, bot, x1, bot + 2 * ry)
    brx, bry = (x1 - x0) / 2 * 1.04, (top - bot) / 2
    cx, cy = x0 + brx, (top + bot) / 2
    a0 = open_angle(g, 52, 64)
    p0 = g.epoint(cx, cy, brx, bry, a0)
    (g.path(p0.real, p0.imag, fl=1.0)
     .ellipse(cx, cy, brx, bry, a0, 180)
     .to(x0, bot + ry, w=g.p.round_weight)
     .done(start=g.curved_cut(), tag="stroke"))
    return x0, x1


@SET.add("six", "6", case="figure")
def six(g):
    six_shape(g)
    g.fixed_advance(fig_advance(g))


@SET.add("nine", "9", case="figure")
def nine(g):
    x0, x1 = six_shape(g)
    g.rotate(180, (x0 + x1) / 2, g.cap / 2)
    g.fixed_advance(fig_advance(g))


# Heavy, wide and slanted. Weight 170 is the heaviest that stays clean with the letters redrawn above:
# at 182 the 5, 6 and 9 close up and the & crumples, at 196 the a and the 8 get notches too. A wide
# width and a large counter keep the bowls open; spacing 1.15 leaves room for the outline.
BASE = preset("grotesk", weight=170, width=1.24, slant=10, counter=330, xh=540, superness=0.3,
              contrast=0.9, aperture=0.45, spacing=1.15)

FAMILY = Family(
    name="Tinsheen",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="Heavy, slanted letters of polished chrome: a pale sky over a sharp horizon, dark ground "
                "below it, a bright rim and a dark outline.",
    base=BASE,
    recipes=chrome(SET),
    styles={"Regular": {}},
    sample="High Score",
    palettes=PALETTES,
    ascent=975,                 # room for the outline round the marks of capitals (Ä Ǘ)
)

LINE = Family(
    name="Tinsheen Line",
    designer="WhateverFont examples", copyright="Copyright 2026 Brian Zhou",
    description="The same letters hollow: a chrome tube along the edge of each letter, with the ground "
                "showing through.",
    base=BASE,
    recipes=chrome_line(SET),
    styles={"Regular": {}},
    sample="Insert Coin",
    palettes=PALETTES,
    ascent=975,
)

DIRECTIONS = [FAMILY, LINE]
