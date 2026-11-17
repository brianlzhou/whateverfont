"""Accented letters and a few more symbols, composed from the basic recipes."""

from __future__ import annotations

import unicodedata

from ..geom import contour_bounds
from ..glyph import G, H, V, Recipes
from .lower import LOWER
from .punct import PUNCT, dot_d, tail
from .upper import UPPER

ACCENTS = Recipes()


def _center(g: G) -> float:
    """Horizontal center of what has been drawn so far."""
    if g._frame is not None and g._frame[0] is not None:
        return g._frame[0] / 2
    b = contour_bounds(g.outlines())
    return (b[0] + b[2]) / 2 if b else 0.0


def _drawn_width(g: G) -> float:
    """The width the base letter declared, or the width of its drawing."""
    if g._frame is not None and g._frame[0] is not None:
        return g._frame[0]
    b = contour_bounds(g.outlines())
    return b[2] if b else 0.0


def _box(g: G, upper):
    """(y0, height, half width, stroke scale) for a mark above the letter.

    ``upper`` is True for a capital, False for a lowercase letter, or "tall"
    for a lowercase letter with an ascender (ĥ, ĺ).
    """
    if upper == "tall":
        return g.asc + g.cap * 0.07, g.cap * 0.14, g.p.n_counter * 0.27 + g.sw * 0.25, 0.80
    if upper:
        return g.cap + g.cap * 0.075, g.cap * 0.15, g.p.n_counter * 0.30 + g.sw * 0.25, 0.80
    return g.xh + g.xh * 0.16, g.xh * 0.25, g.p.n_counter * 0.27 + g.sw * 0.25, 0.80


def mark(g: G, kind: str, cx: float, upper: bool, box=None):
    """Draw one mark centered on ``cx``. ``box`` is (y0, height, half width, stroke scale) to draw it
    somewhere else than the usual place above the letter, as the second mark of a stack does."""
    y0, h, half, sc = _box(g, upper) if box is None else box
    t = sc * g.hw / g.sw
    lean = half * 0.62
    if kind == "acute":
        g.line(cx - lean * 0.45, y0, cx + lean * 0.75, y0 + h, w=1.0, scale=sc, tag="mark")
    elif kind == "grave":
        g.line(cx + lean * 0.45, y0, cx - lean * 0.75, y0 + h, w=1.0, scale=sc, tag="mark")
    elif kind in ("circumflex", "caron"):
        ya, yb = (y0, y0 + h * 0.92) if kind == "circumflex" else (y0 + h * 0.92, y0)
        (g.path(cx - half, ya, w=t).to(cx, yb, corner=True, w=t).to(cx + half, ya, w=t)
         .done(scale=1.0, miter=3, tag="mark"))
    elif kind == "dieresis":
        # In a stack (Pinyin ǘ) the dots get smaller with the stroke scale of the box, so the stack fits
        d = g.sw * 0.98 * (1.0 if box is None else sc / 0.80)
        gap = max(half * 0.70, d * 0.95)
        for sx in (-1, 1):
            g.dot(cx + sx * gap, y0 + d * 0.62, d)
    elif kind == "tilde":
        # a long, low wave: a tall one turns into a knot in a heavy weight
        a = h * 0.23
        ym = y0 + h * 0.5
        w = half * 1.3
        (g.path(cx - w, ym - a * 0.7, w=t * 0.92)
         .curve((cx - w * 0.74, ym + a * 1.8), (cx - w * 0.3, ym + a * 1.5), cx, ym, w=t * 1.08)
         .curve((cx + w * 0.3, ym - a * 1.5), (cx + w * 0.74, ym - a * 1.8), cx + w, ym + a * 0.7, w=t * 0.92)
         .done(tag="mark"))
    elif kind == "ring":
        r = h * 0.52
        g.ring(cx - r, y0, cx + r, y0 + 2 * r, w_side=1.0, scale=sc * g.hw / g.sw, tag="mark")
    elif kind == "cedilla":
        d = g.xh * 0.21
        (g.path(cx, g.hw * 0.4, w=t)
         .to(cx - d * 0.12, -d * 0.42, w=t)
         .curve((cx + d * 0.75, -d * 0.42), (cx + d * 0.75, -d * 1.15), cx - d * 0.05, -d * 1.15, w=t)
         .curve((cx - d * 0.3, -d * 1.15), (cx - d * 0.5, -d * 1.05), cx - d * 0.62, -d * 0.95, w=t * 0.9)
         .done(tag="mark"))
    elif kind == "macron":
        g.bar(cx - half * 0.92, cx + half * 0.92, y0 + h * 0.42, w=sc)
    elif kind == "breve":
        bw = half * 0.82
        (g.path(cx - bw, y0 + h, w=t)
         .arc(cx, y0 + g.hw * sc * 0.5, "v", w=t)
         .arc(cx + bw, y0 + h, "h", w=t)
         .done(start=H, end=H, tag="mark"))
    elif kind == "dotaccent":
        d = g.sw * 0.98
        g.dot(cx, y0 + d * 0.62, d)
    elif kind == "doubleacute":
        gap = half * 0.42
        for sx in (-1, 1):
            x = cx + sx * gap
            g.line(x - lean * 0.40, y0, x + lean * 0.55, y0 + h, w=1.0, scale=sc * 0.9, tag="mark")
    elif kind == "ogonek":
        d = (g.cap if upper else g.xh) * 0.22
        (g.path(cx, g.hw * 0.6, w=t * 1.1)
         .curve((cx - d * 0.75, -d * 0.15), (cx - d * 0.85, -d * 1.05), cx - d * 0.05, -d * 1.05, w=t)
         .to(cx + d * 0.30, -d * 0.95, w=t * 0.7)
         .done(tag="mark"))
    elif kind == "commaaccent":
        # sized by the cap height as well as the stem, so a bold comma stays above the descender line
        d = min(dot_d(g) * 0.82, g.cap * 0.135)
        tail(g, cx, -g.hw * 0.3 - d * 0.62, d)
    elif kind == "commaturned":
        from ..geom import rotate_about
        d = min(dot_d(g) * 0.82, g.cap * 0.135)
        s0, h0 = len(g.strokes), len(g.shapes)
        tail(g, cx, y0 + d * 0.9, d)
        g.transform(rotate_about(180, cx, y0 + d * 0.75), s0, h0)
    elif kind == "hookabove":
        # the top of a question mark: a bowl open to the left, then a short stem down to y0. It is
        # lighter than the other marks, and the bowl grows with the stroke, so that it stays open.
        # In a heavy weight the stroke stops growing, so the hook is no taller than an acute.
        w = min(t * 0.80, h * 0.40 / g.thick(1 + 0j))
        rx = max(half * 0.52, g.thick(1j, w) * 1.45)
        ry = max(h * 0.30, g.thick(1 + 0j, w) * 1.30)
        top = max(y0 + h, y0 + ry * 2.15 + h * 0.16)
        my = top - ry
        (g.path(cx - rx, my + ry * 0.05, w=w)
         .arc(cx, top, "v", w=w)
         .arc(cx + rx, my, "h", w=w)
         .curve((cx + rx, my - ry * 0.60), (cx + rx * 0.04, my - ry * 0.72), cx, my - ry * 1.15, w=w)
         .to(cx, y0, w=w)
         .done(end=H, tag="mark"))
    elif kind == "dotbelow":
        # the dot of a dot below: as big as a dot above, and its top as far below the baseline
        # as the overshoot plus a little, so it never touches a round letter. Sized by the x-height
        # as well as the stem, so a heavy dot stays above the bottom of the line.
        d = min(g.sw * 0.98, g.xh * 0.26)
        top = -g.o - (g.cap if upper else g.xh) * 0.075
        g.dot(cx, top - d * 0.5, d)
    else:
        raise KeyError(kind)


MARKS = {"̀": "grave", "́": "acute", "̂": "circumflex", "̃": "tilde", "̈": "dieresis",
         "̊": "ring", "̌": "caron", "̧": "cedilla", "̄": "macron", "̆": "breve", "̇": "dotaccent",
         "̋": "doubleacute", "̨": "ogonek", "̦": "commaaccent",
         "̉": "hookabove", "̣": "dotbelow", "̛": "horn"}            # the last three for Vietnamese
BELOW = ("cedilla", "ogonek", "commaaccent", "dotbelow")
ASCENDERS = "bdfhklt"
COMPOSED = "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüýÿŠšŽžČčĚěŘřŇňŸ"
# Central and Eastern European, Baltic, Turkish, Romanian, Maltese, Esperanto, Welsh
COMPOSED_MORE = ("ĀāĂăĄąĆćĈĉĊċĎďĒēĔĕĖėĘęĜĝĞğĠġĢģĤĥĨĩĪīĬĭĮįİĴĶķĹĺĻļĽľŃńŅņŌōŎŏŐőŔŕŖŗŚśŜŝŞşŢţŤťŨũŪū"
                 "ŬŭŮůŰűŲųŴŵŶŷŹźŻżȘșȚțẀẁẂẃẄẅỲỳĴĵ")


def _compose(char: str, into: Recipes | None = None):
    """Register the letter ``char``, a base letter and one mark, in ``into`` (default: ACCENTS)."""
    into = ACCENTS if into is None else into
    base, combining = unicodedata.normalize("NFD", char)
    kind = MARKS[combining]
    name = f"{base}{kind}"
    # Latvian and Romanian letters take a comma, and d l t take a comma beside the ascender
    if kind == "cedilla" and base in "GKLNRgklnr":
        kind = "commaturned" if base == "g" else "commaaccent"
        name = f"{base}commaaccent"
    if kind == "caron" and base in "dltL":
        kind = "caronvertical"
    upper = base.isupper()
    source = UPPER if upper else LOWER
    above = kind not in BELOW
    dotless = {"i": "dotlessi", "j": "dotlessj"}
    if base in dotless and above:
        from .extended import EXTENDED
        base_name = dotless[base]
        fn = (LOWER if base == "i" else EXTENDED)[base_name].fn
    else:
        base_name = base
        fn = source[base].fn
    level = "tall" if (not upper and base in ASCENDERS and above) else upper

    def recipe(g: G):
        g.base(base_name, fn)(g)          # the project's own letter, if it redrew it
        if kind == "ogonek":
            b = contour_bounds(g.outlines())
            mark(g, kind, b[2] - g.sw * 0.55, upper)
        elif kind == "caronvertical":
            # ď ľ ť Ľ: a comma beside the ascender, since a caron would hit it
            b = contour_bounds(g.outlines())
            d = dot_d(g) * 0.82
            x = (g.sw if base == "L" else b[2]) + d * 0.6
            top = g.cap if base == "L" else b[3]
            tail(g, x, top - d * 0.5, d)
            g._frame = (None, g._frame[1] if g._frame else "s", 0.5)
        else:
            mark(g, kind, _center(g), level)

    into[name] = type(source[base])(name, recipe, ord(char), "upper" if upper else "lower")


for _ch in COMPOSED + COMPOSED_MORE:
    _compose(_ch)


def _add(name, uni, case="lower"):
    return ACCENTS.add(name, uni, case=case)


@_add("oslash", "ø")
def oslash(g):
    g.base("o", LOWER["o"].fn)(g)
    w = _drawn_width(g)
    a, b = g.diagonal(w * 0.14, -g.xh * 0.10, w * 0.86, g.xh * 1.10, "c", "c", w=0.6)
    g.line(a.real, a.imag, b.real, b.imag, w=0.6, cut0=H, cut1=H, tag="slash")


@_add("Oslash", "Ø", "upper")
def Oslash(g):
    g.base("O", UPPER["O"].fn)(g)
    w = _drawn_width(g)
    a, b = g.diagonal(w * 0.14, -g.cap * 0.07, w * 0.86, g.cap * 1.07, "c", "c", w=0.6)
    g.line(a.real, a.imag, b.real, b.imag, w=0.6, cut0=H, cut1=H, tag="slash")


@_add("exclamdown", "¡")
def exclamdown(g):
    g.base("exclam", PUNCT["exclam"].fn)(g)
    g.transform((1, 0, 0, -1, 0, g.xh), 0, 0)


@_add("questiondown", "¿")
def questiondown(g):
    g.base("question", PUNCT["question"].fn)(g)
    b = contour_bounds(g.outlines())
    cx = (b[0] + b[2]) / 2 if b else 0
    g.rotate(180, cx, g.xh / 2)


def _guillemet(g: G, n: int, left: bool):
    h = g.xh * 0.34
    w = g.cw * 0.42
    ym = g.xh * 0.5
    t = g.hw / g.sw
    step = w * 1.15
    for i in range(n):
        x_open, x_tip = (w + i * step, i * step) if left else (i * step, w + i * step)
        (g.path(x_open, ym + h, w=t).to(x_tip, ym, corner=True, w=t).to(x_open, ym - h, w=t)
         .done(miter=4, tag="angle"))
    g.frame(None, 0.6, 0.6)


@_add("guillemotleft", "«")
def guillemotleft(g):
    _guillemet(g, 2, True)


@_add("guillemotright", "»")
def guillemotright(g):
    _guillemet(g, 2, False)


@_add("guilsinglleft", 0x2039)
def guilsinglleft(g):
    _guillemet(g, 1, True)


@_add("guilsinglright", 0x203A)
def guilsinglright(g):
    _guillemet(g, 1, False)


@_add("degree", "°", "figure")
def degree(g):
    r = g.cap * 0.16
    g.ring(g.hw * 0.4, g.cap - 2 * r, g.hw * 0.4 + 2 * r, g.cap + g.o * 0.5, w_side=1.0, scale=0.72 * g.hw / g.sw)
    g.frame(None, 0.5, 0.5)


# --------------------------------------------------------------------------
# Combining marks: zero-width glyphs that the `mark` feature attaches to a letter
# --------------------------------------------------------------------------

COMBINING = {
    0x0300: ("gravecomb", "grave"), 0x0301: ("acutecomb", "acute"), 0x0302: ("circumflexcomb", "circumflex"),
    0x0303: ("tildecomb", "tilde"), 0x0304: ("macroncomb", "macron"), 0x0306: ("brevecomb", "breve"),
    0x0307: ("dotaccentcomb", "dotaccent"), 0x0308: ("dieresiscomb", "dieresis"), 0x030A: ("ringcomb", "ring"),
    0x030B: ("hungarumlautcomb", "doubleacute"), 0x030C: ("caroncomb", "caron"),
    0x0326: ("commaaccentcomb", "commaaccent"), 0x0327: ("cedillacomb", "cedilla"), 0x0328: ("ogonekcomb", "ogonek"),
}


def _combining(kind: str):
    def recipe(g: G):
        mark(g, kind, 0.0, False)
        g.frame(0, 0, 0)          # no advance, and no shift: x = 0 is the attachment point
    return recipe


for _uni, (_name, _kind) in COMBINING.items():
    ACCENTS[_name] = type(LOWER["n"])(_name, _combining(_kind), _uni, "lower")


def _caron_alt(g: G):
    """caroncomb.alt: the comma-shaped caron that ď ľ ť use, as a mark beside an ascender."""
    d = dot_d(g) * 0.82
    tail(g, d * 0.6, g.asc - d * 0.5, d)
    g.frame(0, 0, 0)


ACCENTS["caroncomb.alt"] = type(LOWER["n"])("caroncomb.alt", _caron_alt, None, "lower")
