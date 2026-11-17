"""Glyphs without a code point, which the OpenType features of :mod:`whateverfont.features` choose.

- ``zero.pnum`` to ``nine.pnum``: proportional figures (``pnum``). The default figures are tabular.
- ``zero.dnom`` to ``nine.dnom``: small figures on the baseline, the denominators of ``frac`` and ``dnom``.
  The numerators are the superscripts ``zerosuperior`` to ``ninesuperior``.
- ``zero.zero``: the zero with a slash (``zero``).
- ``hyphen.case`` and the others: dashes, brackets and guillemets moved up to the middle of the
  capitals (``case``).

Each is drawn from the glyph it replaces, so a project that redraws ``2`` or ``(`` gets its own
drawing in every form.
"""

from __future__ import annotations

from ..geom import contour_bounds
from ..glyph import G, H, Recipes
from .accents import ACCENTS
from .figures import FIGURES
from .punct import PUNCT
from .signs import FIGURE_NAMES, SIGNS, inferior, small_advance

FORMS = Recipes()
_Rec = type(FIGURES["zero"])

#: The sides of each proportional figure: (left, right), as in :meth:`G.frame`.
PNUM_SIDES = {"zero": ("r", "r"), "one": (1.0, 1.25), "two": (0.6, 0.6), "three": (0.6, "r"),
              "four": (0.4, 0.55), "five": (0.6, "r"), "six": ("r", 0.6), "seven": (0.5, 0.35),
              "eight": ("r", "r"), "nine": (0.6, "r")}


def tabular(g: G, fig: str):
    """Draw the tabular form of figure ``fig``: the default figure, or ``fig.tnum`` in a family whose
    default figures are proportional (see :func:`proportional_default`)."""
    rs = g.recipes or {}
    name = f"{fig}.tnum" if f"{fig}.tnum" in rs else fig
    g.base(name, FIGURES[fig].fn)(g)


def _pnum(fig: str):
    def recipe(g: G):
        tabular(g, fig)
        if g.p.mono:
            return              # every figure fills the cell: the form is the tabular figure
        g._advance = None
        g.frame(None, *PNUM_SIDES[fig])
    return recipe


for _fig in FIGURE_NAMES:
    FORMS[f"{_fig}.pnum"] = _Rec(f"{_fig}.pnum", _pnum(_fig), None, "figure")


def _dnom(fig: str):
    draw = inferior(fig, 0.0)

    def recipe(g: G):
        draw(g)
    return recipe


for _fig in FIGURE_NAMES:
    FORMS[f"{_fig}.dnom"] = _Rec(f"{_fig}.dnom", _dnom(_fig), None, "figure")


@FORMS.add("zero.zero", None, case="figure")
def zero_slashed(g):
    """The zero with a slash across its counter, for the ``zero`` feature."""
    tabular(g, "zero")
    g.strokes = [s for s in g.strokes if s.tag != "dot"]           # the dotted zero of a monospaced font
    b = contour_bounds(g.outlines())
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    rx, ry = (b[2] - b[0]) / 2 - g.rw / 2, (b[3] - b[1]) / 2 - g.hw / 2
    a = g.epoint(cx, cy, rx, ry, 238)
    c = g.epoint(cx, cy, rx, ry, 58)
    g.line(a.real, a.imag, c.real, c.imag, w=0.66, cut0=H, cut1=H, tag="slash")


# --------------------------------------------------------------------------
# Case forms
# --------------------------------------------------------------------------

#: Glyphs that move up to sit with capitals, and how: "middle" centers the drawing on the middle
#: of the capitals (dashes, guillemets, a dot), "brackets" centers a bracket on it, and "top" lifts
#: ¡ and ¿ so that they stand on the baseline like ! and ?.
CASE = {"hyphen": "middle", "endash": "middle", "emdash": "middle", "figuredash": "middle",
        "horizontalbar": "middle", "periodcentered": "middle", "bullet": "middle",
        "guillemotleft": "middle", "guillemotright": "middle", "guilsinglleft": "middle",
        "guilsinglright": "middle", "parenleft": "brackets", "parenright": "brackets",
        "bracketleft": "brackets", "bracketright": "brackets", "braceleft": "brackets",
        "braceright": "brackets", "slash": "brackets", "backslash": "brackets", "bar": "brackets",
        "at": "brackets", "exclamdown": "top", "questiondown": "top"}


def _source(name: str):
    for group in (PUNCT, ACCENTS, SIGNS):
        if name in group:
            return group[name].fn
    raise KeyError(name)


def _case(name: str, how: str):
    default = _source(name)

    def recipe(g: G):
        g.base(name, default)(g)
        b = contour_bounds(g.outlines())
        if not b:
            return
        if how == "top":
            dy = g.cap - g.xh
        else:
            dy = max(0.0, g.cap / 2 - (b[1] + b[3]) / 2)
        g.shift(0.0, dy)
    return recipe


for _name, _how in CASE.items():
    FORMS[f"{_name}.case"] = _Rec(f"{_name}.case", _case(_name, _how), None, "lower")


def proportional_default(recipes: Recipes) -> Recipes:
    """A copy of ``recipes`` whose default figures are proportional, and whose tabular figures are
    ``zero.tnum`` to ``nine.tnum``, for the ``tnum`` feature. ``Family(figures="proportional")`` uses it.

    A set without ``zero.pnum`` and the others is returned as it is.
    """
    if not all(f"{f}.pnum" in recipes and f in recipes for f in FIGURE_NAMES):
        return recipes
    out = Recipes()
    for name, rec in recipes.items():
        fig = name[:-5] if name.endswith(".pnum") else None
        if fig in FIGURE_NAMES:
            tab = recipes[fig]
            out[f"{fig}.tnum"] = _Rec(f"{fig}.tnum", tab.fn, None, tab.case, tab.plain)
            continue
        if name in FIGURE_NAMES:
            pro = recipes[f"{name}.pnum"]
            out[name] = _Rec(name, pro.fn, rec.unicode, rec.case, pro.plain)
            continue
        out[name] = rec
    return out


__all__ = ["FORMS", "CASE", "PNUM_SIDES", "proportional_default", "small_advance", "tabular"]
