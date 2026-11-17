"""Build the project site from the example projects.

Run from the repository root:  python3 scripts/build_site.py

The site is one page that sets every example font live, with its brief, axes, palettes, review board and a
download. It uses only the standard library, so the host can build it without installing whateverfont. Rebuild
the examples first (scripts/build_examples.py) when the fonts change.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import os
import re
import shutil
import struct
import unicodedata
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
EXAMPLES = ROOT / "examples"
LIBRARY = ROOT / "library"
#: The example faces that the pages themselves are set in (see style.css).
PAGE_FACES = {"arroyo", "arroyo-text", "gantry", "tally-mono"}
REPO = "https://github.com/brianlzhou/whateverfont"
#: The GitHub account that the example fonts are credited to: the one that holds the repository.
OWNER = REPO.split("/")[3]
#: Where the votes and views are counted: the address of the Cloudflare Worker in worker/ (see its
#: wrangler.jsonc: the two must agree). COUNTS is what the pages get. With an empty COUNTS the pages ask
#: for nothing, and they show no vote buttons and no numbers: set COUNTS = "" here to turn the counts
#: off, or build with WHATEVERFONT_COUNTS set to another address (or to nothing).
COUNTS_ADDRESS = "https://www.brianzhou.org/api/fonts"
COUNTS = COUNTS_ADDRESS
URL = "https://fonts.brianzhou.org"
# Search engines skip the site until the project is public under its final name. Set True at launch.
INDEX = True

PROJECTS = ["starry", "arroyo", "lastbell", "hopstep", "leafpile", "drippelgang", "lacentine", "panework", "ombrelle", "cabochon", "haystack", "caliper", "dayshift", "setsquare", "softboil", "doorstep", "hedmast", "lowslung", "scanstep", "etchant", "tinsheen", "teacloth", "knollrise", "aviary", "platen", "pinout", "greenbar", "tally",
            "gilt", "kanagawa", "cutout", "wassail", "neon", "crate", "effects", "pebble"]
# A color font is drawn for a ground: gold for a dark wall, cut paper for a light table. The page shows
# every color sample on the ground of its palette, in the light and the dark theme alike.
PAPER_GROUND, DARK_GROUND = "#F6F1E7", "#15171C"
GROUNDS = {
    "Leafpile": {"Maple": "#F4E9D4", "Ginkgo": "#23302C", "Oak": "#E4E2C8", "Late October": "#17120E"},
    "Drippelgang": {"Slime": "#1C0E2B", "Pumpkin": "#120A05", "Black Cat": "#FFFFFF", "Ghost": "#0F1A2C"},
    "Lacentine": {"Valentine": "#F4BFCB", "Candy": "#FFF8EE", "Pink": "#B3122E", "Chocolate": "#2B150E"},
    "Panework Boogie": {"Broadway": "#1B1C21", "Midtown": "#F3F1EC"},
    "Panework": {"Primary": "#F3F1EC", "Stone": "#FFFFFF", "Night": "#101217"},
    "Ombrelle Initials": {"Afternoon": "#F3EBD5", "Harbor": "#F4DED2", "Circus": "#1F1B47"},
    "Ombrelle": {"Afternoon": "#F3EBD5", "Harbor": "#F4DED2", "Circus": "#1F1B47"},
    "Cabochon Rose": {"Jade": "#7A1418", "Ruby": "#F2EADB", "Sapphire": "#B08636", "Amethyst": "#D2D8C6", "Amber": "#15233A", "Onyx": "#C6A77B"},
    "Cabochon": {"Jade": "#7A1418", "Ruby": "#F2EADB", "Sapphire": "#B08636", "Amethyst": "#D2D8C6", "Amber": "#15233A", "Onyx": "#C6A77B"},
    "Aviary Color": {"Field Guide": "#F3ECDC", "Letterpress": "#F3ECDC", "Risograph": "#F7F3EA", "Chalk": "#22262D"},
    "Cutout Color": {"Paper": "#FBF7EC", "Night": "#14182B", "Lagoon": "#F2F7F4"},
    "Hopstep": {"Bright": "#FBF7EC", "Chalk": "#141416", "Poster": "#141416", "Quiet": "#FBF7EC"},
    "Billboard": {"Peach": "#FBE7CF", "Lime": "#F3F6DF", "Paper": "#2A2F3A"},
    "Pointille": {"Park": "#F6F0DE", "Dusk": "#2B2140"},
    "Meridian": {"Sunset": "#150F26", "Sea": "#07182B"},
    "Gilt": {"Gold on Dark": "#0E0B07"}, "Gilt Robe": {"Gold on Dark": "#0E0B07"}, "Gilt Bloom": {"Gold on Dark": "#0E0B07"},
    "Halation": {"Green": "#050806", "Amber": "#0A0703", "White": "#06080C", "Paper": "#F6F1E7"},
    "Haystack Initials": {"Noon": "#EFE6C4", "Sunset": "#F6D9B8", "Snow": "#EEF1F7", "Dusk": "#C4BFD9"},
    "Haystack": {"Noon": "#EFE6C4", "Sunset": "#F6D9B8", "Snow": "#EEF1F7", "Dusk": "#C4BFD9"},
    "Kanagawa": {"Print": "#EFE4C8", "Night": "#0F1B2E", "Bare": "#F6F1E7"},
    "Kanagawa Brush": {"Print": "#EFE4C8", "Night": "#0F1B2E", "Bare": "#F6F1E7"},
    "Kanagawa Swell": {"Print": "#EFE4C8", "Night": "#0F1B2E", "Bare": "#F6F1E7"},
    "Last Bell Snow": {"Mitten": "#12372A", "Pine": "#6E1B1B", "Cocoa": "#D9C2A0", "Midnight": "#14213D"},
    "Neon Glow": {"Pink": "#0B0A12", "Blue": "#0B0A12", "Pink Day": "#F6F1E7", "Blue Day": "#F6F1E7"},
    "Starry Initials": {"Night": "#0A0F24", "Dawn": "#F4E9DD", "Ink": "#F6F1E7"},
    "Starry": {"Night": "#0A0F24", "Dawn": "#F4E9DD", "Ink": "#F6F1E7"},
    "Scanstep Color": {"Title": "#141A4A", "Dungeon": "#121014", "Handheld": "#B6C65A", "Manual": "#F4EAD2"},
    "Etchant": {"Green": "#0F3D24", "Black": "#141517", "Blue": "#0C2D63", "Paper": "#FFFFFF"},
    "Tinsheen": {"Chrome": "#0A1A4F", "Gold": "#2A0710", "Magenta": "#000000", "Lime": "#03181C"},
    "Tinsheen Line": {"Chrome": "#0A1A4F", "Gold": "#2A0710", "Magenta": "#000000", "Lime": "#03181C"},
    "Teacloth": {"Linen": "#E6DCC6", "Blue": "#F8F7F2", "Garden": "#EDE5D2", "Night": "#232B38"},
    "Teacloth Initials": {"Linen": "#E6DCC6", "Blue": "#F8F7F2", "Garden": "#EDE5D2", "Night": "#232B38"},
    "Knollrise": {"Trail": "#F4EEDC", "Sea Chart": "#E6F0F2", "Night": "#1A222B", "Desert": "#F7EBDA"},
    "Wassail Initials": {"Christmas": "#F1E6CC", "Ultramarine": "#F1E6CC", "Frost": "#EEF2F6"},
}


# The poster at the top sets the same words in one font after another:
# (family, palette, ground, ink, the request that made it, axis settings).
HERO = [
    ("Starry Initials", "Night", "#0A0F24", "#9DC1E6", "Make me a font like Starry Night", None),
    ("Cabochon", "Jade", "#7A1418", "#8ACDA3", "Make me a font like polished jade", None),
    ("Last Bell Snow", "Mitten", "#12372A", "#F6F1E7", "A font that feels like winter break in middle school", None),
    ("Lacentine", "Valentine", "#F4BFCB", "#7A1022", "Make me a font like a valentine glued on a paper doily", None),
    ("Hopstep", "Bright", "#FBF7EC", "#161616", "Make every letter a person who dances", None),
    ("Cutout Color", "Paper", "#FBF7EC", "#1F53B5", "Like Matisse's paper cut-outs", None),
    ("Ombrelle Initials", "Afternoon", "#F3EBD5", "#2E5A45", "Make me a font like Seurat's Sunday on La Grande Jatte", None),
    ("Dayshift", None, "#F3F3F1", "#16171A", "A plain sans for the interface of my app", None),
    ("Lowslung", None, "#A3201B", "#F6F0E4", "A wide, flat sans for the name of a studio", {"wght": 700, "wdth": 100}),
    ("Drippelgang", "Slime", "#1C0E2B", "#8FE23C", "A font for a Halloween party, dipped in dripping slime", None),
    ("Gilt", "Gold on Dark", "#0D0A06", "#E9C46A", "Gold, like Klimt's The Kiss", None),
    ("Arroyo", None, "#F4EFE6", "#1B1A17", "A calm serif for a long essay", {"wght": 420, "FLAR": 34, "slnt": 0}),
    ("Kanagawa", "Print", "#EFE4C8", "#1E4E7E", "Like Hokusai's Great Wave", None),
    ("Leafpile", "Maple", "#F4E9D4", "#7A2214", "Make me a font like a pile of fall leaves", None),
    ("Panework", "Primary", "#F3F1EC", "#141414", "Make me a font like Mondrian's grids", None),
    ("Platen Ribbon", None, "#F1ECE0", "#1F1D1A", "A typewriter that needs a new ribbon", None),
    ("Neon Glow", "Pink", "#0B0A12", "#FF2E9A", "A neon sign for a bar", None),
    ("Caliper", None, "#E4572E", "#FFF3E2", "Tall and condensed, for headlines", {"wght": 700, "wdth": 60, "FLAR": 45, "slnt": 0}),
    ("Greenbar", None, "#EEF3E6", "#26302A", "A dot-matrix invoice from 1985", None),
    ("Haystack Initials", "Dusk", None, None, "Make me a font like Monet's haystacks", None),
    ("Aviary Color", "Field Guide", "#E3EEF0", "#1B1A17", "Wingdings, but actual birds", None),
    ("Wassail Initials", "Christmas", "#1F3D2B", "#F3E9D2", "Illuminated, like a medieval text, and a little Christmas", None),
    ("Crate Stencil", None, "#C9A26B", "#2A2017", "A stencil font for labels on shipping crates", None),
    ("Marquee", None, "#4A1220", "#F0D089", "Letters with an engraved line, like a theater sign", None),
    ("Pinout", None, "#10151A", "#B8F2C8", "A monospace like the manual of an early computer", None),
    ("Tally Mono", None, "#F1EFEA", "#1B1A17", "A calm monospace for a terminal and an editor", None),
    ("Pebble Sans", None, "#EAEEF1", "#16191C", "Round the corners of Inter", None),
    ("Eight Dials", None, "#F2EEE6", "#1B1A17", "A calm sans with a slider for every decision", None),
]
# The wall under it: one word in each of these fonts, on a ground that suits it.
# (family, word, axis settings, palette or None for the first, ground or None for the palette's own, ink)
GREENBAR_PAPER = "repeating-linear-gradient(#F3F6EC 0 22px, #DCEBD8 22px 44px)"
WALL = [
    ("Starry Initials", "Night", None, "Night", None, None),
    ("Last Bell Snow", "Snow", None, "Mitten", None, None),
    ("Hopstep", "DANCE", None, "Poster", None, None),
    ("Aviary Color", "OWL", None, "Field Guide", "#E3EEF0", "#1B1A17"),
    ("Gilt", "Gold", None, "Gold on Dark", None, None),
    ("Kanagawa", "WAVE", None, "Print", None, None),
    ("Cutout Color", "Paper", None, "Night", None, None),
    ("Platen", "Dear", None, None, None, None),
    ("Greenbar", "TOTAL", None, None, GREENBAR_PAPER, "#26302A"),
    ("Halation", "READY", None, "Green", None, None),
    ("Neon Glow", "Open", None, "Pink", None, None),
    ("Haystack Initials", "Hay", None, "Dusk", None, None),
    ("Wassail Initials", "Noel", None, "Christmas", "#1F3D2B", "#F3E9D2"),
    ("Arroyo", "Quiet", {"wght": 420, "FLAR": 34, "slnt": 0}, None, None, None),
    ("Caliper", "TALL", {"wght": 700, "wdth": 60, "FLAR": 45, "slnt": 0}, None, "#E4572E", "#FFF3E2"),
    ("Crate Stencil", "CRATE", None, None, "#C9A26B", "#2A2017"),
    ("Cabochon", "Jade", None, "Jade", None, None),
    ("Ombrelle Initials", "Park", None, "Afternoon", None, None),
    ("Panework", "Grid", None, "Primary", None, None),
    ("Lacentine", "Love", None, "Valentine", None, None),
    ("Drippelgang", "Boo!", None, "Slime", None, None),
    ("Leafpile", "Fall", None, "Maple", None, None),
    ("Dayshift", "Save", None, None, "#F3F3F1", "#16171A"),
    ("Setsquare", "Angle", None, None, "#16191C", "#F2EEE6"),
    ("Softboil", "Soft", None, None, "#FBE7A1", "#3A2A12"),
    ("Doorstep", "Bread", None, None, "#F3EADB", "#8A3324"),
    ("Hedmast", "Shout", {"wght": 800, "wdth": 75}, None, "#EFEBE0", "#111111"),
    ("Lowslung", "COUPE", {"wght": 700, "wdth": 100}, None, "#A3201B", "#F6F0E4"),
    ("Scanstep Color", "START", None, "Title", None, None),
    ("Etchant", "Trace", None, "Green", None, None),
    ("Tinsheen", "Turbo", None, "Chrome", None, None),
    ("Teacloth", "Home", None, "Linen", None, None),
    ("Knollrise", "Ridge", None, "Trail", None, None),
]

# The wall is laid in rows of four. A wide tile takes two places and shows the font's sample line, the thing
# its brief asked for: an invoice, a letter, a label on a crate. The order makes the wide tiles change sides
# from row to row. A font that is not named here comes after these, in the order of the library.
WALL_ORDER = ["starry", "arroyo", "lastbell",
              "hopstep", "leafpile", "caliper",
              "dayshift", "setsquare", "softboil",
              "drippelgang", "lacentine", "panework", "ombrelle",
              "greenbar", "cabochon", "haystack",
              "aviary", "pinout", "neon",
              "gilt", "kanagawa", "cutout", "tally",
              "platen", "wassail", "eight-dials",
              "effects", "pebble", "crate"]
# font -> how its line is set: "" in the middle, "flush" from the left like a page from a machine
WALL_WIDE = {"starry": "", "caliper": "", "dayshift": "", "greenbar": "flush", "neon": "", "platen": "flush", "crate": ""}

# The numbers of the live demo under "How it works" are the axes of this font of the library. Each axis moves
# one number of the engine, and the demo shows that number, as the design file would have it.
DIALS = "eight-dials"
DIAL_ORDER = ["weight", "contrast", "width", "xh", "roundness", "flare", "slant", "spacing"]
DIAL_START = {"width": 1.0, "slant": 0}       # the engine's own value, where the design file does not set one

# The footer drops one block for each of the wall's fonts, and for these: (family, word, axis settings, palette, ground, ink).
DROPS = WALL + [
    ("Last Bell", "Bell", {"wght": 700}, None, "#F2C14E", "#3A2408"),
    ("Hopstep", "HOP", None, "Bright", "#FBF7EC", "#161616"),
    ("Pinout", "0x3F", None, None, "#10151A", "#B8F2C8"),
    ("Tally Mono", "{ }", None, None, None, None),
    ("Marquee", "NOW", None, None, "#4A1220", "#F0D089"),
    ("Billboard", "Fresh", None, "Peach", None, None),
    ("Turbo", "77", None, None, "#F2C230", "#191919"),
    ("Meridian", "Hour", None, "Sunset", None, None),
    ("Gantry", "310 rpm", {"wght": 520, "ROND": 100, "wdth": 100}, None, "#1F3A5F", "#EAF2FF"),
    ("Pebble Sans", "Round", None, None, None, None),
    ("Platen Ribbon", "Ribbon", None, None, "#F1ECE0", "#1F1D1A"),
    ("Starry", "Stars", None, "Night", None, None),
]

# A picture font draws small inside its line, so its sample is set larger.
SCALE = {"Aviary Color": 1.9, "Aviary": 1.9, "Aviary Line": 1.9}


def ground_of(family: dict, palette: str) -> tuple:
    """(ground, ink) for one palette of a color font: its own ground, else the one the build found, else paper."""
    ground = GROUNDS.get(family["name"], {}).get(palette) or (family.get("grounds") or {}).get(palette) or PAPER_GROUND
    r, g, b = (int(ground[i:i + 2], 16) for i in (1, 3, 5))
    return ground, "#1B1A17" if 0.299 * r + 0.587 * g + 0.114 * b > 140 else "#F1EEE7"


# Pebble has no font.py: it is a remix made with one command.
REMIXES = {
    "pebble": {
        "title": "Pebble",
        "brief": "Round the corners of Inter, the open sans by Rasmus Andersson.",
        "command": 'whateverfont remix Inter.ttf --name "Pebble Sans" --round 46',
        "families": [{"name": "Pebble Sans", "description": "Inter with every sharp corner replaced by an arc. It keeps all of "
                      "Inter: Latin, Greek, Cyrillic, arrows, signs and 39 OpenType features. It stays under "
                      "Inter's Open Font License.", "sample": "Rounded in one command"}],
    },
}
AXIS_NAMES = {"wght": "Weight", "wdth": "Width", "slnt": "Slant", "ital": "Italic", "opsz": "Optical size",
              "FLAR": "Flare", "ROND": "Roundness"}


# --------------------------------------------------------------------------
# Reading the projects
# --------------------------------------------------------------------------

def _value(node, consts):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    if isinstance(node, ast.Dict):
        return [_value(k, consts) for k in node.keys]
    return None


def families_in(font_py: Path) -> list[dict]:
    """Name, description, sample and palette names of each Family(...) in a project's font.py."""
    tree = ast.parse(font_py.read_text(encoding="utf-8"))
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = node.value.value
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Family":
            kw = {k.arg: _value(k.value, consts) for k in node.keywords}
            if kw.get("name"):
                out.append({"name": kw["name"], "description": kw.get("description") or "",
                            "sample": kw.get("sample") or "", "palettes": kw.get("palettes") or [],
                            "line": node.lineno})
    return sorted(out, key=lambda f: f["line"])


def brief_of(project: Path) -> str:
    """The first paragraph under '## Brief' in BRIEF.md."""
    path = project / "BRIEF.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Brief\s*\n+(.+?)(?:\n\s*\n|\Z)", text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def _tables(data: bytes) -> dict:
    n = struct.unpack(">H", data[4:6])[0]
    tables = {}
    for i in range(n):
        tag, _, off, length = struct.unpack(">4sIII", data[12 + i * 16: 28 + i * 16])
        tables[tag.decode("latin-1")] = data[off: off + length]
    return tables


def _names(t: bytes) -> dict:
    _, count, start = struct.unpack(">HHH", t[:6])
    names = {}
    for i in range(count):
        pid, eid, lang, nid, length, off = struct.unpack(">6H", t[6 + i * 12: 18 + i * 12])
        raw = t[start + off: start + off + length]
        if pid == 3 and eid in (0, 1, 10) and nid not in names:
            names[nid] = raw.decode("utf-16-be", "replace")
        elif pid == 1 and eid == 0 and nid not in names:
            names[nid] = raw.decode("mac_roman", "replace")
    return names


def axes_of(tables: dict) -> list[dict]:
    t = tables.get("fvar")
    if not t:
        return []
    names = _names(tables["name"]) if "name" in tables else {}
    _, _, off, _, count, size = struct.unpack(">6H", t[:12])
    axes = []
    for i in range(count):
        rec = t[off + i * size: off + (i + 1) * size]
        tag, lo, default, hi, _, nid = struct.unpack(">4siiiHH", rec[:20])
        tag = tag.decode("latin-1")
        axes.append({"tag": tag, "name": names.get(nid) or AXIS_NAMES.get(tag, tag),
                     "min": lo / 65536, "default": default / 65536, "max": hi / 65536})
    return axes


def codepoints_of(tables: dict) -> list[int]:
    t = tables["cmap"]
    _, n = struct.unpack(">HH", t[:4])
    subtables = {}
    for i in range(n):
        pid, eid, off = struct.unpack(">HHI", t[4 + i * 8: 12 + i * 8])
        subtables[(pid, eid)] = off
    for key in ((3, 10), (0, 4), (3, 1), (0, 3), (3, 0)):
        if key not in subtables:
            continue
        s = t[subtables[key]:]
        fmt = struct.unpack(">H", s[:2])[0]
        if fmt == 12:
            groups = struct.unpack(">I", s[12:16])[0]
            cps = []
            for g in range(groups):
                start, end, _ = struct.unpack(">III", s[16 + g * 12: 28 + g * 12])
                cps.extend(range(start, end + 1))
            return cps
        if fmt == 4:
            seg = struct.unpack(">H", s[6:8])[0] // 2
            ends = struct.unpack(f">{seg}H", s[14: 14 + seg * 2])
            starts = struct.unpack(f">{seg}H", s[16 + seg * 2: 16 + seg * 4])
            cps = []
            for a, b in zip(starts, ends):
                if a != 0xFFFF:
                    cps.extend(range(a, b + 1))
            return cps
    return []


def font_files(project: Path, name: str) -> dict:
    """The web font (variable if there is one), its TTF, and the count of static styles."""
    stem = name.replace(" ", "")
    base = project / "fonts" / stem
    if not base.exists():
        base = project / "fonts"
    var = sorted((base / "variable").glob("*.woff2")) if (base / "variable").exists() else []
    statics = sorted(base.rglob(f"{stem}-*.woff2"))
    statics = [p for p in statics if "variable" not in p.parts]
    if var:
        web, ttf = var[0], var[0].with_suffix(".ttf")
    else:
        web = next((p for p in statics if p.stem.endswith("-Regular")), statics[0])
        ttf = next(iter(sorted(base.rglob(web.stem + ".ttf"))), None)
    return {"web": web, "ttf": ttf, "styles": len(statics), "variable": bool(var)}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load() -> list[dict]:
    projects = []
    for pid in PROJECTS:
        folder = EXAMPLES / pid
        if (folder / "font.py").exists():
            index = folder / "fonts" / "index.json"
            if index.exists():
                # written by `whateverfont build`: it knows the families however font.py declares them
                import json
                fams = [{"name": f["name"], "description": f["description"], "sample": f["sample"],
                         "palettes": f["palettes"], "grounds": f.get("grounds", {})}
                        for f in json.loads(index.read_text(encoding="utf-8"))["families"]]
            else:
                fams = families_in(folder / "font.py")
            title = pid.capitalize()
            heading = re.match(r"#\s*(.+)", (folder / "BRIEF.md").read_text(encoding="utf-8"))
            if heading:
                title = heading.group(1).strip()
            info = {"id": pid, "title": title, "brief": brief_of(folder), "command": None, "github": OWNER}
        else:
            r = REMIXES[pid]
            fams = [dict(f, palettes=[]) for f in r["families"]]
            info = {"id": pid, "title": r["title"], "brief": r["brief"], "command": r["command"], "github": OWNER}
        for f in fams:
            files = font_files(folder, f["name"])
            tables = _tables(files["ttf"].read_bytes()) if files["ttf"] else {}
            f.update(files, id=slug(f["name"]), axes=axes_of(tables),
                     codepoints=codepoints_of(tables) if tables else [])
        info["families"] = fams
        info["board"] = folder / "board.html" if (folder / "board.html").exists() else None
        info["license"] = folder / "OFL.txt" if (folder / "OFL.txt").exists() else EXAMPLES / "OFL.txt"
        projects.append(info)
    return projects


#: Fonts of other scripts, made with `whateverfont retrace`: letters traced from an open font and redrawn with a
#: family's pen. On the page each one is a second file of its Latin family, so the family's sample can be
#: Arabic or Hindi, and the browser loads the file only for text in that script.
OTHER_SCRIPTS = EXAMPLES / "retrace"


#: A family that has no font of its own in another script borrows the one of a sister family.
SAME_LETTERS = {"Last Bell": ["Last Bell Rounds"]}

#: How the Unicode names of a script's characters begin, by the language of the page. Simplified (zh) and
#: Traditional Chinese (zh-Hant) share their block of Unicode.
SCRIPT_NAMES = {"ar": ("ARABIC",), "hi": ("DEVANAGARI", "VEDIC"), "ko": ("HANGUL",),
                "ja": ("HIRAGANA", "KATAKANA", "CJK", "IDEOGRAPHIC", "FULLWIDTH", "HALFWIDTH"),
                "zh": ("CJK", "IDEOGRAPHIC", "FULLWIDTH"), "zh-Hant": ("CJK", "IDEOGRAPHIC", "FULLWIDTH")}
#: The languages whose text is set in squares: Chinese characters, kana or Hangul.
EAST_ASIAN = ("ja", "zh", "zh-Hant", "ko")


def in_script(cp: int, language: str) -> bool:
    """True if a code point belongs to the script of ``language``, and not to Latin text."""
    if language in EAST_ASIAN and 0x3000 <= cp <= 0x303F:        # the brackets and stops of East Asia
        return True
    return unicodedata.name(chr(cp), "").startswith(SCRIPT_NAMES.get(language, ()))


#: Small fonts for the page itself: a family that has no whole font of a script still shows its own words on
#: the page in that script. Each holds only the letters of those words (scripts/build_page_fonts.py).
PAGE_FONTS = SITE / "page-fonts"


def load_parts(projects: list, folder: Path = OTHER_SCRIPTS, whole: bool = True, slices: bool = True) -> list:
    """Give each Latin family its fonts of other scripts, as ``f["parts"]``. Returns every part.

    ``whole`` is False for the page's own small fonts: a family takes one only for a language in which it has
    no whole font, and the page does not say that the family sets that script."""
    index = folder / "fonts" / "index.json" if whole else folder / "index.json"
    if not index.is_file():
        return []
    latin = {f["name"]: f for p in projects for f in p["families"]}
    listed = PAGE_FONTS / "slices.json"
    sliced = {s["part"]: s for s in json.loads(listed.read_text(encoding="utf-8"))["slices"]} if listed.is_file() else {}
    parts = []
    for c in json.loads(index.read_text(encoding="utf-8"))["families"]:
        style = next(iter(c["woff2"]))
        ttf = folder / c["ttf"][style] if c.get("ttf") else None
        if ttf is not None and not ttf.is_file():
            ttf = None                  # a large font keeps only its web file in the repository
        # the script itself only: Latin letters, figures, dashes and quotes stay with the family's own font,
        # so a reader of English never loads this file
        all_cps = code_points(c["codepoints"]) if c.get("codepoints") else codepoints_of(_tables(ttf.read_bytes()))
        cps = [cp for cp in all_cps if in_script(cp, c["language"])]
        # "codepoints" are the letters that this file gives the page. "listed" are all the letters of the font:
        # the table of a font's page lists them, also where the font is cut in two files below.
        part = {"name": c["name"], "id": slug(c["name"]), "language": c["language"], "script": c["script"],
                "source": c["source"], "web": folder / c["woff2"][style], "ttf": ttf, "codepoints": cps,
                "listed": cps, "pen": c["pen"], "project": c.get("pen_project"), "folder": folder, "whole": whole}
        mine = [part]
        cut = sliced.get(c["name"]) if whole and slices else None
        if cut and (PAGE_FONTS / cut["file"]).is_file():
            # A large font is in two files: a small one with the letters of the page's own words, and the whole
            # font for every other letter. A reader loads the whole font only after typing other words.
            small = set(code_points(cut["codepoints"]))
            mine.append(dict(part, id=part["id"] + "-page", web=PAGE_FONTS / cut["file"], ttf=None, whole=False,
                             codepoints=[cp for cp in cps if cp in small]))
            part["codepoints"] = [cp for cp in cps if cp not in small]
        used = False
        for name in [c["pen"]] + SAME_LETTERS.get(c["pen"], []):
            if name in latin and not any(q["language"] == part["language"] and q["folder"] != folder
                                         for q in latin[name].get("parts", [])):
                latin[name].setdefault("parts", []).extend(mine)
                used = True
        if used:
            parts.extend(mine)
    return parts


def code_points(listed) -> list:
    """The code points that an index lists: a list of numbers, or ranges such as "20 A0 3041-3096"."""
    if not isinstance(listed, str):
        return list(listed)
    out = []
    for run in listed.split():
        a, _, b = run.partition("-")
        out.extend(range(int(a, 16), int(b or a, 16) + 1))
    return out


def unicode_range(cps: list, gap: int = 4, never=frozenset()) -> str:
    """The CSS unicode-range of a set of code points. Small gaps are bridged to keep the list short.

    A gap is not bridged over a code point of ``never``: those belong to another file of the same font, and
    a range that covered them would make the browser load this file for them too."""
    runs = []
    for cp in sorted(set(cps)):
        if runs and cp - runs[-1][1] <= gap and not any(q in never for q in range(runs[-1][1] + 1, cp)):
            runs[-1][1] = cp
        else:
            runs.append([cp, cp])
    return ", ".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in runs)


def load_library() -> list[dict]:
    """The entries of the library that have built fonts: one dict each, like a project."""
    import json
    entries = []
    for folder in sorted(LIBRARY.iterdir()) if LIBRARY.is_dir() else []:
        index = folder / "fonts" / "index.json"
        credit = folder / "entry.json"
        if not (index.is_file() and credit.is_file()):
            continue                         # not built yet: the build after a merge adds the fonts
        entry = json.loads(credit.read_text(encoding="utf-8"))
        fams = [{"name": f["name"], "description": f["description"], "sample": f["sample"],
                 "palettes": f["palettes"], "grounds": f.get("grounds", {})}
                for f in json.loads(index.read_text(encoding="utf-8"))["families"]]
        for f in fams:
            files = font_files(folder, f["name"])
            tables = _tables(files["ttf"].read_bytes()) if files["ttf"] else {}
            f.update(files, id="lib-" + slug(f["name"]), axes=axes_of(tables),
                     codepoints=codepoints_of(tables) if tables else [])
            f["copyright"] = _names(tables["name"]).get(0, "") if tables.get("name") else ""
        title = folder.name
        heading = re.match(r"#\s*(.+)", (folder / "BRIEF.md").read_text(encoding="utf-8")) if (folder / "BRIEF.md").exists() else None
        if heading:
            title = heading.group(1).strip()
        entries.append({"id": folder.name, "title": title, "github": entry["github"], "prompt": entry["prompt"],
                        "agent": entry.get("agent", ""), "moods": entry.get("moods", ""),
                        "word": entry.get("word", ""), "families": fams})
    return entries


# --------------------------------------------------------------------------
# Writing the page
# --------------------------------------------------------------------------

#: The languages of the page: code, the language's own name, and "rtl" where the script runs right to left.
#: English is in the pages themselves. Every other language is one file, site/i18n/CODE.json, and it is
#: in the menu only when that file exists.
LANGS = [("en", "English", ""), ("es", "Español", ""), ("fr", "Français", ""), ("de", "Deutsch", ""),
         ("gl", "Galego", ""), ("br", "Brezhoneg", ""), ("vi", "Tiếng Việt", ""), ("zh", "简体中文", ""),
         ("zh-Hant", "繁體中文", ""), ("ja", "日本語", ""), ("ko", "한국어", ""), ("ar", "العربية", "rtl"),
         ("hi", "हिन्दी", "")]
#: The label of the menu on a phone, where the name does not fit: the code, or this. Both Chinese pages
#: would read "ZH".
SHORT = {"zh": "简体", "zh-Hant": "繁體"}


def lang_rule(code: str) -> str:
    """A selector for the page in language ``code`` and no other.

    ``:lang(zh)`` also matches a page in zh-Hant, so the rule of zh leaves out every longer code that
    starts with it. A Traditional page must never name a Simplified font, nor the reverse."""
    longer = [other for other, _, _ in LANGS if other.lower().startswith(code.lower() + "-")]
    return f":root:lang({code})" + "".join(f":not(:lang({other}))" for other in longer)
I18N = SITE / "i18n"
GLOBE = ('<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" '
         'stroke-width="1.4"><circle cx="10" cy="10" r="7.6"/><ellipse cx="10" cy="10" rx="3.5" ry="7.6"/>'
         '<path d="M2.4 10h15.2"/></svg>')


#: The sample text of the fonts: key -> English. Fonts with the same sample share one key, so a translator
#: writes each sample once.
SAMPLES: dict = {}


def sample_key(f: dict) -> str:
    """The key of a family's sample text in the translations."""
    for key, text in SAMPLES.items():
        if text == f["sample"]:
            return key
    key = f"sample.{f['id']}"
    SAMPLES[key] = f["sample"]
    return key


def translations() -> dict:
    """Every translation that is there: code -> its texts."""
    if not hasattr(translations, "read"):
        translations.read = {code: json.loads((I18N / f"{code}.json").read_text(encoding="utf-8"))
                             for code, _, _ in LANGS[1:] if (I18N / f"{code}.json").is_file()}
    return translations.read


def text_langs(fams: list, key: str) -> list:
    """The languages in which every font of ``fams`` can set the translation of ``key``.

    Text that shows a font never falls back to another font. Where a letter is missing, the text stays in
    English. A font may use the letters of its part for that language (see ``load_parts``).
    """
    out = []
    for code, words in translations().items():
        text = re.sub(r"<[^>]+>", "", words.get(key) or "")
        if not text:
            continue
        for f in fams:
            have = set(f["codepoints"]) | {cp for part in f.get("parts", []) if part["language"] == code
                                           for cp in part["codepoints"]}
            if not all(ord(c) in have or c.isspace() for c in unicodedata.normalize("NFC", text)):
                break
        else:
            out.append(code)
    return out


def sample_langs(f: dict) -> list:
    """The languages in which this font can set its translated sample."""
    return text_langs([f], sample_key(f))


#: Words that the page sets in a font, apart from the samples (the poster, the wall, the footer, the demo),
#: and the requests of the poster: key -> English.
FONT_TEXTS: dict = {}
POSTER = "WhateverFont<br>You Want."


def font_text(fams, key: str, english: str) -> str:
    """The attributes of an element whose words are set in a font and follow the reader's language.

    ``fams`` is the family, or the families that set the same words on top of each other."""
    fams = fams if isinstance(fams, list) else [fams]
    FONT_TEXTS[key] = english
    return (f' data-font-text="{key}" data-english="{e(english)}" data-langs="{" ".join(text_langs(fams, key))}"')


def said(key: str, text: str, n=None) -> str:
    """A piece of page text that the build writes, with its key (and its number) for the translations."""
    number = f' data-n="{n}"' if n is not None else ""
    return f'<span data-i18n="{key}"{number}>{e(text)}</span>'


CHEVRON = ('<svg class="lang-chevron" viewBox="0 0 12 12" width="10" height="10" aria-hidden="true" fill="none" '
           'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 4.5 6 8l3.5-3.5"/></svg>')
CHECK = ('<svg viewBox="0 0 14 14" width="13" height="13" aria-hidden="true" fill="none" stroke="currentColor" '
         'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 7.5 5.6 10.5 11.5 3.8"/></svg>')


def langs_menu() -> str:
    """The language menu: a button, and a list that opens under it. The browser's own menu would open over
    the header and run off the top of the screen, so the list is the page's own. The select holds the
    choice for the script and is never shown."""
    have = [(code, name, way) for code, name, way in LANGS if code == "en" or (I18N / f"{code}.json").is_file()]
    if len(have) < 2:
        return ""
    options = "".join('<option value="{}" lang="{}"{}{}>{}</option>'.format(
                          code, code, f' data-dir="{way}"' if way else "",
                          f' data-short="{e(SHORT[code])}"' if code in SHORT else "", e(name))
                      for code, name, way in have)
    rows = "".join(f'<button type="button" class="lang-option" role="option" data-code="{code}" lang="{code}" '
                   f'aria-selected="{str(code == "en").lower()}"><span>{e(name)}</span>{CHECK}</button>'
                   for code, name, way in have)
    return (f'<div class="lang" id="lang-box">'
            f'<button type="button" class="lang-button" id="lang-button" aria-haspopup="listbox" aria-expanded="false" '
            f'aria-controls="lang-list" aria-label="Language">{GLOBE}'
            f'<span class="lang-name" id="lang-name" data-code="EN">English</span>{CHEVRON}</button>'
            f'<div class="lang-list" id="lang-list" role="listbox" aria-label="Language" dir="ltr" hidden>{rows}</div>'
            f'<select id="lang" hidden aria-hidden="true" tabindex="-1" autocomplete="off">{options}</select></div>')


class _Texts(HTMLParser):
    """Collects the inner HTML of every element with data-i18n, and the attributes of data-i18n-attr."""
    VOID = {"br", "img", "input", "meta", "link", "hr", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.found, self.open = [], []       # open: [key, n, depth, parts]

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for item in self.open:
            item[3].append(self.get_starttag_text())
            if tag not in self.VOID:
                item[2] += 1
        if "data-i18n-attr" in a:
            name, key = a["data-i18n-attr"].split(":")
            self.found.append((key, None, a[name]))
        if "data-i18n" in a and tag not in self.VOID:
            self.open.append([a["data-i18n"], a.get("data-n"), 0, []])

    def handle_endtag(self, tag):
        for item in list(self.open):
            if item[2] == 0:
                self.open.remove(item)
                self.found.append((item[0], item[1], "".join(item[3])))
            else:
                item[2] -= 1
                item[3].append(f"</{tag}>")

    def handle_data(self, data):
        for item in self.open:
            item[3].append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def english(pages: list) -> dict:
    """Every keyed text of the built pages: key -> English, with {n} where a number goes."""
    texts = {}
    for page in pages:
        reader = _Texts()
        reader.feed(page)
        for key, n, text in reader.found:
            text = " ".join(text.split())
            if n is not None and n in text:
                text = text.replace(n, "{n}", 1)
            if texts.setdefault(key, text) != text:
                raise SystemExit(f"{key} has two English texts: {texts[key]!r} and {text!r}")
    for key, text in list(SAMPLES.items()) + list(FONT_TEXTS.items()):
        if text.strip():
            texts[key] = text
    # the names of the groups of a character table: the page's script writes them for the fonts of other scripts
    for name, key in GROUP_KEYS.items():
        texts.setdefault(key, name)
    return dict(sorted(texts.items()))


def _tags(text: str) -> list:
    return sorted(re.findall(r"<[^>]+>", text))


def languages(out: Path, pages: list) -> None:
    """Write the English texts of the built pages, check every translation against them, and copy the
    translations."""
    en = english(pages)
    body = json.dumps(en, ensure_ascii=False, indent=2) + "\n"
    I18N.mkdir(exist_ok=True)
    source = I18N / "en.json"
    if not source.is_file() or source.read_text(encoding="utf-8") != body:
        source.write_text(body, encoding="utf-8")       # what a translator starts from
    (out / "i18n").mkdir()
    wrong = []
    for code, name, _ in LANGS[1:]:
        path = I18N / f"{code}.json"
        if not path.is_file():
            continue
        words = json.loads(path.read_text(encoding="utf-8"))
        for key, text in words.items():
            if key not in en:
                wrong.append(f"{code}: {key} is not a text of the page")
            elif not isinstance(text, str) or not text.strip():
                wrong.append(f"{code}: {key} is empty")
            elif _tags(text) != _tags(en[key]):
                wrong.append(f"{code}: {key} must keep the tags of the English text exactly: {_tags(en[key])}")
            elif ("{n}" in text) != ("{n}" in en[key]):
                wrong.append(f"{code}: {key} must keep the number {{n}}")
        # words that are set in a font are translated only where it makes sense, so a missing one is no fault
        missing = [k for k in en if k not in words and not k.startswith(("sample.", "word.", "block.", "demo.", "poster."))]
        if missing:
            print(f"{name} ({code}): {len(missing)} of {len(en)} texts stay in English: {', '.join(missing[:6])}"
                  f"{' …' if len(missing) > 6 else ''}")
        (out / "i18n" / f"{code}.json").write_text(json.dumps(words, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if wrong:
        raise SystemExit("translations:\n  " + "\n  ".join(wrong))


def e(text) -> str:
    return html.escape(str(text), quote=True)


def _num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


def faces_css(projects) -> str:
    out, by_language = [], {}
    for p in projects:
        for f in p["families"]:
            rules = [f'font-family: "ff-{f["id"]}"', f'src: url("fonts/{f["id"]}.woff2") format("woff2")',
                     "font-display: swap"]
            wght = next((a for a in f["axes"] if a["tag"] == "wght"), None)
            if wght:
                rules.append(f'font-weight: {_num(wght["min"])} {_num(wght["max"])}')
            cut = latin_slice(f)
            if cut:
                # a large font is in two files: the letters of the page's own words, and all the others
                small = set(cut[1])
                rest = [cp for cp in f["codepoints"] if cp not in small]
                first = [rules[0], f'src: url("fonts/{f["id"]}-basic.woff2") format("woff2")'] + rules[2:]
                out.append("@font-face { " + "; ".join(first + [f"unicode-range: {unicode_range(sorted(small), 0)}"]) + "; }")
                out.append("@font-face { " + "; ".join(rules + [f"unicode-range: {unicode_range(rest, 4, small)}"]) + "; }")
            else:
                out.append("@font-face { " + "; ".join(rules) + "; }")
            # A font of another script has a name of its own for each language: "ff-last-bell-ja". Japanese and
            # Chinese share their characters in Unicode, so one name for both would load both fonts and draw
            # Japanese words with Chinese letter forms. The page of a language names only its own fonts.
            names = [f'"ff-{f["id"]}"']
            for part in f.get("parts", []):
                name = f'"ff-{f["id"]}-{part["language"]}"'
                # the other files of this font in this language keep their own characters
                others = frozenset(cp for q in f["parts"] if q is not part and q["language"] == part["language"]
                                   for cp in q["codepoints"])
                wide = 48 if len(part["codepoints"]) > 1500 else 4
                more = [f"font-family: {name}", f'src: url("fonts/{part["id"]}.woff2") format("woff2")',
                        "font-display: swap", f'unicode-range: {unicode_range(part["codepoints"], wide, others)}']
                out.append("@font-face { " + "; ".join(more) + "; }")
                if name not in names:
                    names.append(name)
                    by_language.setdefault(part["language"], []).append(f'--p-{f["id"]}: {name};')
            for k in range(len(f["palettes"])):
                out.append(f'@font-palette-values --ff-{f["id"]}-{k} {{ font-family: {", ".join(names)}; base-palette: {k}; }}')
            if f["name"] == "Last Bell Snow" and len(names) > 1:
                # the demo lays the snow of this font over other letters: the letter color is made clear
                out.append(f'@font-palette-values --snow-only {{ font-family: {", ".join(names[1:])}; base-palette: 0; '
                           "override-colors: 0 transparent; }")
    for language, rules in by_language.items():
        out.append(f'{lang_rule(language)} {{ {" ".join(rules)} }}')
    return "\n".join(out)


def latin_slice(f: dict):
    """(file, code points) of the slice of a large Latin font, or None (see scripts/build_page_slices.py)."""
    if not hasattr(latin_slice, "listed"):
        listed = PAGE_FONTS / "slices.json"
        rows = json.loads(listed.read_text(encoding="utf-8")).get("latin", []) if listed.is_file() else []
        latin_slice.listed = {row["family"]: row for row in rows}
    row = latin_slice.listed.get(f["name"])
    if not row or not (PAGE_FONTS / row["file"]).is_file():
        return None
    return PAGE_FONTS / row["file"], code_points(row["codepoints"])


def stack(f: dict) -> str:
    """The font-family value for words in the family ``f``: its own font, then its font for the script of the
    page's language (a custom property that only that language defines), then the fallback."""
    own = f'"ff-{f["id"]}"'
    return f'{own}, var(--p-{f["id"]}, {own}), var(--fallback)' if f.get("parts") else f"{own}, var(--fallback)"


def default_fvs(f: dict) -> str:
    """The default of every axis. Without it, a browser sets wght from font-weight and wdth from font-stretch."""
    return ", ".join(f'"{a["tag"]}" {_num(a["default"])}' for a in f["axes"])


def chars(f: dict) -> int:
    return len(set(f["codepoints"]))


def quoted(text: str) -> str:
    """Curly quotes. A brief that quotes the person keeps its own marks; any other gets a pair around it."""
    if '"' not in text:
        return f"“{text}”"
    out, opening = [], True
    for ch in text:
        if ch == '"':
            out.append("“" if opening else "”")
            opening = not opening
        else:
            out.append(ch)
    return "".join(out)


def _size(path: Path) -> str:
    n = path.stat().st_size
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{round(n / 1e3)} KB"


def specimen(f: dict) -> str:
    meta = []
    if f["variable"]:
        meta.append(said("meta.variable", "Variable"))
    if f["styles"] == 1:
        meta.append(said("meta.style", "1 style"))
    elif f["styles"]:
        meta.append(said("meta.styles", f'{f["styles"]} styles', f["styles"]))
    if f["palettes"]:
        meta.append(said("meta.color", f'Color, {len(f["palettes"])} palettes', len(f["palettes"])))
    if f["codepoints"]:
        meta.append(said("meta.chars", f'{chars(f)} characters', chars(f)))
    controls = []
    for a in f["axes"]:
        step = "1" if a["max"] - a["min"] > 4 else "0.1"
        controls.append(
            f'<label class="axis"><span class="axis-name">{e(a["name"])}</span>'
            f'<input type="range" min="{_num(a["min"])}" max="{_num(a["max"])}" step="{step}" '
            f'value="{_num(a["default"])}" data-tag="{e(a["tag"])}" data-default="{_num(a["default"])}">'
            f'<output>{_num(a["default"])}</output></label>')
    if f["palettes"]:
        # every palette brings its own ground and ink, so a color sample reads in both themes
        chips = "".join(
            '<button type="button" data-palette="--ff-{id}-{k}" data-ground="{g}" data-ink="{i}" aria-pressed="{on}">{n}</button>'
            .format(id=f["id"], k=k, g=ground_of(f, n)[0], i=ground_of(f, n)[1], on=str(k == 0).lower(), n=e(n))
            for k, n in enumerate(f["palettes"]))
        controls.append(f'<div class="chips" role="group" aria-label="Palette">{chips}</div>')
    style = f'font-family: {stack(f)};'
    if f["name"] in SCALE:
        style += f' font-size: calc(var(--sample) * {SCALE[f["name"]]});'
    if f["axes"]:
        style += f' font-variation-settings: {default_fvs(f)};'
    if f["palettes"]:
        ground, ink = ground_of(f, f["palettes"][0])
        style += f' font-palette: --ff-{f["id"]}-0; background: {ground}; color: {ink};'
    return f"""
<article class="spec" id="{e(f["id"])}">
  <div class="spec-head">
    <h3>{e(f["name"])}</h3>
    <p class="spec-meta">{"".join(meta)}</p>
  </div>
  <p class="spec-desc">{e(f["description"])}</p>{also(f)}
  <div class="sample" contenteditable="true" spellcheck="false" aria-label="{e(f["name"])} sample, editable"
       data-default="{e(f["sample"])}" data-english="{e(f["sample"])}" data-sample="{sample_key(f)}"
       data-sample-langs="{" ".join(sample_langs(f))}" style='{style}'>{e(f["sample"])}</div>
  {'<div class="controls">' + "".join(controls) + "</div>" if controls else ""}
</article>"""


def also(f: dict) -> str:
    """One line under a family's description: its other scripts, and the open font their letters are traced from."""
    parts = [part for part in f.get("parts", []) if part["whole"]]
    if not parts:
        return ""
    items = ", ".join(f'{e(part["script"])} <span class="muted">({e(part["source"])})</span>' for part in parts)
    return f'\n  <p class="spec-also">{said("meta.also", "Also sets")} {items}</p>'


def project_block(p: dict, downloads: dict) -> str:
    links = []
    if p["board"]:
        links.append(f'<a href="boards/{p["id"]}.html" data-i18n="link.board">Open the review board</a>')
    z = downloads[p["id"]]
    links.append(f'<a href="downloads/{z.name}" download>{said("link.download", "Download the fonts")} '
                 f'<span class="muted" dir="ltr">({_size(z)})</span></a>')
    links.append(f'<a href="{REPO}/tree/main/examples/{p["id"]}" data-i18n="link.source">Source and brief</a>')
    command = f'<pre class="cmd"><code>{e(p["command"])}</code></pre>' if p["command"] else ""
    return f"""
<section class="project" id="project-{p["id"]}" aria-labelledby="h-{p["id"]}">
  <div class="project-side">
    <h2 class="project-title" id="h-{p["id"]}">{e(p["title"])}</h2>
    <blockquote class="brief" lang="en" dir="ltr">{e(quoted(p["brief"]).replace("'", "’"))}</blockquote>
    {command}
    <ul class="links">{"".join(f"<li>{x}</li>" for x in links)}</ul>
  </div>
  <div class="project-fonts" lang="en" dir="ltr">{"".join(specimen(f) for f in p["families"])}</div>
</section>"""


def _fvs(settings: dict | None) -> str:
    return ", ".join(f'"{k}" {v}' for k, v in settings.items()) if settings else ""


def _family(projects: list, name: str) -> dict | None:
    return next((f for p in projects for f in p["families"] if f["name"] == name), None)


def hero(books: list) -> list:
    """The poster's slides, for the script on the page: one for each font of the library that the list of the
    poster names. A font that is not built is left out. A slide carries the person who made the font."""
    slides = []
    for name, palette, ground, ink, ask, settings in HERO:
        home = next((p for p in books if any(f["name"] == name for f in p["families"])), None)
        if home is None:
            continue
        f = next(f for f in home["families"] if f["name"] == name)
        k = f["palettes"].index(palette) if palette in f["palettes"] else None
        if ground is None and k is not None:
            ground, ink = ground_of(f, palette)          # the ground that the palette was drawn for
        FONT_TEXTS["poster.text"] = POSTER
        FONT_TEXTS[f"ask.{f['id']}"] = ask
        slides.append({"face": f"ff-{f['id']}", "palette": f"--ff-{f['id']}-{k}" if k is not None else "",
                       "ground": ground, "ink": ink, "ask": ask, "askKey": f"ask.{f['id']}", "name": name,
                       "by": f"@{home['github']}" if home.get("github") else "",
                       "fvs": _fvs(settings), "langs": text_langs([f], "poster.text"),
                       "parts": {part["language"]: f"ff-{f['id']}-{part['language']}" for part in f.get("parts", [])}})
    return slides


def _dressed(f: dict, settings, palette, ground, ink) -> tuple:
    """(style of the word, ground, ink) for one word in a font on a ground that suits it."""
    style = f'font-family: {stack(f)};'
    if settings:
        style += f" font-variation-settings: {_fvs(settings)};"
    elif f["axes"]:
        style += f" font-variation-settings: {default_fvs(f)};"
    if f["name"] in SCALE:
        style += f" --k: {SCALE[f['name']]};"
    if f["palettes"]:
        k = f["palettes"].index(palette) if palette in f["palettes"] else 0
        style += f' font-palette: --ff-{f["id"]}-{k};'
        own = ground_of(f, f["palettes"][k])
        ground, ink = ground or own[0], ink or own[1]
    return style, ground, ink


def drops(projects: list) -> str:
    """The blocks that fall in the footer: one word in each font."""
    out = []
    for name, word, settings, palette, ground, ink in DROPS:
        f = _family(projects, name)
        if f is None:
            continue
        style, ground, ink = _dressed(f, settings, palette, ground, ink)
        style = style.replace(f"--k: {SCALE.get(name)};", "--k: 1.25;")       # a block of birds is big enough at this size
        if ground:
            style += f" background: {ground}; color: {ink};"
        key = f"word.{f['id']}" if (name, word) in [(w[0], w[1]) for w in WALL] else f"block.{f['id']}"
        out.append(f'<span class="drop{"" if ground else " plain"}" style=\'{style}\'{font_text(f, key, word)}>{e(word)}</span>')
    return "".join(out)


def tile_name(p: dict) -> str:
    """The foot of a font's tile: its name, and under it the person who added the font, when that is someone
    other than the owner of the repository."""
    theirs = p.get("github") and p["github"].lower() != OWNER.lower()
    by = (f'<span class="tile-by">{said("lib.by", "by")} <span dir="ltr">@{e(p["github"])}</span></span>'
          if theirs else "")
    return f'<span class="tile-name"><span class="tile-title">{e(p["title"])}</span>{by}</span>'


def wall(books: list) -> str:
    """The first page's wall: one word in each font of the library, on a ground that suits it. A wide tile
    shows the font's sample line. A tile leads to the font's page."""
    place = {page: k for k, page in enumerate(WALL_ORDER)}
    tiles = []
    for p in sorted(books, key=lambda p: place.get(p["page"], len(place))):
        f, word, settings, palette, ground, ink, key = tile_of(p)
        kind = ""
        if p["page"] in WALL_WIDE and f["sample"]:
            word, key = f["sample"], sample_key(f)
            kind = " wide" + (" " + WALL_WIDE[p["page"]] if WALL_WIDE[p["page"]] else "")
        style, ground, ink = _dressed(f, settings, palette, ground, ink)
        dress = f' style="background: {ground}; color: {ink}"' if ground else ""
        tiles.append(f'<a class="tile{kind}{"" if ground else " plain"}" href="library/{p["page"]}/"{dress}>'
                     f'<span class="tile-word" style=\'{style}\'{font_text(f, key, word)}>{e(word)}</span>'
                     f'{tile_name(p)}</a>')
    return "".join(tiles)


def dials(books: list) -> str:
    """The live demo under "How it works": a line in the font of DIALS, and a slider for each of its axes.

    A row shows the engine's name for the number and its value, read from the font's design file: the
    numbers at the ends of each axis, and the number of the base where the axis is at rest."""
    home = next((p for p in books if p["page"] == DIALS), None)
    source = LIBRARY / DIALS / "font.py"
    if home is None or not source.is_file():
        return ""
    f = home["families"][0]
    tree = ast.parse(source.read_text(encoding="utf-8"))
    base, moves = dict(DIAL_START), {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", None) == "preset":
            base.update({k.arg: ast.literal_eval(k.value) for k in node.keywords})
            preset_name = ast.literal_eval(node.args[0])
        if getattr(node.func, "id", None) == "Axis":
            tag, _, low, rest, high, stops = (ast.literal_eval(a) for a in node.args[:6])
            moves[tag] = (stops, low, rest, high)
    rows = {}
    for a in f["axes"]:
        stops, low, rest, high = moves[a["tag"]]
        number = next(iter(next(iter(stops.values()))))          # the first number that the axis moves
        at = lambda stop: stops[stop][number] if stop in stops else base[number]
        ends = (at(low), base[number], at(high))
        span = (a["min"], a["default"], a["max"])
        # An axis that rests at its far end (slant: -14 to 0) is turned over, so every slider rests on the
        # near side and its number grows to the far side. The script gives the font the axis' own sign back.
        turned = a["default"] == a["max"] > a["min"]
        if turned:
            ends, span = ends[::-1], tuple(0 - v for v in span[::-1])
        places = 0 if all(float(v).is_integer() for v in ends) and max(ends) - min(ends) > 2 else 2
        rows[number] = (f'<label class="dial"><span class="dial-name">{number}</span>'
                        f'<input type="range" data-tag="{a["tag"]}" min="{_num(span[0])}" max="{_num(span[2])}" '
                        f'step="any" value="{_num(span[1])}" data-default="{_num(span[1])}"'
                        f'{" data-turned" if turned else ""} '
                        f'data-ends="{" ".join(_num(v) for v in ends)}" data-places="{places}" aria-label="{number}">'
                        f'<output>{ends[1]:.{places}f}</output></label>')
    order = [n for n in DIAL_ORDER if n in rows] + [n for n in rows if n not in DIAL_ORDER]
    # The sliders move the letters of the font itself. Its letters of another script are traced, in a file of
    # their own that has no axes, so the line follows a language only where the font itself has the letters.
    own = dict(f, parts=[])
    style = f'font-family: {stack(own)}; font-variation-settings: {default_fvs(f)};'
    return (f'<figure class="dials" id="dials"><div class="dials-stage" dir="ltr" lang="en">'
            f'<p class="dials-line" id="dials-line" style=\'{style}\'{font_text(own, sample_key(f), f["sample"])}>{e(f["sample"])}</p></div>'
            f'<div class="dials-rows" dir="ltr"><p class="dials-code">preset(&quot;{e(preset_name)}&quot;,</p>'
            + "".join(rows[n] for n in order) +
            f'<p class="dials-code dials-end">)<button type="button" id="dials-reset" class="dials-reset" '
            f'data-i18n="tester.reset" hidden>Reset</button></p></div></figure>')


def entry_block(p: dict, downloads: dict) -> str:
    """One font of the library, with the name of the person who added it."""
    user = e(p["github"])
    z = downloads[p["id"]]
    links = [f'<a href="downloads/{z.name}" download>{said("link.download", "Download the fonts")} '
             f'<span class="muted" dir="ltr">({_size(z)})</span></a>',
             f'<a href="{REPO}/tree/main/library/{p["id"]}" data-i18n="link.source">Source and brief</a>']
    agent = f' {said("lib.with", "with")} {e(p["agent"])}' if p["agent"] else ""
    return f"""
<section class="project" id="font-{p["id"]}" aria-labelledby="h-{p["id"]}">
  <div class="project-side">
    <h2 class="project-title" id="h-{p["id"]}">{e(p["title"])}</h2>
    <p class="credit"><img src="https://github.com/{user}.png?size=56" alt="" width="28" height="28" loading="lazy">
    <span>{said("lib.by", "by")} <a href="https://github.com/{user}" dir="ltr">@{user}</a>{agent}</span></p>
    <blockquote class="brief" lang="en" dir="ltr">{e(quoted(p["prompt"]).replace("'", "’"))}</blockquote>
    <ul class="links">{"".join(f"<li>{x}</li>" for x in links)}</ul>
  </div>
  <div class="project-fonts" lang="en" dir="ltr">{"".join(specimen(f) for f in p["families"])}</div>
</section>"""


UP = ('<svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true" fill="currentColor">'
      '<path d="M6 1.6 11 8.4H7.6V10.6H4.4V8.4H1Z"/></svg>')
EYE = ('<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" '
       'stroke-width="1.5" stroke-linejoin="round"><path d="M1.3 8S3.9 3.5 8 3.5 14.7 8 14.7 8 12.1 12.5 8 12.5 1.3 8 1.3 8Z"/>'
       '<circle cx="8" cy="8" r="2.1"/></svg>')
SEARCH = SITE / "search"


def tile_of(p: dict) -> tuple:
    """(family, word, axis settings, palette, ground, ink, key of the word) for the one tile of a font: its
    word in the list of the wall or of the footer's blocks, the word of its entry, or the start of its sample."""
    names = {f["name"]: f for f in p["families"]}
    on_wall = {(row[0], row[1]) for row in WALL}
    for name, word, settings, palette, ground, ink in DROPS:
        if name in names:
            f = names[name]
            return f, word, settings, palette, ground, ink, ("word." if (name, word) in on_wall else "block.") + f["id"]
    f = p["families"][0]
    # a font that someone added names its word in entry.json, or shows the start of its sample
    return f, p.get("word") or " ".join(f["sample"].split()[:2]), None, None, None, None, f"word.{f['id']}"


def book(p: dict) -> str:
    """One font on the shelf: its tile, which leads to its page, with its views and its vote."""
    f, word, settings, palette, ground, ink, key = tile_of(p)
    style, ground, ink = _dressed(f, settings, palette, ground, ink)
    look = f' style="--tile-ground: {ground}; --tile-ink: {ink}"' if ground else ""
    follow = font_text(f, key, word)
    name, page = e(p["title"]), p["page"]
    return (f'<article class="book" data-id="{page}" data-name="{name}"{look}>'
            f'<a class="tile" href="library/{page}/"><span class="tile-word" style=\'{style}\'{follow}>{e(word)}</span>'
            f'{tile_name(p)}</a><p class="book-why"></p>'
            f'<div class="book-stats"><span class="views" data-id="{page}" hidden>{EYE}<span class="views-n"></span></span>'
            f'<button type="button" class="vote" data-id="{page}" aria-pressed="false" aria-label="Vote for {name}" hidden>'
            f'{UP}<span class="vote-n"></span></button></div></article>')


def mood_words(p: dict, moods: dict) -> tuple:
    """(the mood words that someone chose for a font, the other text about it), for the search."""
    chosen = moods.get(p["page"]) or p.get("moods") or ""
    more = " ".join([p["title"], p.get("brief") or p.get("prompt") or ""]
                    + [f'{f["name"]} {f["description"]}' for f in p["families"]])
    return chosen, more


class _Vectors:
    """The word vectors of the search (site/search, see scripts/build_search.py), read without a package."""

    def __init__(self, folder: Path):
        import array
        self.words = {w: i for i, w in enumerate((folder / "vocab.txt").read_text(encoding="utf-8").split())}
        self.data = array.array("b", (folder / "vectors.bin").read_bytes())

    def near(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        i, j = self.words.get(a), self.words.get(b)
        if i is None or j is None:
            return 0.0
        d = self.data
        return sum(d[i * 50 + k] * d[j * 50 + k] for k in range(50)) / 16129

    def alike(self, a: list, b: list) -> float:
        """How alike two lists of words are: each word takes its best match in the other list."""
        if not a or not b:
            return 0.0
        return (sum(max(self.near(w, v) for v in b) for w in a) / len(a)
                + sum(max(self.near(w, v) for v in a) for w in b) / len(b)) / 2


def _filled(page: str, fills: dict, where: str) -> str:
    for key, value in fills.items():
        page = page.replace(f"<!--@{key}-->", value).replace(f"@{key}@", value)
    left = re.findall(r"<!--@[A-Z]+-->|@[A-Z]+@", page)
    if left:
        raise SystemExit(f"unfilled placeholders in {where}: {left}")
    return page


def _once(families: list) -> list:
    """The families once each, as one project for ``faces_css``."""
    seen = {}
    for f in families:
        seen.setdefault(f["id"], f)
    return [{"families": list(seen.values())}]


def build_library(out: Path, projects: list, downloads: dict) -> list:
    """Write the library: ``library/index.html``, a shelf of every font with a search by mood, and
    ``library/<font>/index.html``, a page for each font. Returns the pages, the shelf first."""
    entries = load_library()
    # a font of the library shows its sample in other scripts too, through its small page fonts
    for part in load_parts(entries, PAGE_FONTS, whole=False):
        shutil.copyfile(part["web"], out / "fonts" / f"{part['id']}.woff2")
    license_body = (EXAMPLES / "OFL.txt").read_text(encoding="utf-8").split("\n", 1)[1]
    taken = {p["id"] for p in projects}
    gifts = {}
    for p in projects:
        p["page"] = p["id"]
    for p in entries:
        # the page of a font has the name of its folder; an entry never takes the page of an example
        p["page"] = p["id"] if p["id"] not in taken else f"lib-{p['id']}"
        folder = LIBRARY / p["id"]
        for f in p["families"]:
            shutil.copyfile(f["web"], out / "fonts" / f"{f['id']}.woff2")
            if latin_slice(f):
                shutil.copyfile(latin_slice(f)[0], out / "fonts" / f"{f['id']}-basic.woff2")
        z = out / "downloads" / f"library-{p['id']}-fonts.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted((folder / "fonts").rglob("*")):
                if path.is_file() and path.suffix in (".ttf", ".woff2", ".css"):
                    zf.write(path, f"{p['id']}/{path.relative_to(folder / 'fonts')}")
            # the license names the person who holds the copyright: the one who made the font
            owner = next((f["copyright"] for f in p["families"] if f["copyright"]), f"Copyright (c) {p['github']}")
            zf.writestr(f"{p['id']}/OFL.txt", f"{owner} (https://github.com/{p['github']})\n{license_body}")
        gifts[p["id"]] = z
    books = projects + entries
    for f in (f for p in books for f in p["families"]):
        sample_key(f)                 # one order of the samples, whatever page is written first
    moods = json.loads((SEARCH / "moods.json").read_text(encoding="utf-8"))
    chrome = [f for p in projects for f in p["families"] if f["id"] in PAGE_FACES]
    common = {"LANGS": langs_menu(), "REPO": REPO, "URL": URL, "UP": UP, "EYE": EYE,
              "COUNTS": e(os.environ.get("WHATEVERFONT_COUNTS", COUNTS)),
              "ROBOTS": "" if INDEX else '<meta name="robots" content="noindex">'}

    # the shelf
    data = []
    for p in books:
        chosen, more = mood_words(p, moods)
        data.append({"id": p["page"], "name": p["title"], "moods": chosen, "more": more})
    shelf = _filled((SITE / "catalog.html").read_text(encoding="utf-8"), dict(
        common, FACES=faces_css(_once([tile_of(p)[0] for p in books] + chrome)),
        TILES="\n".join(book(p) for p in books), NUMBER=str(len(books)),
        CATALOG=json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), "the library page")
    (out / "library").mkdir()
    (out / "library" / "index.html").write_text(shelf, encoding="utf-8")

    # a page for each font, with the three fonts that are most like it
    vectors = _Vectors(SEARCH)
    words = {row["id"]: sorted(set(re.findall(r"[a-z]+", (row["moods"] or row["more"]).lower())))[:40] for row in data}
    template = (SITE / "font.html").read_text(encoding="utf-8")
    pages = [shelf]
    for p in books:
        block = entry_block(p, gifts) if p in entries else project_block(p, downloads)
        near = sorted((q for q in books if q is not p),
                      key=lambda q: -vectors.alike(words[p["page"]], words[q["page"]]))[:3]
        first = p["families"][0]
        table, count = font_charset(p)
        page = _filled(template, dict(
            common, ID=p["page"], TITLE=e(p["title"]), PROJECT=block, MORE="\n".join(book(q) for q in near),
            CHARSET=table, COUNT=str(count),
            DESCRIPTION=e(first["description"] or p.get("brief") or p.get("prompt") or p["title"]),
            FACES=faces_css(_once(p["families"] + [tile_of(q)[0] for q in near] + chrome))), f"the page of {p['title']}")
        (out / "library" / p["page"]).mkdir()
        (out / "library" / p["page"] / "index.html").write_text(page, encoding="utf-8")
        pages.append(page)

    # the characters of each whole font of another script, for the tables of the fonts' pages
    (out / "chars").mkdir(exist_ok=True)
    for part in {part["id"]: part for p in books for f in p["families"] for part in f.get("parts", []) if part["whole"]}.values():
        (out / "chars" / f"{part['id']}.json").write_text(
            json.dumps(part_chars(part), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # the Worker that counts votes and views counts only fonts that exist
    names = json.dumps(sorted(p["page"] for p in books), indent=1) + "\n"
    listed = ROOT / "worker" / "fonts.json"
    if listed.parent.is_dir() and (not listed.is_file() or listed.read_text(encoding="utf-8") != names):
        listed.write_text(names, encoding="utf-8")
    for name in ("catalog.css", "catalog.js", "search.js"):
        shutil.copyfile(SITE / name, out / name)
    (out / "search").mkdir()
    for name in ("vocab.txt", "vectors.bin"):
        shutil.copyfile(SEARCH / name, out / "search" / name)
    return pages, books


GROUP_KEYS = {"Basic letters": "chars.g1", "Accented and extended letters": "chars.g2",
              "Figures, fractions and superscripts": "chars.g3", "Punctuation": "chars.g4",
              "Signs and symbols": "chars.g5", "Combining marks, shown on o": "chars.g6",
              "Greek letters": "chars.g7", "Cyrillic letters": "chars.g8", "Other letters": "chars.g9",
              "Kana": "chars.g10", "Han characters": "chars.g11", "Hangul": "chars.g12"}

#: The groups of the table on the first page, in the order shown: (name, test of a code point, its category and
#: its Unicode name). A character goes to the first group that takes it.
GROUPS = [
    ("Basic letters", lambda c, cat, name: cat in ("Lu", "Ll") and c < 0x80),
    ("Greek letters", lambda c, cat, name: cat[0] == "L" and "GREEK" in name),
    ("Cyrillic letters", lambda c, cat, name: cat[0] == "L" and "CYRILLIC" in name),
    ("Accented and extended letters", lambda c, cat, name: cat[0] == "L"),
    ("Figures, fractions and superscripts", lambda c, cat, name: cat in ("Nd", "No")),
    ("Punctuation", lambda c, cat, name: cat[0] == "P"),
    ("Signs and symbols", lambda c, cat, name: cat[0] == "S"),
    ("Combining marks, shown on o", lambda c, cat, name: cat == "Mn"),
]

#: The groups of the table on a font's own page. A font from another tool can hold other alphabets and
#: characters of any kind, so every character has a group.
FONT_GROUPS = [
    ("Basic letters", lambda c, cat, name: cat in ("Lu", "Ll") and c < 0x80),
    ("Accented and extended letters", lambda c, cat, name: cat[0] == "L" and "LATIN" in name),
    ("Greek letters", lambda c, cat, name: cat[0] == "L" and "GREEK" in name),
    ("Cyrillic letters", lambda c, cat, name: cat[0] == "L" and "CYRILLIC" in name),
    ("Kana", lambda c, cat, name: cat[0] == "L" and name.startswith(("HIRAGANA", "KATAKANA"))),
    ("Han characters", lambda c, cat, name: cat[0] == "L" and name.startswith("CJK") and "IDEOGRAPH" in name),
    ("Hangul", lambda c, cat, name: cat[0] == "L" and name.startswith("HANGUL")),
    ("Other letters", lambda c, cat, name: cat[0] == "L"),
    ("Figures, fractions and superscripts", lambda c, cat, name: cat[0] == "N"),
    ("Punctuation", lambda c, cat, name: cat[0] == "P"),
    ("Combining marks, shown on o", lambda c, cat, name: cat[0] == "M"),
    ("Signs and symbols", lambda c, cat, name: True),
]
#: Where the table of a font's page shows its groups: the marks come last, as on the first page.
FONT_ORDER = ([name for name, _ in FONT_GROUPS if name not in ("Signs and symbols", "Combining marks, shown on o")]
              + ["Signs and symbols", "Combining marks, shown on o"])


def grouped(cps, groups: list) -> dict:
    """The characters of ``cps`` by group. Spaces and control characters are left out."""
    out = {name: [] for name, _ in groups}
    for c in sorted(set(cps)):
        cat = unicodedata.category(chr(c))
        if cat[0] in "CZ":
            continue
        name = unicodedata.name(chr(c), "")
        for group, test in groups:
            if test(c, cat, name):
                out[group].append(c)
                break
    return out


def glyph_blocks(groups: dict, only=None) -> str:
    """The boxes of a character table: a heading with a count for each group, and a button for each character.

    With ``only``, a set of code points, the other characters are in the page and hidden, and each group
    counts the ones that show. The page's script shows them when the reader picks a font that has them."""
    blocks = []
    for name, items in groups.items():
        if not items:
            continue
        cells = []
        for c in items:
            ch = chr(c)
            shown = "o" + ch if unicodedata.category(ch)[0] == "M" else ch
            label = unicodedata.name(ch, f"U+{c:04X}").lower()
            out = " hidden" if only is not None and c not in only else ""
            cells.append(f'<button type="button" data-cp="{c:04X}" data-name="{e(label)}" aria-label="{e(label)}"{out}>'
                         f'{e(shown)}</button>')
        count = len(items) if only is None else sum(c in only for c in items)
        out = "" if count else " hidden"
        blocks.append(f'<h3 class="label"{out}>{said(GROUP_KEYS[name], name)} <span class="muted">{count}</span></h3>'
                      f'<div class="glyphs"{out}>{"".join(cells)}</div>')
    return "".join(blocks)


def glyph_detail(first: int) -> str:
    """The large view of the character that the reader points at. It starts with the first character."""
    ch = chr(first)
    return (f'<aside class="glyph-detail" aria-live="polite"><div class="glyph-big">{e(ch)}</div>'
            f'<p class="glyph-name">{e(unicodedata.name(ch, "").lower())}</p>'
            f'<p class="glyph-code muted">U+{first:04X}</p></aside>')


def fold_button() -> str:
    """The button under a character table. A long table starts with its first rows, and this button opens the
    rest and closes it again. The page's script shows the button only where the table is long."""
    return ('<p class="charset-more" hidden><button type="button" aria-expanded="false">'
            '<span class="when-shut" data-i18n="chars.more">Show all characters</span>'
            '<span class="when-open" data-i18n="chars.less">Show fewer characters</span></button></p>')


def charset(projects) -> tuple[str, int]:
    drawn = [f for p in projects if p["command"] is None for f in p["families"] if not f["palettes"]]
    groups = grouped(drawn[0]["codepoints"], GROUPS)
    # the alphabets in the order of the page: Latin, its accented letters, Greek, Cyrillic, then the signs
    first = ["Basic letters", "Accented and extended letters", "Greek letters", "Cyrillic letters"]
    groups = {name: groups[name] for name in first + [name for name in groups if name not in first]}
    pills = "".join(f'<button type="button" data-font="ff-{f["id"]}" data-fvs=\'{default_fvs(f)}\' '
                    f'aria-pressed="{str(i == 0).lower()}">{e(f["name"])}</button>'
                    for i, f in enumerate(drawn))
    count = chars(drawn[0])
    body = (f'<div class="chips charset-fonts" role="group" aria-label="Font" lang="en" dir="ltr">{pills}</div>'
            f'<div class="charset-body" lang="en" dir="ltr" style=\'font-family: "ff-{drawn[0]["id"]}", var(--fallback); '
            f'font-variation-settings: {default_fvs(drawn[0])}\'>'
            f'<div class="charset-grid">{glyph_blocks(groups)}</div>{glyph_detail(0x41)}</div>{fold_button()}')
    return body, count


def hex_runs(cps) -> str:
    """Code points as short text for the page's script: "20-7E A0 ..." in hexadecimal."""
    runs = []
    for c in sorted(set(cps)):
        if runs and c == runs[-1][1] + 1:
            runs[-1][1] = c
        else:
            runs.append([c, c])
    return " ".join(f"{a:X}" if a == b else f"{a:X}-{b:X}" for a, b in runs)


def scripts_of(f: dict) -> list:
    """The whole fonts of other scripts that a family has, for the table of its page: the script's name, the
    name of the font on the page, the file with its characters, and their number."""
    return [{"name": part["script"], "font": f"ff-{f['id']}-{part['language']}", "file": f"chars/{part['id']}.json",
             "n": len(set(part.get("listed", part["codepoints"])))} for part in f.get("parts", []) if part["whole"]]


def part_chars(part: dict) -> dict:
    """The characters of a font of another script, for the page's script: the groups with their code points, and
    the names. A Han character has no name of its own, so the page writes its code."""
    groups = grouped(part.get("listed", part["codepoints"]), FONT_GROUPS)
    names = {}
    for items in groups.values():
        for c in items:
            name = unicodedata.name(chr(c), "")
            if name and not name.startswith("CJK UNIFIED IDEOGRAPH"):
                names[f"{c:04X}"] = name.lower()
    # the letters of the script come first, and the Latin letters that a font of that script carries follow them
    first = ["Kana", "Han characters", "Hangul", "Other letters"]
    order = first + [name for name in FONT_ORDER if name not in first]
    return {"count": sum(len(items) for items in groups.values()),
            "groups": [[GROUP_KEYS[name], name, hex_runs(groups[name])] for name in order if groups[name]],
            "names": names}


def font_charset(p: dict) -> tuple[str, int]:
    """The character table of one font's page, and the number of its characters.

    It shows every character of the font's families, set in the family that the reader picks. A color font
    stands on the ground of its first palette. Where the families do not have the same characters, each
    button of a family lists its own, and the page shows only those. A family with whole fonts of other
    scripts names them (``scripts_of``), and the page reads the characters of one when the reader picks it."""
    fams = p["families"]
    sets = [set(f["codepoints"]) for f in fams]
    differ = any(s != sets[0] for s in sets)
    groups = grouped(set().union(*sets), FONT_GROUPS)
    # a few letters of another alphabet (the pi of a Latin font) stay with the accented letters
    for small in ("Greek letters", "Cyrillic letters", "Other letters"):
        if len(groups[small]) < 12:
            groups["Accented and extended letters"] = sorted(groups["Accented and extended letters"] + groups[small])
            groups[small] = []
    groups = {name: groups[name] for name in FONT_ORDER}

    def dress(f: dict) -> dict:
        """What the table takes from a family: its font, its axes, and for a color font a palette and a ground."""
        look = {"font": f"ff-{f['id']}", "fvs": default_fvs(f)}
        if f["palettes"]:
            ground, ink = ground_of(f, f["palettes"][0])
            look.update(palette=f"--ff-{f['id']}-0", ground=ground, ink=ink)
        if scripts_of(f):
            look["scripts"] = json.dumps(scripts_of(f), ensure_ascii=False, separators=(",", ":"))
        return look

    pills = ""
    if len(fams) > 1:
        buttons = []
        for i, f in enumerate(fams):
            look = dress(f)
            if differ:
                look["has"] = hex_runs(f["codepoints"])
            attrs = " ".join(f"data-{key}='{e(value)}'" for key, value in look.items() if value)
            buttons.append(f'<button type="button" {attrs} aria-pressed="{str(i == 0).lower()}">{e(f["name"])}</button>')
        pills = (f'<div class="chips charset-fonts" role="group" aria-label="Style" lang="en" dir="ltr">'
                 f'{"".join(buttons)}</div>')
    look = dress(fams[0])
    style = f'font-family: "{look["font"]}", var(--fallback);'
    if look["fvs"]:
        style += f' font-variation-settings: {look["fvs"]};'
    if "ground" in look:
        style += f' font-palette: {look["palette"]}; --ground: {look["ground"]}; --tone: {look["ink"]};'
    # the page starts with the first family: where the families differ, the characters that it lacks are hidden
    blocks = glyph_blocks(groups, sets[0] if differ else None)
    shown = [c for items in groups.values() for c in items if c in sets[0]]
    # the scripts of the picked family: the page's script fills this row
    scripts = '<div class="chips charset-scripts" role="group" aria-label="Script" lang="en" dir="ltr" hidden></div>'
    has = f" data-scripts='{e(look['scripts'])}'" if "scripts" in look else ""
    body = (f'{pills}{scripts}<div class="charset-body{" dressed" if "ground" in look else ""}" lang="en" dir="ltr" '
            f"data-font='{look['font']}'{has} style='{style}'><div class=\"charset-grid\">{blocks}</div>"
            f"{glyph_detail(shown[0])}</div>{fold_button()}")
    return body, chars(fams[0])


def build(out: Path, scripts_from: Path | None = None) -> Path:
    projects = load()
    parts = load_parts(projects, scripts_from or OTHER_SCRIPTS) + load_parts(projects, PAGE_FONTS, whole=False)
    if out.exists():
        shutil.rmtree(out)
    (out / "fonts").mkdir(parents=True)
    (out / "boards").mkdir()
    (out / "downloads").mkdir()

    downloads = {}
    for p in projects:
        folder = EXAMPLES / p["id"]
        for f in p["families"]:
            shutil.copyfile(f["web"], out / "fonts" / f"{f['id']}.woff2")
        if p["board"]:
            shutil.copyfile(p["board"], out / "boards" / f"{p['id']}.html")
        z = out / "downloads" / f"{p['id']}-fonts.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted((folder / "fonts").rglob("*")):
                if path.is_file() and path.suffix in (".ttf", ".woff2", ".css"):
                    zf.write(path, f"{p['id']}/{path.relative_to(folder / 'fonts')}")
            zf.write(p["license"], f"{p['id']}/OFL.txt")
            for part in {part["id"]: part for f in p["families"] for part in f.get("parts", [])
                         if part["whole"] and part["ttf"] is not None}.values():
                # a traced font derives from another open font: it travels with that font's license text
                for path in (part["ttf"], part["web"]):
                    zf.write(path, f"{p['id']}/other-scripts/{path.name}")
                notice = part["folder"] / "OFL.txt"
                if notice.is_file() and f"{p['id']}/other-scripts/OFL.txt" not in zf.namelist():
                    zf.write(notice, f"{p['id']}/other-scripts/OFL.txt")
        downloads[p["id"]] = z
    for part in parts:
        shutil.copyfile(part["web"], out / "fonts" / f"{part['id']}.woff2")
    for f in (f for p in projects for f in p["families"]):
        if latin_slice(f):
            shutil.copyfile(latin_slice(f)[0], out / "fonts" / f"{f['id']}-basic.woff2")

    library, books = build_library(out, projects, downloads)
    chars, count = charset(projects)
    families = sum(len(p["families"]) for p in projects)
    page = (SITE / "index.html").read_text(encoding="utf-8")
    slides = hero(books)
    demo = [f for f in (_family(projects, "Last Bell Rounds"), _family(projects, "Last Bell Snow")) if f]
    first = slides[0]
    first_style = f'font-family: "{first["face"]}", var(--fallback);'
    if first["palette"]:
        first_style += f' font-palette: {first["palette"]};'
    if first["fvs"]:
        first_style += f' font-variation-settings: {first["fvs"]};'
    fills = {
        # every example family, and the family on the tile of each font that someone added
        "FACES": faces_css(_once([f for p in projects for f in p["families"]] + [tile_of(p)[0] for p in books])),
        "HERO": json.dumps(slides, ensure_ascii=False).replace("</", "<\\/"),
        "HEROASK": e(first["ask"]), "HERONAME": e(first["name"]), "HEROBY": e(first["by"]), "HEROSTYLE": first_style,
        "HEROGROUND": first["ground"], "HEROINK": first["ink"], "HEROFILE": first["face"].removeprefix("ff-"),
        "WALL": wall(books),
        "TALKBIG": font_text(demo, "demo.big", "Snow day").strip(),
        "TALKSMALL": font_text(demo, "demo.small", "staying up late,<br>sleeping in").strip(),
        "DROPS": drops(projects),
        "SKELETON": (SITE / "skeleton.svg").read_text(encoding="utf-8"),
        "DIALS": dials(books),
        "CHARSET": chars,
        "COUNT": str(count),
        "FAMILIES": str(families),
        "LANGS": langs_menu(),
        "REPO": REPO,
        "URL": URL,
        "ROBOTS": "" if INDEX else '<meta name="robots" content="noindex">',
    }
    for key, value in fills.items():
        page = page.replace(f"<!--@{key}-->", value).replace(f"@{key}@", value)
    left = re.findall(r"<!--@[A-Z]+-->|@[A-Z]+@", page)
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    (out / "index.html").write_text(page, encoding="utf-8")
    languages(out, [page] + library)
    for name in ("style.css", "app.js", "favicon.svg"):
        shutil.copyfile(SITE / name, out / name)
    shutil.copytree(SITE / "vendor", out / "vendor")
    shutil.copyfile(SITE / "card.png", out / "card.png")      # the picture of a link's preview (scripts/build_card.py)
    (out / "robots.txt").write_text("User-agent: *\n" + ("Allow: /\n" if INDEX else "Disallow: /\n"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "out" / "site"))
    ap.add_argument("--serve", type=int, metavar="PORT", help="after the build, serve the site on this computer")
    ap.add_argument("--no-build", action="store_true", help="with --serve: serve the site as it is")
    ap.add_argument("--scripts-from", metavar="DIR", help="the project with the fonts of other scripts "
                    "(default: examples/retrace)")
    args = ap.parse_args()
    out = Path(args.out)
    if not (args.serve and args.no_build):
        out = build(out, Path(args.scripts_from) if args.scripts_from else None)
        total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
        print(f"site: {out} ({total / 1e6:.1f} MB)")
    if args.serve:
        serve(out, args.serve)
    return 0


def serve(out: Path, port: int) -> None:
    """Serve the built site on this computer only.

    A page asks for some fifty fonts at once. The server of ``python -m http.server`` holds five waiting
    connections and drops the others, so a font or two would be missing. This one holds them all.
    """
    import functools
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Server(ThreadingHTTPServer):
        request_queue_size = 256
        daemon_threads = True

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")      # a new build shows at the next reload
            super().end_headers()

    with Server(("127.0.0.1", port), functools.partial(Quiet, directory=str(out))) as httpd:
        print(f"http://127.0.0.1:{port}/  (Ctrl-C stops it)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
