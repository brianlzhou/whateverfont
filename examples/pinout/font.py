"""Pinout: a monospaced face for datasheets, terminal manuals and machine listings, 1975 to 1985."""

from whateverfont import Axis, Family, H, V, mono
from whateverfont.presets import preset
from whateverfont.recipes import lower, upper
from whateverfont.recipes.lower import arch, bowl, n_width, _bowl_width

SAMPLE = "PIN 14  VCC  +5V +/-0.25V  ICC 80mA MAX  [0x3F] -> {CLK, /RESET}"

# Square rounds, flat horizontal cuts, sharp corners and a narrow 560-unit cell. A tall x-height
# keeps lowercase readable at the small sizes of a table in a manual.
BASE = preset("technical", mono=560, weight=80, superness=0.80, roundness=0.0, contrast=0.9, xh=548, cap=700,
              asc=740, desc=-210, counter=270, width=0.92, aperture=0.42, apex=0.9, join=0.82,
              cut="horizontal", a_story=1, dot="square", kerning=0)

RECIPES = mono()
r = RECIPES.add


def _hooked_stem(g, x: float, top: float, reach: float):
    """A stem from ``top`` down past the baseline, turning left in a square hook on the descender."""
    rr = min(reach, (g.xh - g.desc) * 0.22)
    (g.path(x, top, fl=1.0)
     .flared_from(x, g.dbot + rr)
     .arc(x - rr, g.dbot, "v")
     .to(x - reach, g.dbot)
     .done(start=H, end=V, tag="hook"))


@r("g", "g")
def g_(g):
    """A single-story g whose stem drops straight and turns in a square hook: the y has the same one."""
    w = _bowl_width(g)
    R = w - g.L
    bowl(g, R, g.rw / 2)
    _hooked_stem(g, R, g.xh, R - g.rw * 0.55)
    g.frame(w, "r", "s")


@r("y", "y")
def y(g):
    """A u whose right stem runs on into the descender: no diagonals, so it stays square."""
    w = n_width(g)
    start = len(g.strokes)
    arch(g, g.L, w - g.L)
    g.rotate(180, w / 2, g.xh / 2, start=start)
    _hooked_stem(g, w - g.L, g.xh, w - g.L * 2)
    g.frame(w, "s", "s")


@r("l", "l")
def l(g):
    """A flag at the top and a foot that turns right in a square corner."""
    w = 0.70 * g.p.mono
    xs = 0.40 * w
    rr = 0.16 * w
    yb = g.hw / 2
    g.bar(0, xs, g.flat_top(g.asc), l=0.5)
    (g.path(xs, g.asc)
     .to(xs, yb + rr)
     .arc(xs + rr, yb, "v")
     .to(w, yb)
     .done(start=H, end=V))
    g.frame(w, 0.5, 0.5)


@r("M", "M", case="upper")
def M(g):
    """The V of the M stops at a third of the height, so the four strokes do not fill a narrow cell."""
    upper.em(g, vertex=0.34, thin=0.80)


@r("W", "W", case="upper")
def W(g):
    upper.double_vee(g, middle=0.64, thin=0.80)


@r("w", "w")
def w_(g):
    lower.double_vee(g, middle=0.70, thin=0.82)


@r("zero", "0", case="figure")
def zero(g):
    """A slashed zero: a stroke from corner to corner of the counter, so 0 and O never meet."""
    w = 0.80 * g.p.mono
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.cap))
    a, b = g.diagonal(g.rw * 0.95, g.cap * 0.16, w - g.rw * 0.95, g.cap * 0.84, "c", "c", w=0.7)
    g.line(a.real, a.imag, b.real, b.imag, w=0.7, cut0=H, cut1=H, tag="slash")
    g.frame(w, 0.5, 0.5)


FAMILY = Family(
    name="Pinout",
    description="A square monospace for datasheets and terminal manuals: flat cuts, slashed zero, hooked g and y.",
    base=BASE,
    recipes=RECIPES,
    axes=[Axis("wght", "Weight", 300, 400, 700, {300: {"weight": 52}, 700: {"weight": 122}})],
    styles={"Regular": {}, "Light": {"wght": 300}, "Bold": {"wght": 700}},
    sample=SAMPLE,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)
