"""Cyrillic: the letters of Russian, Ukrainian, Belarusian, Bulgarian, Serbian, Macedonian and Kazakh.

The basic block U+0400 to U+045F, Ґ ґ, and the letters that Kazakh, Uzbek, Tatar, Tajik and
Kyrgyz add (Ә Ғ Қ Ң Ө Ұ Ү Һ Җ Ҳ Ҷ Ӣ Ӯ and their lowercase).

A letter that has the shape of a Latin one draws that letter: А is A, р is p, Ѕ is S, ё is ë. So
a project that redraws A gets its own А too, and the two can never drift apart. И and Я are N and R
turned over, Э is C turned over with a bar, and Є is C with a bar.

Most lowercase letters are small capitals in upright Cyrillic: в г д ж з и л м н п т ц ч ш щ ъ ы ь
я. :func:`small` draws the capital recipe at the x-height with the strokes and counters of the
lowercase, so н is the H of the lowercase, and its weight and width match n. The letters with
their own lowercase shape (б ф ђ є э ю ү) have recipes of their own.

These forms are the Russian ones. The Bulgarian forms (д л with a pointed top, and the others)
and the Serbian and Macedonian cursive forms are not drawn, so there is no ``locl`` for them.
"""

from __future__ import annotations

from ..geom import contour_bounds, translate
from ..glyph import G, H, V, Recipe, Recipes
from .accents import ACCENTS, _center, mark
from .extended import EXTENDED, _mark, _width_so_far
from .letters import LETTERS
from .lower import LOWER, arch, diagonal_slab, n_width, o_width, open_angle, vee
from .upper import UPPER, _lobe

CYRILLIC = Recipes()


def cap(name, uni):
    return CYRILLIC.add(name, uni, case="upper")


def low(name, uni):
    return CYRILLIC.add(name, uni, case="lower")


def uni(cp: int) -> str:
    return f"uni{cp:04X}"


# --------------------------------------------------------------------------
# Shared parts
# --------------------------------------------------------------------------

def small(g: G, draw, *args):
    """Draw a capital recipe as a lowercase letter: at the x-height, with lowercase strokes and counters.

    The recipe reads ``g.cap`` for its height. While it runs, the cap height is the x-height; the
    stroke weight and the counter already follow the lowercase case of ``g``.
    """
    p = g.p
    g.p = p.but(cap=g.xh)
    try:
        return draw(g, *args)
    finally:
        g.p = p


def tail_y(g: G) -> float:
    """The bottom of a descender on the baseline (Ц Щ Д Ң): shorter than the descender of p."""
    if g.case == "upper":
        return max(g.desc * 0.72, -g.cap * 0.205)
    return g.desc * 0.74


def tail(g: G, x_right: float, w: float = 0.92) -> float:
    """A short descender that hangs from a bar on the baseline, its right edge at ``x_right``. Its top is
    level with the top of the bar. Returns its centerline, where the bar should end: a bar that ends
    exactly on the edge of another stroke leaves two edges on each other, which an effect cannot merge."""
    t = g.sw * w
    g.stem(x_right - t / 2, tail_y(g), g.hw, b=1, t=0, w=w, serif0=False, serif1=False, tag="tail")
    return x_right - t / 2


def _letter(name: str, source: Recipes):
    """A recipe that draws the Latin letter ``name``: the project's own, if it redrew it."""
    def recipe(g: G):
        g.base(name, source[name].fn)(g)
    return recipe


def _turned(name: str, source: Recipes, left, right):
    """The Latin letter ``name`` turned over left to right (И from N, Я from R)."""
    def recipe(g: G):
        g.base(name, source[name].fn)(g)
        w = _width_so_far(g)
        g.mirror_x(w / 2)
        g.frame(w, left, right)
    return recipe


def _same(name: str, cp: int, base: str, source: Recipes, case: str):
    CYRILLIC[name] = Recipe(name, _letter(base, source), cp, case)


def light(g: G) -> float:
    """The weight of the inner strokes of a crowded letter (Ш Ж Ы Ю Њ): lighter in a monospaced cell,
    so its counters stay open, and full elsewhere."""
    return 0.80 if g.p.mono else 1.0


def _narrow(g: G, k: float, draw):
    """Run ``draw`` with counters ``k`` times as wide (the O of Ю)."""
    p = g.p
    g.p = p.but(width=p.width * k)
    try:
        draw(g)
    finally:
        g.p = p


# --------------------------------------------------------------------------
# Capitals that draw a Latin letter
# --------------------------------------------------------------------------

for _cp, _base in ((0x0410, "A"), (0x0412, "B"), (0x0415, "E"), (0x041A, "K"), (0x041C, "M"), (0x041D, "H"),
                   (0x041E, "O"), (0x0420, "P"), (0x0421, "C"), (0x0422, "T"), (0x0425, "X"), (0x0405, "S"),
                   (0x0406, "I"), (0x0408, "J"), (0x04AE, "Y")):
    _same(uni(_cp), _cp, _base, UPPER, "upper")

for _cp, _base in ((0x0430, "a"), (0x0435, "e"), (0x043E, "o"), (0x0440, "p"), (0x0441, "c"), (0x0443, "y"),
                   (0x0445, "x"), (0x0455, "s"), (0x0456, "i"), (0x0458, "j"), (0x04BB, "h")):
    _same(uni(_cp), _cp, _base, LOWER, "lower")


def _from_set(name: str):
    """A Latin glyph of the full set that is not in UPPER or LOWER (ë, ĸ, ħ, ə)."""
    group = next(grp for grp in (ACCENTS, EXTENDED, LETTERS) if name in grp)
    return _letter(name, group)


for _cp, _base, _case in ((0x0400, "Egrave", "upper"), (0x0401, "Edieresis", "upper"),
                          (0x0407, "Idieresis", "upper"), (0x0450, "egrave", "lower"),
                          (0x0451, "edieresis", "lower"), (0x0457, "idieresis", "lower"),
                          (0x043A, "kgreenlandic", "lower"), (0x045B, "hbar", "lower"),
                          (0x04D8, "Schwa", "upper"), (0x04D9, "schwa", "lower")):
    CYRILLIC[uni(_cp)] = Recipe(uni(_cp), _from_set(_base), _cp, _case)


# --------------------------------------------------------------------------
# Г П Ш Щ Ц Џ: stems and bars
# --------------------------------------------------------------------------

def ge(g: G) -> float:
    """Г: a stem and an arm along the top. Returns the width. Greek Γ is the same letter."""
    w = g.sw + g.capw(0.78, 0.64)
    g.stem(g.L, 0, g.cap, serif1=(1.0, 0))
    g.bar(g.L, w, g.flat_top(g.cap), r=0.7)
    g.beak(w, g.flat_top(g.cap), down=True)
    return w


@cap("uni0413", 0x0413)
def Ge(g):
    g.frame(ge(g), "s", 0.25)


def pe(g: G, w: float):
    """П: two stems under a bar. Greek Π is the same letter."""
    h = g.cap
    g.bar(g.L, w - g.L, g.flat_top(h))             # from stem to stem: the stems make the corners
    g.stem(g.L, 0, h, t=0, serif1=False)
    g.stem(w - g.L, 0, h, t=0, serif1=False)
    g.slab(g.L, h, 1.0, 0, top=True)               # in a serif family the bar reaches past the stems
    g.slab(w - g.L, h, 0, 1.0, top=True)
    g.frame(w)


def pe_width(g: G) -> float:
    return 2 * g.sw + g.capw(0.98, 1.02)


@cap("uni041F", 0x041F)
def Pe(g):
    pe(g, pe_width(g))


def _stems_on_bar(g: G, xs: list, right: float, inner: float = 1.0):
    """Stems that stand on a bar along the baseline, from the first stem to ``right`` (Ш Ц Џ). The
    stems between the first and the last are ``inner`` as heavy."""
    for i, x in enumerate(xs):
        g.stem(x, 0, g.cap, b=0, serif0=False, w=inner if 0 < i < len(xs) - 1 else 1.0)
    g.bar(xs[0], right, g.hw / 2)
    g.slab(g.L, 0, 1.0, 0)                         # in a serif family the bar reaches past the stems


def _sha_width(g: G):
    c = g.capw(0.78, 0.82)
    return c, 3 * g.sw + 2 * c


def sha(g: G, with_tail: bool):
    c, w = _sha_width(g)
    xs = [g.L, w / 2, w - g.L]
    if with_tail:
        right = w + g.sw * 0.42
        _stems_on_bar(g, xs, tail(g, right), light(g))
        g.frame(right, "s", 0.55)
    else:
        _stems_on_bar(g, xs, w - g.L, light(g))
        g.slab(w - g.L, 0, 0, 1.0)
        g.frame(w)


@cap("uni0428", 0x0428)
def Sha(g):
    sha(g, False)


@cap("uni0429", 0x0429)
def Shcha(g):
    sha(g, True)


def tse(g: G):
    w = 2 * g.sw + g.capw(0.98, 1.02)
    right = w + g.sw * 0.42
    _stems_on_bar(g, [g.L, w - g.L], tail(g, right))
    g.frame(right, "s", 0.55)


@cap("uni0426", 0x0426)
def Tse(g):
    tse(g)


def dzhe(g: G):
    """Џ: a U with a flat bottom and a descender in the middle."""
    w = 2 * g.sw + g.capw(0.98, 1.02)
    _stems_on_bar(g, [g.L, w - g.L], w - g.L)
    g.slab(w - g.L, 0, 0, 1.0)
    tail(g, w / 2 + g.sw * 0.46)
    g.frame(w)


@cap("uni040F", 0x040F)
def Dzhe(g):
    dzhe(g)


# --------------------------------------------------------------------------
# Л Д Љ: the left leg
# --------------------------------------------------------------------------

#: The direction in which the leg of Л leaves the letter at its foot: down and out to the left.
LEG = complex(-0.40, -1.0)


def _leg(g: G, R: float, xl: float, xf: float, yf: float, h: float, end_cut=H, fl: float = 1.0):
    """The bar along the top, from the right stem at ``R`` to the leg at ``xl``, and the leg, which
    comes straight down and turns out to the left to its foot at (``xf``, ``yf``)."""
    ft = g.flat_top(h)
    ym = yf + (h - yf) * 0.52
    d = LEG / abs(LEG)
    span = ym - yf
    return (g.path(R, ft)
            .to(xl, ft, corner=True)
            .to(xl, ym)
            .curve((xl, ym - span * 0.42), (xf - d.real * span * 0.48, yf - d.imag * span * 0.48), xf, yf,
                   fl=fl)
            .done(start=V, end=end_cut, round_end=0.0 if g.serifed else None, miter=4, tag="leg"))


def el(g: G, w: float) -> float:
    """Л: a right stem, a bar along the top and a left leg whose foot turns out. Returns the right stem."""
    h = g.cap
    R = w - g.L
    xf = g.dx(LEG)                                # the outer corner of the foot sits at x = 0
    xl = xf + g.sw * 0.18 + w * 0.11
    g.stem(R, 0, h, t=0, serif1=False)
    _leg(g, R, xl, xf, 0.0, h)
    diagonal_slab(g, xf, 0, LEG, top=False, left=1.0, right=0.5)
    g.slab(xl, h, 1.0, 0, top=True)
    g.slab(R, h, 0, 1.0, top=True)
    return R


def el_width(g: G) -> float:
    return 2 * g.sw + g.capw(0.96, 1.0)


@cap("uni041B", 0x041B)
def El(g):
    el(g, el_width(g))
    g.frame(el_width(g), 0.35, "s")


def de(g: G):
    """Д: the top of a Л standing on a wide bar, with a descender at each end of the bar."""
    h = g.cap
    w = 2 * g.sw + g.capw(1.06, 1.10)
    t = 0.92                                       # the weight of the descenders
    R = w - g.L
    x_left = g.sw * t / 2                          # the left descender
    xf = x_left + g.sw * 1.05                      # where the leg stands on the bar
    xl = xf + w * 0.09
    g.stem(R, tail_y(g), h, t=0, serif1=False)     # the right stem runs on down as the right descender
    g.stem(x_left, tail_y(g), g.hw, b=1, t=0, w=t, serif0=False, serif1=False, tag="tail")
    g.bar(x_left, R, g.hw / 2)
    _leg(g, R, xl, xf, g.hw / 2, h, end_cut=H, fl=0.0)
    g.slab(xl, h, 1.0, 0, top=True)
    g.slab(R, h, 0, 1.0, top=True)
    g.frame(w, 0.45, 0.6)


@cap("uni0414", 0x0414)
def De(g):
    de(g)


# --------------------------------------------------------------------------
# Б Ь Ъ Ы Љ Њ: a stem with a bowl at the foot
# --------------------------------------------------------------------------

def bowl_top(g: G) -> float:
    """The centerline of the top of the bowl of Ь Ъ Ы Б Љ Њ."""
    return g.cap * 0.555


def _soft_bowl(g: G, x_stem: float, w: float):
    _lobe(g, x_stem, w - g.rw / 2, bowl_top(g), g.hw / 2, straight=0.40)


def soft_width(g: G) -> float:
    return g.sw + g.rw + g.capw(0.84, 0.72)


@cap("uni042C", 0x042C)
def Soft(g):
    w = soft_width(g)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0))
    _soft_bowl(g, g.L, w)
    g.frame(w, "s", 0.55)


@cap("uni042A", 0x042A)
def Hard(g):
    arm = g.capw(0.40, 0.40)
    x = arm + g.L
    w = arm + soft_width(g)
    g.bar(0, x, g.flat_top(g.cap), l=0.7)
    g.beak(0, g.flat_top(g.cap), side=-1, down=True)
    g.stem(x, 0, g.cap, t=0, serif0=(1.0, 0), serif1=False)
    _soft_bowl(g, x, w)
    g.frame(w, 0.25, 0.55)


@cap("uni042B", 0x042B)
def Yeru(g):
    w1 = g.sw + g.rw + g.capw(0.74, 0.64)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0))
    _soft_bowl(g, g.L, w1)
    k = light(g)
    x = w1 + g.capw(0.30, 0.30) + g.sw * k / 2
    g.stem(x, 0, g.cap, w=k)
    g.frame(x + g.sw * k / 2, "s", "s")


@cap("uni0411", 0x0411)
def Be(g):
    w = soft_width(g) + g.capw(0.02, 0.0)
    g.stem(g.L, 0, g.cap, serif0=(1.0, 0), serif1=(1.0, 0))
    g.bar(g.L, w * 0.93, g.flat_top(g.cap), r=0.7)
    g.beak(w * 0.93, g.flat_top(g.cap), down=True)
    _soft_bowl(g, g.L, w)
    g.frame(w, "s", 0.55)


def lje(g: G):
    """Љ: a Л whose right stem carries the bowl of Ь."""
    wl = 2 * g.sw + g.capw(0.86, 0.90)
    R = el(g, wl)
    w = R + g.rw / 2 + g.capw(0.62, 0.56) + g.rw / 2
    _soft_bowl(g, R, w)
    g.frame(w, 0.35, 0.55)


@cap("uni0409", 0x0409)
def Lje(g):
    lje(g)


def nje(g: G):
    """Њ: an H whose right stem carries the bowl of Ь, at the height of the bar."""
    wh = 2 * g.sw + g.capw(0.86, 0.90)
    R = wh - g.L
    g.stem(g.L, 0, g.cap)
    g.stem(R, 0, g.cap, serif0=(1.0, 0), w=light(g))
    g.bar(g.L, R, bowl_top(g))
    w = R + g.rw / 2 + g.capw(0.62, 0.56) + g.rw / 2
    _soft_bowl(g, R, w)
    g.frame(w, "s", 0.55)


@cap("uni040A", 0x040A)
def Nje(g):
    nje(g)


# --------------------------------------------------------------------------
# И Й Я Э Є Ю Ө: turned and barred Latin letters
# --------------------------------------------------------------------------

CYRILLIC["uni0418"] = Recipe("uni0418", _turned("N", UPPER, "s", "s"), 0x0418, "upper")
CYRILLIC["uni042F"] = Recipe("uni042F", _turned("R", UPPER, "d", "s"), 0x042F, "upper")


def _ii(g: G):
    g.base("uni0418", CYRILLIC["uni0418"].fn)(g)


@cap("uni0419", 0x0419)
def Iishort(g):
    _ii(g)
    mark(g, "breve", _center(g), True)


@cap("uni040D", 0x040D)
def Igrave(g):
    _ii(g)
    mark(g, "grave", _center(g), True)


def ereversed(g: G, letter: str, source: Recipes, h: float):
    """Э and э: C or c turned over, with a bar from its right side to the middle."""
    g.base(letter, source[letter].fn)(g)
    b = contour_bounds(g.outlines())
    g.mirror_x((b[0] + b[2]) / 2)
    xr = b[2] - g.rw / 2
    g.bar(b[0] + (b[2] - b[0]) * 0.30, xr, h * 0.50, w=0.94)
    g.frame(None, 0.36 if letter == "C" else 0.3, "r")


@cap("uni042D", 0x042D)
def Ereversed(g):
    ereversed(g, "C", UPPER, g.cap)


def ie_ukrainian(g: G, letter: str, source: Recipes, h: float):
    """Є and є: C or c with a bar from its left side to the middle."""
    g.base(letter, source[letter].fn)(g)
    b = contour_bounds(g.outlines())
    g.bar(b[0] + g.rw / 2, b[0] + (b[2] - b[0]) * 0.66, h * 0.50, w=0.94)
    g.frame(None, "r", 0.36 if letter == "C" else 0.3)


@cap("uni0404", 0x0404)
def Ieukrainian(g):
    ie_ukrainian(g, "C", UPPER, g.cap)


def yu(g: G, letter: str, source: Recipes, h: float, k: float = 0.84):
    """Ю and ю: a stem, a short bar, and a narrower O."""
    gap = g.cw * 0.30
    g.stem(g.L, 0, h)
    s0, h0 = _mark(g)
    _narrow(g, k, lambda q: g.base(letter, source[letter].fn)(q))
    wo = _width_so_far(g)
    dx = g.sw + gap
    g.transform(translate(dx, 0.0), s0, h0)
    g.bar(g.L, dx + g.rw * 0.5, h * 0.50, w=0.94 * light(g))
    g.frame(dx + wo, "s", "r")


@cap("uni042E", 0x042E)
def Yu(g):
    yu(g, "O", UPPER, g.cap)


def barred_o(g: G, letter: str, source: Recipes, h: float):
    """Ө and ө: O or o with a bar across the middle."""
    g.base(letter, source[letter].fn)(g)
    w = _width_so_far(g)
    g.bar(g.rw * 0.5, w - g.rw * 0.5, h * 0.50, w=0.94)


@cap("uni04E8", 0x04E8)
def Obarred(g):
    barred_o(g, "O", UPPER, g.cap)


# --------------------------------------------------------------------------
# Ж З Ф Ч У
# --------------------------------------------------------------------------

def zhe(g: G):
    """Ж: a stem with the arm and the leg of K on each side."""
    h = g.cap
    # each half has room for two diagonals as heavy as the stem, so a narrow heavy Ж keeps its white
    half = g.capw(0.80, 0.84) + g.sw * 1.0
    xc = half
    w = 2 * half
    k = light(g)
    g.stem(xc, 0, h, w=k)
    square = 0.0 if g.serifed else None
    for side in (1, -1):
        start = len(g.strokes)
        pa, pb = g.diagonal(xc + g.sw * 0.25, h * 0.44, w * 0.985, h, "c", "r", w=k)
        g.line(pa.real, pa.imag, pb.real, pb.imag, b=0, t=1, cut0=V, cut1=H, tag="arm", round1=square, w=k)
        j = pa + (pb - pa) * 0.30
        qa, qb = g.diagonal(j.real, j.imag, w, 0, "c", "r")
        g.line(qa.real, qa.imag, qb.real, qb.imag, b=0, t=1, cut0=pb - pa, cut1=H, tag="leg", round1=square)
        diagonal_slab(g, pb.real, h, pb - pa, top=True, left=0.8, right=0.8)
        diagonal_slab(g, qb.real, 0, qb - qa, top=False, left=0.8, right=1.0)
        if side < 0:
            g.mirror_x(xc, start)
    g.frame(w, "d", "d")


@cap("uni0416", 0x0416)
def Zhe(g):
    zhe(g)


def ze(g: G):
    """З: two bowls open to the left, the upper one smaller, joined in the middle like a 3."""
    h = g.cap
    x0 = g.rw / 2
    x1 = x0 + g.capw(0.80, 0.74) + g.sw * 0.62      # a heavy З keeps the white of both bowls
    bot, top = g.bot, g.top(h)
    ym = h * 0.545
    urx, ury = (x1 - x0) / 2 * 0.90, (top - ym) / 2
    lrx, lry = (x1 - x0) / 2, (ym - bot) / 2
    ucx = x1 - (x1 - x0) * 0.055 - urx
    lcx = x1 - lrx
    a0 = 180 - open_angle(g, 28, 44)
    a1 = -(180 - open_angle(g, 26, 42))
    ps = g.epoint(ucx, top - ury, urx, ury, -106)
    (g.path(ps.real, ps.imag, 0.85)
     .ellipse(ucx, top - ury, urx, ury, -106, a0, fl=1.0)
     .done(end=g.curved_cut(), tag="upper"))
    qs = g.epoint(lcx, bot + lry, lrx, lry, 106)
    (g.path(qs.real, qs.imag, 0.85)
     .ellipse(lcx, bot + lry, lrx, lry, 106, a1, fl=1.0)
     .done(end=g.curved_cut(), tag="lower"))
    g.frame(None, 0.45, "r")


@cap("uni0417", 0x0417)
def Ze(g):
    ze(g)


def ef(g: G, y0: float, y1: float, ring_bot: float, ring_top: float, c: float):
    """Ф and ф: a stem from ``y0`` to ``y1`` through a wide oval. ``c`` is the white on each side."""
    w = 2 * c + g.sw + 2 * g.rw
    g.stem(w / 2, y0, y1)
    g.ring(g.rw / 2, ring_bot, w - g.rw / 2, ring_top)
    g.frame(w, "r", "r")


@cap("uni0424", 0x0424)
def Ef(g):
    h = g.cap
    ef(g, 0, h, h * 0.125 + g.hw / 2, h * 0.875 - g.hw / 2, g.capw(0.50, 0.56))


def che(g: G):
    """Ч: a full stem on the right, and a short one on the left that turns down and joins it."""
    h = g.cap
    w = 2 * g.sw + g.capw(0.90, 0.94)
    start = len(g.strokes)
    # an arch like the one of n, turned over: it leaves the right stem, rounds at the bottom of the
    # bowl, and rises as the short left stem to a free end at the top
    arch(g, g.L, w - g.L, foot=0.0, branch=0.70, height=h * 0.62 - g.o)
    g.rotate(180, w / 2, h / 2, start)
    g.stem(w - g.L, 0, h)
    g.frame(w, "s", "s")


@cap("uni0427", 0x0427)
def Che(g):
    che(g)


def u_cyr(g: G):
    """У: a short arm from the top left meets a long stroke from the top right, which runs down to the
    baseline and turns out to the left in a short tail."""
    h = g.cap
    w = g.capw(1.10, 1.16) + g.sw * 1.5
    xm = w * 0.5
    pa, _ = g.diagonal(0, h, xm, h * 0.36, "l", "c")
    pc, _ = g.diagonal(w, h, xm, h * 0.36, "r", "c")
    xj, yj = xm + g.sw * 0.10, h * 0.34
    slope = (pc.real - xj) / (h - yj)
    y_turn = h * 0.15
    x_turn = xj - slope * (yj - y_turn)
    x_end = max(g.sw * 0.5, x_turn - w * 0.30)
    square = 0.0 if g.serifed else None
    d = complex(-slope, -1)
    (g.path(pc.real, h, fl=1.0)
     .flared_from(x_turn, y_turn)
     .curve((x_turn + d.real * y_turn * 0.45, y_turn + d.imag * y_turn * 0.45),
            (x_end + (x_turn - x_end) * 0.45, g.hw / 2), x_end, g.hw / 2, fl=1.0)
     .done(start=H, end=V, round_start=square, tag="tail"))
    g.line(pa.real, h, xj, yj, b=1, t=0, cut0=H, cut1=complex(slope, 1), tag="arm", round0=square)
    diagonal_slab(g, pa.real, h, complex(xj, yj) - pa, top=True)
    diagonal_slab(g, pc.real, h, complex(x_turn, y_turn) - pc, top=True)
    g.frame(w, "d", "d")


@cap("uni0423", 0x0423)
def U(g):
    u_cyr(g)


@cap("uni040E", 0x040E)
def Ushort(g):
    u_cyr(g)
    mark(g, "breve", _center(g), True)


# --------------------------------------------------------------------------
# Ђ Ћ Һ: an arch from the stem, under a bar or not
# --------------------------------------------------------------------------

def _tshe_top(g: G):
    """The bar of Ћ and Ђ, and the stem under it. Returns the stem's x and the bar's width."""
    wb = g.capw(0.98, 1.04) + g.sw
    xs = wb * 0.34
    ft = g.flat_top(g.cap)
    g.bar(0, wb, ft, l=0.7, r=0.7)
    g.beak(0, ft, side=-1, down=True)
    g.beak(wb, ft, side=1, down=True)
    g.stem(xs, 0, g.cap, t=0, serif1=False)
    return xs, wb


def _arch_height(g: G) -> float:
    return g.cap * 0.60


@cap("uni040B", 0x040B)
def Tshe(g):
    xs, wb = _tshe_top(g)
    x1 = xs + g.sw + g.capw(0.78, 0.80)
    arch(g, xs, x1, height=_arch_height(g))
    g.frame(max(wb, x1 + g.L), 0.25, "s")


def _hooked_arch(g: G, x0: float, x1: float, h: float, y_hook: float, y_bottom: float, rx: float):
    """An arch from the stem at ``x0`` whose right leg runs down below the baseline and hooks left (Ђ ђ)."""
    top = g.top(h)
    xm = x0 + (x1 - x0) * 0.5
    ysh = max(top - (x1 - xm) * 1.02, h * 0.3)
    ry = y_hook - y_bottom
    end = -(90 + open_angle(g, 46, 60))
    (g.path(x0, h * 0.60, g.p.join)
     .arc(xm, top, "v", k0=0.42, k1=0.62)
     .arc(x1, ysh, "h")
     .to(x1, y_hook)
     .ellipse(x1 - rx, y_hook, rx, ry, 0, end, fl=1.0)
     .done(end=g.curved_cut(), tag="arch"))


@cap("uni0402", 0x0402)
def Dje(g):
    xs, wb = _tshe_top(g)
    x1 = xs + g.sw + g.capw(0.74, 0.76)
    rx = g.capw(0.24, 0.24)
    # the leg turns under the baseline in a short hook, not a descender
    _hooked_arch(g, xs, x1, _arch_height(g), g.cap * 0.12, -g.cap * 0.10 + g.hw / 2, rx)
    g.frame(max(wb, x1 + g.L), 0.25, "s")


@cap("uni04BA", 0x04BA)
def Shha(g):
    w = 2 * g.sw + g.capw(0.92, 0.96)
    g.stem(g.L, 0, g.cap)
    arch(g, g.L, w - g.L, height=_arch_height(g))
    g.frame(w, "s", "s")


# --------------------------------------------------------------------------
# Ѓ Ќ Ґ Ғ Қ Ң Ұ Җ Ҳ Ҷ Ӣ Ӯ
# --------------------------------------------------------------------------

@cap("uni0403", 0x0403)
def Gje(g):
    w = ge(g)
    g.frame(w, "s", 0.25)
    mark(g, "acute", _center(g), True)


@cap("uni040C", 0x040C)
def Kje(g):
    g.base("K", UPPER["K"].fn)(g)
    mark(g, "acute", _center(g), True)


def ge_upturn(g: G):
    """Ґ: the arm of Г turns up at its end."""
    w = g.sw + g.capw(0.78, 0.64)
    ft = g.flat_top(g.cap)
    top = g.cap * 1.17 if g.case == "upper" else g.xh + (g.asc - g.xh) * 0.62
    g.stem(g.L, 0, g.cap, serif1=(1.0, 0))
    g.bar(g.L, w - g.L, ft)
    g.stem(w - g.L, ft, top, b=0, serif0=False, serif1=False, tag="upturn")
    g.frame(w, "s", 0.4)


@cap("uni0490", 0x0490)
def Geupturn(g):
    ge_upturn(g)


def ge_stroke(g: G):
    """Ғ: Г with a bar across the stem."""
    over = g.sw * 0.62
    w = ge(g)
    g.shift(over)
    g.bar(0, g.L + over + g.sw * 1.25, g.cap * 0.47, w=0.9)
    g.frame(w + over, 0.4, 0.25)


@cap("uni0492", 0x0492)
def Gestroke(g):
    ge_stroke(g)


def with_tail(letter: str, source: Recipes):
    """A letter whose right stem stands on a short bar with a descender at its end: Ң Ҷ."""
    def recipe(g: G):
        g.base(letter, source[letter].fn)(g)
        width, left, _ = g._frame if g._frame is not None else (None, "s", "s")
        b = contour_bounds(g.outlines())
        w = width if width is not None else b[2]
        right = w + g.sw * 0.42
        g.bar(w - g.sw * 0.5, tail(g, right), g.hw / 2)
        g.frame(right if width is not None else None, left, 0.55)
    return recipe


@cap("uni04A2", 0x04A2)
def Endescender(g):
    with_tail("H", UPPER)(g)


@cap("uni049A", 0x049A)
def Kadescender(g):
    g.base("K", UPPER["K"].fn)(g)
    w = _width_so_far(g)
    tail(g, w + g.sw * 0.20)
    g.frame(w + g.sw * 0.20, "s", 0.55)


@cap("uni0496", 0x0496)
def Zhedescender(g):
    g.base("uni0416", CYRILLIC["uni0416"].fn)(g)
    w = _width_so_far(g)
    tail(g, w + g.sw * 0.20)
    g.frame(w + g.sw * 0.20, "d", 0.55)


@cap("uni04B2", 0x04B2)
def Hadescender(g):
    g.base("X", UPPER["X"].fn)(g)
    w = _width_so_far(g)
    tail(g, w + g.sw * 0.20)
    g.frame(w + g.sw * 0.20, "d", 0.55)


@cap("uni04B6", 0x04B6)
def Chedescender(g):
    with_tail("uni0427", CYRILLIC)(g)


@cap("uni04B0", 0x04B0)
def Ustraightstroke(g):
    g.base("Y", UPPER["Y"].fn)(g)
    w = _width_so_far(g)
    g.bar(w * 0.24, w * 0.76, g.cap * 0.27, w=0.9)


@cap("uni04E2", 0x04E2)
def Imacron(g):
    _ii(g)
    mark(g, "macron", _center(g), True)


@cap("uni04EE", 0x04EE)
def Umacron(g):
    u_cyr(g)
    mark(g, "macron", _center(g), True)


# --------------------------------------------------------------------------
# Lowercase: small capitals
# --------------------------------------------------------------------------

def _small_of(name: str, source: Recipes):
    """The capital ``name`` of ``source`` (the project's own, if it redrew it) as a small capital."""
    def recipe(g: G):
        small(g, lambda q: q.base(name, source[name].fn)(q))
    return recipe


for _cp, _cap_name, _src in ((0x0432, "B", UPPER), (0x043C, "M", UPPER), (0x043D, "H", UPPER),
                             (0x0442, "T", UPPER)):
    CYRILLIC[uni(_cp)] = Recipe(uni(_cp), _small_of(_cap_name, _src), _cp, "lower")

for _cp, _cap_cp in ((0x0433, 0x0413), (0x0434, 0x0414), (0x0436, 0x0416), (0x0437, 0x0417), (0x0438, 0x0418),
                     (0x043B, 0x041B), (0x043F, 0x041F), (0x0446, 0x0426), (0x0447, 0x0427), (0x0448, 0x0428),
                     (0x0449, 0x0429), (0x044A, 0x042A), (0x044B, 0x042B), (0x044C, 0x042C), (0x044F, 0x042F),
                     (0x0459, 0x0409), (0x045A, 0x040A), (0x045F, 0x040F), (0x0491, 0x0490), (0x0493, 0x0492),
                     (0x04A3, 0x04A2), (0x0497, 0x0496), (0x04B7, 0x04B6)):
    CYRILLIC[uni(_cp)] = Recipe(uni(_cp), _small_of(uni(_cap_cp), CYRILLIC), _cp, "lower")


def _ii_small(g: G):
    g.base("uni0438", CYRILLIC["uni0438"].fn)(g)


@low("uni0439", 0x0439)
def iishort(g):
    _ii_small(g)
    mark(g, "breve", _center(g), False)


@low("uni045D", 0x045D)
def igrave(g):
    _ii_small(g)
    mark(g, "grave", _center(g), False)


@low("uni04E3", 0x04E3)
def imacron(g):
    _ii_small(g)
    mark(g, "macron", _center(g), False)


@low("uni0453", 0x0453)
def gje(g):
    g.base("uni0433", CYRILLIC["uni0433"].fn)(g)
    mark(g, "acute", _center(g), False)


def _ka(g: G):
    g.base("uni043A", CYRILLIC["uni043A"].fn)(g)


@low("uni045C", 0x045C)
def kje(g):
    _ka(g)
    mark(g, "acute", _center(g), False)


@low("uni049B", 0x049B)
def kadescender(g):
    _ka(g)
    w = _width_so_far(g)
    tail(g, w + g.sw * 0.20)
    g.frame(w + g.sw * 0.20, "s", 0.55)


@low("uni04B3", 0x04B3)
def hadescender(g):
    g.base("x", LOWER["x"].fn)(g)
    w = _width_so_far(g)
    tail(g, w + g.sw * 0.20)
    g.frame(w + g.sw * 0.20, "d", 0.55)


def _u_lower(g: G):
    g.base("y", LOWER["y"].fn)(g)


@low("uni045E", 0x045E)
def ushort(g):
    _u_lower(g)
    mark(g, "breve", _center(g), False)


@low("uni04EF", 0x04EF)
def umacron(g):
    _u_lower(g)
    mark(g, "macron", _center(g), False)


# --------------------------------------------------------------------------
# Lowercase with shapes of their own: б ф ђ э є ю ө ү ұ
# --------------------------------------------------------------------------

@low("uni0431", 0x0431)
def be(g):
    """б: a round bowl, and a stroke that rises from its left side and turns right under the ascender."""
    w = o_width(g)
    g.ring(g.rw / 2, g.bot, w - g.rw / 2, g.top(g.xh))
    top = g.flat_top(g.asc)
    x0 = g.rw / 2
    y0 = g.xh * 0.52
    x_end = w * 0.92
    (g.path(x0, y0, w=g.p.round_weight)
     .to(x0, g.xh * 0.80)
     .curve((x0, g.xh + (top - g.xh) * 0.62), (x0 + (x_end - x0) * 0.30, top), x0 + (x_end - x0) * 0.62, top)
     .to(x_end, top, fl=1.0)
     .done(end=V, tag="neck"))
    g.frame(w, "r", "r")


@low("uni0444", 0x0444)
def ef_lower(g):
    ef(g, g.desc, g.asc, g.bot, g.top(g.xh), g.cw * 0.50)


@low("uni0452", 0x0452)
def dje(g):
    """ђ: an h with a bar across the ascender, whose right leg hooks under the baseline like j."""
    over = g.sw * 0.7
    x0 = g.L + over
    x1 = x0 + g.sw + g.cw
    g.stem(x0, 0, g.asc)
    _hooked_arch(g, x0, x1, g.xh, g.desc * 0.40, g.dbot, min(g.cw * 0.40, (x1 - x0) * 0.62))
    g.bar(0, x0 + g.sw * 1.5, g.asc * 0.80, w=0.85)
    g.frame(x1 + g.L, 0.4, "s")


@low("uni044D", 0x044D)
def ereversed_lower(g):
    ereversed(g, "c", LOWER, g.xh)


@low("uni0454", 0x0454)
def ie_ukrainian_lower(g):
    ie_ukrainian(g, "c", LOWER, g.xh)


@low("uni044E", 0x044E)
def yu_lower(g):
    yu(g, "o", LOWER, g.xh, 0.86)


@low("uni04E9", 0x04E9)
def obarred(g):
    barred_o(g, "o", LOWER, g.xh)


def ue_straight(g: G):
    """ү: a v on the baseline over a stem down to the descender."""
    w = n_width(g) * 1.0
    pa, pc, ya = vee(g, 0, w, g.xh, 0)
    g.stem(w / 2, g.desc, max(ya, 0.0) + g.sw * 0.4, t=0)
    g.frame(w, "d", "d")


@low("uni04AF", 0x04AF)
def ustraight(g):
    ue_straight(g)


@low("uni04B1", 0x04B1)
def ustraightstroke(g):
    ue_straight(g)
    w = _width_so_far(g)
    g.bar(w * 0.24, w * 0.76, g.desc * 0.30, w=0.9)


# in the order of the code points, so the font lists them as Unicode does
_by_code = sorted(CYRILLIC.values(), key=lambda rec: rec.unicode)
CYRILLIC.clear()
CYRILLIC.update((rec.name, rec) for rec in _by_code)

#: Every letter, for ``Recipes.only(cyrillic=True)``.
ALPHABET = "".join(chr(rec.unicode) for rec in CYRILLIC.values())
