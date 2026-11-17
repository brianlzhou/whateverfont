"""Mark positioning: anchors and the `mark`, `mkmk` and `ccmp` features.

A combining mark (U+0300 to U+0341) is a glyph with no advance, drawn above the
x-height or below the baseline around x = 0. The `mark` feature moves it onto
the letter before it: above marks to the letter's top anchor, below marks to
its bottom anchor, the ogonek to the right foot, and the horn to the upper
right of o and u. `mkmk` stacks marks. `ccmp` swaps i and j for their dotless
forms when a mark goes above them.

Vietnamese text needs none of this when it is typed with its precomposed
letters, and a shaper puts decomposed text back together into those letters.
"""

from __future__ import annotations

import math

from .geom import contour_bounds

ABOVE = ("gravecomb", "acutecomb", "circumflexcomb", "tildecomb", "macroncomb", "brevecomb", "dotaccentcomb",
         "dieresiscomb", "ringcomb", "hungarumlautcomb", "caroncomb", "hookabovecomb", "gravetonecomb",
         "acutetonecomb")
BELOW = ("commaaccentcomb", "cedillacomb", "dotbelowcomb")
OGONEK = ("ogonekcomb",)
HORN = ("horncomb",)
MARKS = ABOVE + BELOW + OGONEK + HORN
#: The letters that take a horn: it grows from their right side, a little below the top.
HORN_BASES = ("o", "u", "O", "U")
ASCENDERS = set("bdfhklt") | {"thorn", "eth", "germandbls", "lslash", "dcroat", "hbar",
                              # б ф ђ ћ һ, and β δ ζ θ λ ξ φ ψ
                              "uni0431", "uni0444", "uni0452", "uni045B", "uni04BB",
                              "beta", "delta", "zeta", "theta", "lambda", "xi", "phi", "psi"}


def _right_edge(contours, b, y: float) -> float:
    """The right edge of the ink on the line at height ``y`` (the right of the glyph if there is none)."""
    from .outline import intersection, rect
    try:
        part = contour_bounds(intersection(contours, [rect(b[0] - 10, y - 1, b[2] + 10, y + 1)]))
    except Exception:
        part = None
    return (part or b)[2]


def _center_in_band(contours, b, y0: float, y1: float) -> float:
    """Horizontal center of the ink between heights y0 and y1 (the whole glyph if there is none)."""
    from .outline import intersection, rect
    try:
        part = contour_bounds(intersection(contours, [rect(b[0] - 10, y0, b[2] + 10, y1)]))
    except Exception:
        part = None
    bb = part or b
    return (bb[0] + bb[2]) / 2


def _top_height(name: str, case: str, p) -> float:
    if case == "upper" or case == "figure":
        return p.cap
    return p.asc if name in ASCENDERS else p.xh


def feature(glyphs: dict, cases: dict, p) -> str:
    """Feature code for the glyphs present. ``cases`` maps a glyph name to its recipe case."""
    marks = [m for m in MARKS if m in glyphs]
    if not marks:
        return ""
    gap = p.xh * 0.06
    lines = []
    for m in marks:
        cls = "top" if m in ABOVE else ("bottom" if m in BELOW else ("horn" if m in HORN else "ogonek"))
        y = int(round(p.xh)) if cls == "top" else (int(round(p.xh * 0.80)) if cls == "horn" else 0)
        lines.append(f"markClass {m} <anchor 0 {y}> @{cls};")
    bases, mkmk = [], []
    for name, g in glyphs.items():
        if name in MARKS or name.startswith(".") or not g.contours or "." in name:
            continue
        b = contour_bounds(g.contours)
        ref = _top_height(name, cases.get(name, "lower"), p)
        cx = _center_in_band(g.contours, b, ref * 0.55, b[3] + 1)           # j, f: the stem, not the tail
        cx_bottom = _center_in_band(g.contours, b, b[1] - 1, ref * 0.30)
        top = ref if b[3] < ref + p.cap * 0.10 else b[3] + gap     # a letter that has a mark already
        if "top" in g.anchors:
            # the letter says where its middle is: ơ and ư, whose horn would pull the middle to the right
            a = g.anchors["top"]
            cx = a.real + (top - a.imag) * math.tan(math.radians(p.slant))
        sw = p.weight
        parts = [f"<anchor {int(round(cx))} {int(round(top))}> mark @top"]
        if any(m in BELOW for m in marks):
            parts.append(f"<anchor {int(round(cx_bottom))} 0> mark @bottom")
        if "ogonekcomb" in marks:
            parts.append(f"<anchor {int(round(b[2] - sw * 0.55))} 0> mark @ogonek")
        if "horncomb" in marks and name in HORN_BASES:
            y = ref * 0.80
            parts.append(f"<anchor {int(round(_right_edge(g.contours, b, y)))} {int(round(y))}> mark @horn")
        bases.append(f"    pos base {name} " + " ".join(parts) + ";")
    for m in marks:
        if m not in ABOVE:
            continue
        b = contour_bounds(glyphs[m].contours)
        top = (b[3] if b else p.xh * 1.4) + gap
        mkmk.append(f"    pos mark {m} <anchor 0 {int(round(top))}> mark @top;")
    out = lines + ["", "feature mark {"] + bases + ["} mark;"]
    if mkmk:
        out += ["", "feature mkmk {"] + mkmk + ["} mkmk;"]
    tops = [m for m in marks if m in ABOVE]
    subs = []
    if "dotlessi" in glyphs and "i" in glyphs:
        subs.append("    sub i' @CombiningTop by dotlessi;")
    if "dotlessj" in glyphs and "j" in glyphs:
        subs.append("    sub j' @CombiningTop by dotlessj;")
    # the Cyrillic і and ј too: a stressed і (і́) loses its dot, as í does
    if "dotlessi" in glyphs and "uni0456" in glyphs:
        subs.append("    sub uni0456' @CombiningTop by dotlessi;")
    if "dotlessj" in glyphs and "uni0458" in glyphs:
        subs.append("    sub uni0458' @CombiningTop by dotlessj;")
    if tops and subs:
        out = [f"@CombiningTop = [{' '.join(tops)}];", ""] + out + ["", "feature ccmp {"] + subs + ["} ccmp;"]
    return "\n".join(languages(glyphs) + out + [""] + locl(glyphs)) + "\n"


# Language systems come first in a feature file. Every feature applies to all of them.
LANGUAGES = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "languagesystem latn ROM;",
             "languagesystem latn MOL;", "languagesystem latn CAT;", ""]


def languages(glyphs: dict) -> list:
    """The language systems of a font: Latin, and Cyrillic and Greek if the font has their letters. A
    shaper falls back on DFLT for a script that is not listed, but some programs kern and place marks
    only for a script the font names."""
    codes = {g.unicode for g in glyphs.values() if getattr(g, "unicode", None) is not None}
    more = []
    if codes & set(range(0x0400, 0x0530)):
        more.append("languagesystem cyrl dflt;")
    if codes & (set(range(0x0384, 0x03D0)) - {0x03A9, 0x03C0}):     # not only the Ω and π of the Latin set
        more.append("languagesystem grek dflt;")
    return LANGUAGES[:-1] + more + [""]


def locl(glyphs: dict) -> list:
    """Language forms: Romanian and Moldovan commas, and the Catalan middle dot."""
    out = ["feature locl {", "    script latn;"]
    pairs = [(a, b) for a, b in (("Scedilla", "Scommaaccent"), ("scedilla", "scommaaccent"),
                                 ("Tcedilla", "Tcommaaccent"), ("tcedilla", "tcommaaccent"))
             if a in glyphs and b in glyphs]
    if pairs:
        rule = f"    sub [{' '.join(a for a, _ in pairs)}] by [{' '.join(b for _, b in pairs)}];"
        out += ["    language ROM;", rule, "    language MOL;", rule]
    if {"l", "L", "periodcentered", "periodcentered.loclCAT", "periodcentered.loclCAT.case"} <= set(glyphs):
        out += ["    language CAT;",
                "    sub l periodcentered' l by periodcentered.loclCAT;",
                "    sub L periodcentered' L by periodcentered.loclCAT.case;"]
    out.append("} locl;")
    return out if len(out) > 3 else []
