"""Glyph recipes that ship with whateverfont."""

from ..glyph import Recipes
from .accents import ACCENTS
from .extended import EXTENDED
from .figures import FIGURES
from .forms import FORMS
from .letters import LETTERS
from .lower import LOWER
from .punct import PUNCT
from .signs import SIGNS
from .symbols import SYMBOLS
from .upper import UPPER
from .vietnamese import VIETNAMESE


def _scripts(r: Recipes, greek: bool, cyrillic: bool) -> Recipes:
    """Add the Greek and the Cyrillic alphabets after everything else, so the Latin glyphs keep their place."""
    if greek:
        from .greek import GREEK
        r.update(GREEK)
        # the Greek question mark is the semicolon of this set, as heavy as it (a sign, in a monospaced set)
        q = r["uni037E"]
        r["uni037E"] = type(q)(q.name, q.fn, q.unicode, r["semicolon"].case, q.plain)
    if cyrillic:
        from .cyrillic import CYRILLIC
        r.update(CYRILLIC)
    return r


def latin(greek: bool = True, cyrillic: bool = True) -> Recipes:
    """A fresh copy of the basic recipe set. Add or replace recipes freely.

    It covers GF Latin Core and Vietnamese: every letter of the Vietnamese alphabet, with the
    horn, the hook above, the dot below and the stacked marks, and the dong sign. It also has the
    rest of Latin Extended-A, letters for Pinyin, Azerbaijani, Yoruba, Igbo and Hausa, the currency
    signs, the Mac Roman math signs, arrows, shapes, superscripts, subscripts and fractions: 605 code
    points of Latin and signs. The glyphs without a code point (``zero.pnum``, ``one.dnom``,
    ``hyphen.case`` and the others) are the forms that the OpenType features choose (see
    :mod:`whateverfont.features`).

    It also has modern Greek (``greek``) and Cyrillic (``cyrillic``): see :mod:`.greek` and
    :mod:`.cyrillic`. ``latin(greek=False, cyrillic=False)`` leaves them out.
    """
    r = Recipes()
    # New groups come last, so the glyphs that were there before keep their place in the font
    for part in (UPPER, LOWER, FIGURES, PUNCT, ACCENTS, EXTENDED, SYMBOLS, VIETNAMESE, LETTERS, SIGNS, FORMS):
        r.update(part)
    return _scripts(r, greek, cyrillic)


def mono(greek: bool = True, cyrillic: bool = True) -> Recipes:
    """The Latin set with the letters a monospaced font needs: i, j, l, I and 1 with bars, and a dotted zero.

    It also has the box drawings and block elements (U+2500 to U+259F), which fill the cell and join up.
    A family whose base has ``mono`` set uses this set unless it is given another. In a monospaced
    font every figure is as wide as the cell, so the font gets no ``pnum`` feature. Greek and Cyrillic
    come last, as in :func:`latin`; their І і ј draw the barred I, i and j of this set.
    """
    from .box import BOX
    from .monospace import MONO
    r = latin(greek=False, cyrillic=False)
    r.update(MONO)
    r.update(BOX)
    return _scripts(r, greek, cyrillic)
