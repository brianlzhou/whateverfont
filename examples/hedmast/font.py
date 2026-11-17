"""Hedmast: a tall, narrow, heavy sans for newspaper headlines."""

from whateverfont import Axis, Family, latin
from whateverfont.geom import contour_bounds
from whateverfont.presets import preset
from whateverfont.recipes.accents import mark

SAMPLE = "Late goal sinks leaders in the rain"

# A condensed grotesque: a tall x-height, flat-sided rounds, closed c e s at the regular weight, flat cuts
# (level on c e s, upright on the hooks of f t j and the arm of r), short descenders and tight spacing for
# stacked headlines.
BASE = preset("condensed", width=0.72, weight=92, cap_weight=1.08, xh=560, cap=720, asc=760, desc=-200,
              superness=0.55, contrast=0.84, counter=285, round_width=1.04, aperture=0.3, spacing=0.88,
              word_space=0.95, arm=0.95, cut="flat")

HEAVIEST = 146      # the stem of the heaviest weight; at 158 the s, the & and the 6 closed up
NARROWEST = 0.6     # the width at the narrow end of the width axis

FAMILY = Family(
    name="Hedmast",
    description="A tall, narrow sans for headlines: flat-sided rounds, a tall x-height, five weights up to "
                "a heavy, and a width axis.",
    base=BASE,
    axes=[
        # The heavy end opens the counters (counter 318), opens c e s (aperture 0.62), thins the
        # horizontals (contrast 0.74) and tightens the spacing.
        Axis("wght", "Weight", 400, 400, 800, {
            800: {"weight": HEAVIEST, "counter": 318, "aperture": 0.62, "arm": 1.05, "contrast": 0.74,
                  "spacing": 0.82, "cap_weight": 1.05, "round_weight": 1.01},
        }),
        Axis("wdth", "Width", 60, 75, 90, {60: {"width": NARROWEST}, 90: {"width": 0.88}}),
    ],
    styles={"Regular": {}, "Medium": {"wght": 500}, "Semibold": {"wght": 600}, "Bold": {"wght": 700},
            "Heavy": {"wght": 800}},
    sample=SAMPLE,
    ascent=960,
    designer="WhateverFont examples",
    copyright="Copyright 2026 Brian Zhou",
)

STOCK = latin()


def _heavy(g) -> float:
    """0 at the regular weight, 1 at the heaviest."""
    return min(1.0, max(0.0, (g.p.weight - BASE.weight) / (HEAVIEST - BASE.weight)))


def _narrow(g) -> float:
    """0 at the default width or wider, 1 at the narrowest width."""
    return min(1.0, max(0.0, (BASE.width - g.p.width) / (BASE.width - NARROWEST)))


# The dot of i and j. The stock dot sits at a fixed share of the ascender, so in the heavy weights its
# bottom comes down to 30 units over the stem and the i reads as an l at text sizes. Here the gap stays
# 0.11 of the x-height at every weight, and the dot gets a little smaller as the weight grows.
def _i_dot(g, x):
    d = g.sw * 1.16 * (1.0 - 0.15 * _heavy(g))
    g.dot(x, g.xh * 1.11 + d / 2, d)


@FAMILY.recipes.add("i", "i")
def i(g):
    n = len(g.shapes)
    STOCK["i"].fn(g)
    del g.shapes[n:]                        # the stock dot
    _i_dot(g, g.L)


@FAMILY.recipes.add("j", "j")
def j(g):
    n = len(g.shapes)
    STOCK["j"].fn(g)
    del g.shapes[n:]                        # the stock dot; dotlessj removes this one the same way
    _i_dot(g, contour_bounds(g.outlines())[2] - g.sw / 2)


# The places of the marks above a capital and above a lowercase letter, as the stock accents have them.
def _mark_box(g, upper: bool):
    """(bottom, height, half width) of a mark."""
    if upper:
        return g.cap * 1.075, g.cap * 0.15, g.p.n_counter * 0.30 + g.sw * 0.25
    return g.xh * 1.16, g.xh * 0.25, g.p.n_counter * 0.27 + g.sw * 0.25


# The dieresis over a narrow I or i. Its dots are as wide as a stem, so in the heavy weights they reach
# far past the letter. Here they shrink with the weight, to 0.83 of the usual size at the heaviest.
# Cyrillic Ї ї and Greek Ϊ draw these letters, so they follow.
def _narrow_dieresis(base: str, upper: bool):
    def recipe(g):
        g.base(base)(g)
        b = contour_bounds(g.outlines())
        y0, h, half = _mark_box(g, upper)
        mark(g, "dieresis", (b[0] + b[2]) / 2, upper, box=(y0, h, half, 0.80 - 0.14 * _heavy(g)))
    return recipe


FAMILY.recipes.add("Idieresis", "Ï", case="upper")(_narrow_dieresis("I", True))
FAMILY.recipes.add("idieresis", "ï")(_narrow_dieresis("dotlessi", False))


# The double acute of Ő ő Ű ű. Its two strokes stand close, and in a narrow letter they ran together.
# Here they stand 1.3 times as far apart (1.5 times at the heaviest) and get lighter as the weight grows.
def _double_acute(base: str, upper: bool):
    def recipe(g):
        g.base(base)(g)
        b = contour_bounds(g.outlines())
        k = _heavy(g)
        y0, h, half = _mark_box(g, upper)
        mark(g, "doubleacute", (b[0] + b[2]) / 2, upper, box=(y0, h, half * (1.3 + 0.2 * k), 0.80 - 0.10 * k))
    return recipe


for _ch, _base in (("Ő", "O"), ("ő", "o"), ("Ű", "U"), ("ű", "u")):
    FAMILY.recipes.add(f"{_base}doubleacute", _ch, case="upper" if _base.isupper() else "lower")(
        _double_acute(_base, _base.isupper()))


def _wider(name: str, base: float, heavy: float, narrow: float):
    """The stock recipe drawn with a wider counter: ``base`` more at the regular weight and the default
    width, ``heavy`` more at the heaviest weight, ``narrow`` more at the narrowest width."""
    def recipe(g):
        p = g.p
        g.p = p.but(counter=p.counter * (1.0 + base + heavy * _heavy(g) + narrow * _narrow(g)))
        STOCK[name].fn(g)
        g.p = p                             # the sidebearings come from the real counter
    return recipe


# The ampersand is wider than the stock one, so its upper loop stays open in a narrow face. In the heavy
# weights and the narrow widths the s gets wider too: its two openings had closed to slits there.
FAMILY.recipes.add("ampersand", "&", case="upper")(_wider("ampersand", 0.12, 0.12, 0.12))
FAMILY.recipes.add("s", "s")(_wider("s", 0.0, 0.10, 0.10))
