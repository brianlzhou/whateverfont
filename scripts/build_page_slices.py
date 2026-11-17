#!/usr/bin/env python3
"""Cut a small slice of each large font of another script: the letters of the page's own words.

A whole Japanese font is 1 to 5 MB. The page shows a few words in it. So each large font in
examples/retrace gets a slice in site/page-fonts/slices/ that holds only the letters of the words that the
page sets in that family and language. The site gives the slice those characters and the whole font the
rest, so a reader loads the whole font only after typing other words.

Run it again after a translation changes or a font is rebuilt:  python scripts/build_page_slices.py
It needs fontTools (the site build itself does not).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

#: A font smaller than this is loaded whole.
LEAST = 250_000


def words_of(f: dict, code: str, poster: set, demo: set) -> str:
    """Every word that the page sets in the family ``f`` in the language ``code``."""
    texts = site.translations().get(code, {})
    keys = [site.sample_key(f), f"word.{f['id']}", f"block.{f['id']}"]
    if f["name"] in poster:
        keys.append("poster.text")
    if f["name"] in demo:
        keys += ["demo.big", "demo.small"]
    return " ".join(re.sub(r"<[^>]+>", " ", texts.get(k, "")) for k in keys)


def main() -> int:
    projects = site.load() + site.load_library()
    for f in (f for p in projects for f in p["families"]):
        site.sample_key(f)              # families that share a sample share its key, in the order of the page
    parts = site.load_parts(projects, slices=False)
    poster = {row[0] for row in site.HERO}
    demo = {"Last Bell Rounds", "Last Bell Snow"}
    out = site.PAGE_FONTS / "slices"
    out.mkdir(parents=True, exist_ok=True)
    listed = []
    for part in parts:
        if part["web"].stat().st_size < LEAST:
            continue
        fams = [f for p in projects for f in p["families"] if part in f.get("parts", [])]
        text = " ".join(words_of(f, part["language"], poster, demo) for f in fams)
        wanted = sorted({ord(c) for c in text if site.in_script(ord(c), part["language"])})
        if not wanted:
            continue
        font = TTFont(str(part["web"]))
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = False
        opts.flavor = "woff2"
        cutter = subset.Subsetter(opts)
        cutter.populate(unicodes=wanted)
        cutter.subset(font)
        font.flavor = "woff2"
        font.recalcTimestamp = False        # the same words give the same file
        path = out / f"{part['id']}.woff2"
        font.save(str(path))
        have = sorted(cp for cp in font.getBestCmap() if site.in_script(cp, part["language"]))
        listed.append({"part": part["name"], "file": f"slices/{path.name}",
                       "codepoints": " ".join(f"{cp:X}" for cp in have)})
        print(f"{part['name']:28s} {part['web'].stat().st_size / 1e6:5.1f} MB -> {path.stat().st_size / 1e3:6.1f} KB, "
              f"{len(have)} characters")
    # A large Latin font (an effect font with the whole character set) gets a slice too: the basic letters
    # and the letters of its own words on the page, in every language that it sets.
    basic = set(range(0x20, 0x7F)) | {0xA0}
    latin = []
    for f in (f for p in projects for f in p["families"]):
        if f["web"].stat().st_size < LEAST or len(f["codepoints"]) < 200:
            continue
        have = set(f["codepoints"])
        text = f["sample"] + " ".join(row[1] for row in site.DROPS if row[0] == f["name"]) + re.sub(r"<[^>]+>", " ", site.POSTER)
        for code in site.translations():
            text += words_of(f, code, poster, demo)
        wanted = sorted((basic | {ord(c) for c in text}) & have)
        font = TTFont(str(f["web"]))
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = False
        cutter = subset.Subsetter(opts)
        cutter.populate(unicodes=wanted)
        cutter.subset(font)
        font.flavor = "woff2"
        font.recalcTimestamp = False        # the same words give the same file
        path = out / f"{f['id']}-basic.woff2"
        font.save(str(path))
        latin.append({"family": f["name"], "file": f"slices/{path.name}",
                      "codepoints": " ".join(f"{cp:X}" for cp in sorted(font.getBestCmap()))})
        print(f"{f['name']:28s} {f['web'].stat().st_size / 1e3:6.0f} KB -> {path.stat().st_size / 1e3:6.1f} KB, "
              f"{len(font.getBestCmap())} characters")
    (site.PAGE_FONTS / "slices.json").write_text(
        json.dumps({"about": "Slices of large fonts: the letters of the page's own words. A slice loads with the "
                             "page, and the whole font only when a reader types other letters. Made by "
                             "scripts/build_page_slices.py.", "slices": listed, "latin": latin},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
