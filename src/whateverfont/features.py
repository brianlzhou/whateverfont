"""OpenType features for figures and case: frac, numr, dnom, sups, subs, sinf, ordn, zero, case, pnum, tnum.

Each feature is written only for the glyphs the font has, so a small set (``latin().only()``) gets
the features its glyphs allow, or none. The lookups come after ``ccmp`` and ``locl`` and before
the kerning, in this order: the fractions and the small figures first, then the ordinals, the
slashed zero, the case forms, and last the figure widths. So ``frac`` turns a plain figure into a
numerator before ``pnum`` could turn it into another glyph.

- ``frac``: a slash between two figures becomes the fraction slash, the figures before it become
  numerators (the superscripts) and the figures after it denominators (``zero.dnom``). So 1/2 looks
  like ½, and 2 3/4 like 2 ¾. The fraction slash moves closer to both, as in ½.
- ``numr`` and ``dnom``: every figure becomes a numerator, or a denominator.
- ``sups``: superscript figures. ``subs`` and ``sinf``: subscript figures.
- ``ordn``: an a or an o after a figure becomes ª or º, and No. becomes №.
- ``zero``: the zero with a slash.
- ``case``: dashes, brackets, guillemets and the middle dot move up to the middle of the capitals,
  and ¡ ¿ stand on the baseline.
- ``pnum`` and ``tnum``: proportional and tabular figures. The default figures are tabular, so
  ``tnum`` is in a font only if a family turned its default to proportional.

In a monospaced font every glyph keeps its cell: the fraction slash does not move, and there is no
``pnum`` or ``tnum``, since every figure is as wide as the cell.
"""

from __future__ import annotations

from .geom import contour_bounds
from .recipes.forms import CASE
from .recipes.signs import FIGURE_NAMES, INFERIORS, SUPERIORS

#: Glyphs that take the case form of another one (the Unicode hyphens are drawn like the hyphen).
CASE_SAME = {"uni2010": "hyphen", "uni2011": "hyphen"}


def _have(glyphs, names) -> bool:
    return all(n in glyphs for n in names)


def _sub(tag: str, a: list, b: list) -> list:
    return [f"feature {tag} {{", f"    sub [{' '.join(a)}] by [{' '.join(b)}];", f"}} {tag};", ""]


def _fraction_spacing(glyphs: dict) -> tuple | None:
    """How far to move the fraction slash in ``frac``: (x placement, x advance), so that a fraction
    set from figures sits like the precomposed ½. None if the glyphs are not there."""
    num, slash, den = glyphs.get("onesuperior"), glyphs.get("fraction"), glyphs.get("one.dnom")
    if num is None or slash is None or den is None:
        return None
    bs = contour_bounds(slash.contours)
    if not bs:
        return None
    w = bs[2] - bs[0]
    # as in ½: the slash starts at 78% of the numerator's advance, the denominator 62% across the slash
    x = -0.22 * num.advance - bs[0]
    adv = 0.62 * w - 0.22 * num.advance - slash.advance
    return int(round(x)), int(round(adv))


def code(glyphs: dict, p) -> str:
    """Feature code for the figure and case features of the glyphs present."""
    figs = [f for f in FIGURE_NAMES if f in glyphs]
    out: list = []
    whole = len(figs) == 10
    sups = whole and _have(glyphs, SUPERIORS)
    infs = whole and _have(glyphs, INFERIORS)
    dnom = whole and _have(glyphs, [f"{f}.dnom" for f in FIGURE_NAMES])
    fig_class = f"[{' '.join(FIGURE_NAMES)}]"
    if sups and dnom and _have(glyphs, ("slash", "fraction")):
        num_class = f"[{' '.join(SUPERIORS)}]"
        den_class = f"[{' '.join(f + '.dnom' for f in FIGURE_NAMES)}]"
        out += ["feature frac {",
                "    lookup frac_slash {",
                f"        sub {fig_class} slash' {fig_class} by fraction;",
                "    } frac_slash;",
                "    lookup frac_numerators {",
                f"        rsub {fig_class}' [fraction {' '.join(SUPERIORS)}] by {num_class};",
                "    } frac_numerators;",
                "    lookup frac_denominators {",
                f"        sub [fraction {' '.join(f + '.dnom' for f in FIGURE_NAMES)}] {fig_class}' by {den_class};",
                "    } frac_denominators;"]
        spacing = _fraction_spacing(glyphs) if not p.mono else None
        if spacing:
            out.append(f"    pos fraction <{spacing[0]} 0 {spacing[1]} 0>;")
        out += ["} frac;", ""]
    if sups:
        out += _sub("numr", FIGURE_NAMES, SUPERIORS)
    if dnom:
        out += _sub("dnom", FIGURE_NAMES, [f"{f}.dnom" for f in FIGURE_NAMES])
    if sups:
        out += _sub("sups", FIGURE_NAMES, SUPERIORS)
    if infs:
        out += _sub("subs", FIGURE_NAMES, INFERIORS)
        out += _sub("sinf", FIGURE_NAMES, INFERIORS)
    if figs:
        ordn = []
        if _have(glyphs, ("ordfeminine", "a", "A")):
            ordn.append(f"    sub [{' '.join(figs)}] [A a]' by ordfeminine;")
        if _have(glyphs, ("ordmasculine", "o", "O")):
            ordn.append(f"    sub [{' '.join(figs)}] [O o]' by ordmasculine;")
        if _have(glyphs, ("numero", "N", "o", "period")):
            ordn.append("    sub N o period by numero;")
        if ordn:
            out += ["feature ordn {"] + ordn + ["} ordn;", ""]
    if _have(glyphs, ("zero", "zero.zero")):
        out += ["feature zero {", "    sub zero by zero.zero;", "} zero;", ""]
    pairs = [(n, f"{n}.case") for n in CASE if n in glyphs and f"{n}.case" in glyphs]
    same = [(n, f"{t}.case") for n, t in CASE_SAME.items() if n in glyphs and f"{t}.case" in glyphs]
    if pairs or same:
        out += ["feature case {"]
        out += [f"    sub {a} by {b};" for a, b in pairs + same]
        out += ["} case;", ""]
    for tag, suffix in (("pnum", ".pnum"), ("tnum", ".tnum")):
        if whole and not p.mono and _have(glyphs, [f + suffix for f in FIGURE_NAMES]):
            out += _sub(tag, FIGURE_NAMES, [f + suffix for f in FIGURE_NAMES])
    return "\n".join(out) + ("\n" if out else "")


#: Every feature tag this module may write.
TAGS = ("frac", "numr", "dnom", "sups", "subs", "sinf", "ordn", "zero", "case", "pnum", "tnum")
