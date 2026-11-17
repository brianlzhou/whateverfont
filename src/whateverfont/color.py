"""Color fonts: COLR version 0 layers with CPAL palettes.

Version 0 is flat color only, and it is the one color format that renders in
Chrome, Firefox, Safari and CoreText alike. A color glyph keeps a normal
outline as its base, so software without color support still shows a letter.
"""

from __future__ import annotations

from fontTools.colorLib.builder import buildCOLR, buildCPAL


def _rgba(value) -> tuple:
    if isinstance(value, (tuple, list)):
        v = list(value) + [1.0] * (4 - len(value))
        return tuple(float(x) for x in v[:4])
    h = value.lstrip("#")
    if len(h) == 6:
        h += "ff"
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4, 6))


def add_color(font, family, colr: dict, result=None) -> bool:
    """Add COLR/CPAL tables. ``colr`` maps a base glyph to [(layer glyph, palette key)]."""
    if not colr:
        return False
    if not family.palettes:
        if result is not None:
            result.warn("glyphs have color layers but the family has no palettes; built without color")
        return False
    keys = []
    for layers in colr.values():
        for _, key in layers:
            if key not in keys:
                keys.append(key)
    first = next(iter(family.palettes.values()))
    palettes = []
    for name, pal in family.palettes.items():
        row = []
        for key in keys:
            if key not in pal and key not in first and result is not None:
                result.warn(f"palette {name!r} has no color for {key!r}; used black")
            row.append(_rgba(pal.get(key, first.get(key, "#000000"))))
        palettes.append(row)
    font["COLR"] = buildCOLR({base: [(layer, keys.index(key)) for layer, key in layers]
                              for base, layers in colr.items()},
                             version=0, glyphMap=font.getReverseGlyphMap())
    font["CPAL"] = buildCPAL(palettes, paletteLabels=list(family.palettes), nameTable=font["name"])
    return True
