"""Sets of characters for ``whateverfont retrace --only``: the common characters of Japanese, Chinese and Korean.

A font of Chinese characters holds tens of thousands of glyphs. These sets keep the characters that everyday
text uses, taken from the national standards through Python's own codecs, so no data file is needed:

- ``japanese``: hiragana, katakana and the 2,965 kanji of JIS X 0208 level 1.
- ``chinese``: the 3,755 characters of GB 2312 level 1 (Simplified Chinese).
- ``traditional``: the 5,401 characters of Big5 level 1 (Traditional Chinese).
- ``korean``: the 2,350 Hangul syllables of KS X 1001.

Each set also has the space, the punctuation of East Asia (U+3000 to U+303F), the fullwidth forms and the
quotes and dashes of General Punctuation. Latin letters and figures are not in the sets: the Latin family sets
them. Korean has the ASCII punctuation too, because Korean text uses it.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

#: name -> (codec, first lead byte, last lead byte): the rows of a double-byte standard that hold the set
STANDARDS = {
    "japanese": ("euc_jp", 0xB0, 0xCF),      # JIS X 0208 level 1 kanji
    "chinese": ("gb2312", 0xB0, 0xD7),       # GB 2312 level 1 hanzi
    "traditional": ("big5", 0xA4, 0xC6),     # Big5 level 1 hanzi (A440 to C67E)
    "korean": ("euc_kr", 0xB0, 0xC8),        # KS X 1001 Hangul syllables
}

NAMES = tuple(STANDARDS)

#: The trail bytes of each codec. Big5 uses 40-7E as well as A1-FE.
TRAILS = {"big5": list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF))}
#: Sets that keep the ideographs of their rows only. The last row of Big5 level 1 goes on with kana.
IDEOGRAPHS_ONLY = {"traditional"}

#: the punctuation every set has: the ideographic space, brackets and stops, and the fullwidth forms
EAST_ASIAN = set(range(0x3000, 0x3040)) | set(range(0xFF01, 0xFF61)) | set(range(0xFFE0, 0xFFE7))
#: from General Punctuation and Latin-1: quotes, dashes, the ellipsis and the middle dot
GENERAL = {0x20, 0xA0, 0xB7, 0x2010, 0x2013, 0x2014, 0x2015, 0x2018, 0x2019, 0x201C, 0x201D, 0x2025, 0x2026,
           0x2030, 0x2032, 0x2033, 0x203B}
#: Korean writes with the ASCII stops, commas, brackets and quotes
ASCII_PUNCTUATION = {ord(c) for c in "!\"'(),-./:;?[]~"}
KANA = set(range(0x3041, 0x3097)) | set(range(0x3099, 0x30A0)) | set(range(0x30A0, 0x3100))


def standard(name: str) -> set:
    """The ideographs or syllables of a named set, decoded row by row from its standard."""
    codec, first, last = STANDARDS[name]
    out = set()
    for lead in range(first, last + 1):
        for trail in TRAILS.get(codec, range(0xA1, 0xFF)):
            try:
                ch = bytes([lead, trail]).decode(codec)
            except UnicodeDecodeError:
                continue
            if len(ch) != 1:
                continue
            if name in IDEOGRAPHS_ONLY and not unicodedata.name(ch, "").startswith("CJK UNIFIED IDEOGRAPH"):
                continue
            out.add(ord(ch))
    return out


def named(name: str) -> set:
    """Every code point of a named set: its characters and its punctuation."""
    key = name.strip().lower()
    if key not in STANDARDS:
        raise ValueError(f"no character set named {name!r}; the named sets are: {', '.join(NAMES)}")
    cps = standard(key) | EAST_ASIAN | GENERAL
    if key == "japanese":
        cps |= KANA
    if key == "korean":
        cps |= ASCII_PUNCTUATION
    return cps


def from_file(path) -> set:
    """The characters of a UTF-8 text file. Line breaks and tabs do not count."""
    text = Path(path).read_text(encoding="utf-8")
    return {ord(c) for c in text if c not in "\r\n\t﻿"}


def resolve(specs) -> set:
    """Code points for one or more specs, each a named set or a text file. A string may list several, split by
    commas: ``japanese,extra.txt``."""
    if isinstance(specs, str):
        specs = [specs]
    out = set()
    for spec in specs:
        for part in str(spec).split(","):
            part = part.strip()
            if not part:
                continue
            if part.lower() in STANDARDS:
                out |= named(part)
            elif Path(part).is_file():
                out |= from_file(part)
            else:
                raise ValueError(f"--only {part!r} is neither a named set ({', '.join(NAMES)}) nor a text file")
    return out
