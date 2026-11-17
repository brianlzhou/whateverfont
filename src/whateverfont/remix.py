"""Remix: restyle the outlines of an existing, openly licensed font.

This is the quick path to "the same font, but rounder / bolder / slanted".
The result is a derivative work. For a font under the SIL Open Font License
that means: it stays under the OFL, it keeps the original copyright notice,
and it gets a new name. ``remix_file`` keeps the notices and requires the
new name.
"""

from __future__ import annotations

import math
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from .compile import _tt_glyph, quadratic_points, save_woff2, slug
from .geom import cross, dot, seg_tangent, transform_contour
from .outline import ContourPen, dilate, union
from .stroke import clean, fillet

LATIN = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x180))
         + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x20AC, 0x2212, 0x00D7])
HINT_TABLES = ("fpgm", "prep", "cvt ", "hdmx", "VDMX", "LTSH", "DSIG", "cvar")
#: The name records that hold the font's name: family, style, unique ID, full name, PostScript name, the
#: typographic and WWS names, the Mac full name, the CID name and the variations prefix. A remix replaces
#: them in every language.
RENAMED = {1, 2, 3, 4, 6, 16, 17, 18, 20, 21, 22, 25}


def round_corners(contours: list, radius: float, min_angle: float = 22.0) -> list:
    """Round every corner sharper than ``min_angle`` degrees."""
    out = []
    for c in contours:
        n = len(c)
        if n < 2:
            out.append(c)
            continue
        radii = []
        for i in range(n):
            d_in = seg_tangent(c[(i - 1) % n], 1)
            d_out = seg_tangent(c[i], 0)
            ang = abs(math.degrees(math.atan2(cross(d_in, d_out), dot(d_in, d_out))))
            radii.append(radius if ang > min_angle else None)
        out.append(clean(fillet(c, radii)))
    return out


def remix_contours(contours: list, upm: int, round_: float = 0.0, embolden: float = 0.0, slant: float = 0.0,
                   width: float = 1.0) -> tuple:
    """Apply the filters to one glyph. Returns (contours, extra advance)."""
    k = upm / 1000.0
    extra = 0.0
    if not contours:
        return contours, extra
    if embolden:
        contours = dilate(contours, embolden * k / 2, miter=True)
        contours = [transform_contour(c, lambda q: q + embolden * k / 2) for c in contours]
        extra = embolden * k
    if width != 1.0:
        contours = [transform_contour(c, lambda q: complex(q.real * width, q.imag)) for c in contours]
    if round_:
        contours = round_corners(contours, round_ * k)
    if slant:
        t = math.tan(math.radians(slant))
        contours = [transform_contour(c, lambda q: complex(q.real + q.imag * t, q.imag)) for c in contours]
    return contours, extra


def _reserved_names(font: TTFont) -> list:
    """Reserved Font Names declared in the copyright or license text."""
    import re
    names = []
    for rec in font["name"].names:
        if rec.nameID in (0, 13):
            text = rec.toUnicode()
            for m in re.finditer(r"Reserved Font Name[s]?\s*[:\"“']*\s*([^\n.]+)", text, re.I):
                for part in re.split(r",| and |\"|“|”", m.group(1)):
                    part = part.strip(" '\"“”()")
                    if 1 < len(part) < 40:
                        names.append(part)
    return names


OPEN_LICENSES = (
    r"open font licen[cs]e", r"\bOFL\b", r"scripts\.sil\.org/OFL", r"openfontlicense\.org", r"apache licen[cs]e",
    r"apache\.org/licenses", r"ubuntu font licen[cs]e", r"GNU (general|lesser) public licen[cs]e", r"\bL?GPL\b",
    r"bitstream vera", r"\bMIT licen[cs]e", r"public domain", r"\bCC0\b", r"creativecommons\.org/publicdomain",
    r"creativecommons\.org/licenses/by", r"IPA font licen[cs]e", r"arphic public licen[cs]e",
)


def declared_license(font: TTFont) -> tuple:
    """(is_open, the text that says so). Reads the license, its URL and the copyright notice."""
    import re
    texts = []
    for nid in (13, 14, 0):
        rec = font["name"].getDebugName(nid)
        if rec:
            texts.append(rec)
    for text in texts:
        for pattern in OPEN_LICENSES:
            if re.search(pattern, text, re.I):
                return True, text
    return False, (texts[0] if texts else "")


def symbol_codes(font: TTFont) -> list:
    """Code points of a symbol-encoded cmap (Wingdings and friends map their pictures to U+F020-U+F0FF)."""
    codes = set()
    for table in font["cmap"].tables:
        if table.platformID == 3 and table.platEncID == 0:
            codes |= set(table.cmap)
    return sorted(codes)


def remix_file(src: str | Path, out: str | Path, name: str, round_: float = 0.0, embolden: float = 0.0,
               slant: float = 0.0, width: float = 1.0, at: dict | None = None, subset: bool = False,
               style: str = "Regular") -> Path:
    """Restyle ``src`` and write ``<out>/<Name>-<Style>.ttf`` (and .woff2).

    The remix keeps every character and every OpenType feature of the source. With ``subset`` it is cut
    down to Latin letters and the basic features, for a smaller file.

    Any TrueType font is accepted. :func:`declared_license` says whether the
    source declares an open license; the command line prints a note when it
    does not.
    """
    font = TTFont(str(src))
    if "glyf" not in font:
        raise ValueError("only TrueType-flavored fonts (.ttf with a glyf table) are supported so far")
    original = font["name"].getBestFamilyName() or "the original font"
    low = name.lower()
    if low == original.lower() or original.lower() in low.split():
        raise ValueError(f"the new name must not reuse {original!r}: a remix is a different font")
    for reserved in _reserved_names(font):
        if reserved.lower() in low:
            raise ValueError(f"{reserved!r} is a Reserved Font Name of the original; choose another name")

    if "fvar" in font:
        from fontTools.varLib import instancer
        loc = {a.axisTag: a.defaultValue for a in font["fvar"].axes}
        loc.update(at or {})
        font = instancer.instantiateVariableFont(font, loc, inplace=False)
    if subset:
        from fontTools import subset as ft_subset
        opts = ft_subset.Options()
        opts.layout_features = ["kern", "liga", "mark", "mkmk", "ccmp", "locl"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = True
        symbols = symbol_codes(font)
        if symbols:
            opts.symbol_cmap = True     # fontTools drops the symbol cmap unless asked
            opts.legacy_cmap = True     # and the Mac Roman cmap that maps the same pictures to A-Z on a Mac
        sub = ft_subset.Subsetter(opts)
        # A symbol font keeps its pictures: they live at U+F020-U+F0FF, not at Latin code points.
        sub.populate(unicodes=LATIN + symbols)
        sub.subset(font)
    drawn = [g for g in font.getGlyphOrder() if g != ".notdef" and font["glyf"][g].numberOfContours]
    if not drawn:
        raise ValueError(f"{original} has no glyphs that whateverfont can keep (it covers no Latin or symbol code "
                         "points), so the remix would be empty")

    upm = font["head"].unitsPerEm
    gs = font.getGlyphSet()
    glyf, hmtx = font["glyf"], font["hmtx"]
    new = {}
    for gname in font.getGlyphOrder():
        rec = DecomposingRecordingPen(gs)
        gs[gname].draw(rec)
        pen = ContourPen()
        rec.replay(pen)
        contours = union(pen.contours) if embolden else pen.contours
        contours, extra = remix_contours(contours, upm, round_, embolden, slant, width)
        adv, _ = hmtx[gname]
        new[gname] = (contours, int(round(adv * width + (extra if adv else 0))))
    for gname, (contours, adv) in new.items():
        g = _tt_glyph(quadratic_points([contours])[0]) if contours else _tt_glyph([])
        glyf[gname] = g
        g.recalcBounds(glyf)
        hmtx[gname] = (adv, int(getattr(g, "xMin", 0) or 0))
    for tag in HINT_TABLES:
        if tag in font:
            del font[tag]
    font["maxp"].maxComponentElements = 0
    font["maxp"].maxComponentDepth = 0
    if slant:
        font["post"].italicAngle = -float(slant)

    # names: a new family name, the original notices kept. The records of the old name go in every language:
    # a font with Japanese, Chinese or Korean names would keep the source's name there.
    ps = f"{slug(name)}-{slug(style)}"
    table = font["name"]
    table.names = [rec for rec in table.names if rec.nameID not in RENAMED]
    for nid, value in ((1, name), (2, style), (3, f"{ps};whateverfont-remix"), (4, f"{name} {style}"), (6, ps)):
        table.setName(value, nid, 3, 1, 0x409)
        table.setName(value, nid, 1, 0, 0)
    filters = ", ".join(f"{k} {v:g}" for k, v in (("round", round_), ("embolden", embolden), ("slant", slant),
                                                  ("width", width)) if v not in (0.0, 1.0) or (k == "width" and v != 1.0))
    table.setName(f"A remix of {original} made with whateverfont ({filters}). {original} is the work of its "
                  f"authors; this modified version is distributed under the same license.", 10, 3, 1, 0x409)

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{ps}.ttf"
    font.save(path)
    save_woff2(path, out)
    return path
