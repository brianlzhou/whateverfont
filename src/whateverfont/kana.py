"""Kana from KanjiVG centerlines (experimental).

KanjiVG (https://github.com/KanjiVG/kanjivg) holds hand-traced centerlines of
every stroke of the kana and of about 6,000 kanji. The pen that draws the
Latin letters can expand those strokes too, so a family's weight, contrast
and roundness carry over to kana.

KanjiVG is copyright Ulrich Apel and licensed CC BY-SA 3.0. A font built from
it is a derivative work: it must credit KanjiVG and be shared under the same
license. The data is not part of whateverfont; ``download`` fetches it on request.
"""

from __future__ import annotations

import math
import re
import urllib.request
from pathlib import Path

from .geom import cross, dot, unit
from .glyph import G, Recipe, Recipes
from .stroke import Cap, Node, Stroke

LICENSE = "CC-BY-SA-3.0"
CREDIT = "Kana strokes derive from KanjiVG, copyright Ulrich Apel, CC BY-SA 3.0 (https://kanjivg.tagaini.net)."
RAW = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{:05x}.svg"
HIRAGANA = range(0x3041, 0x3097)
KATAKANA = list(range(0x30A1, 0x30FB)) + [0x30FC]
BOX = 109.0


def download(folder: str | Path, codepoints=None) -> Path:
    """Fetch the kana SVG files into ``folder``. Skips files that are already there."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for cp in (codepoints or list(HIRAGANA) + KATAKANA):
        target = folder / f"{cp:05x}.svg"
        if target.exists():
            continue
        try:
            with urllib.request.urlopen(RAW.format(cp), timeout=30) as resp:
                target.write_bytes(resp.read())
        except Exception:
            continue    # KanjiVG does not have every code point
    return folder


_TOKEN = re.compile(r"([MmCcSsLlHhVvZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")


def parse_path(d: str) -> list:
    """An SVG path as a list of absolute cubic segments (p0, p1, p2, p3)."""
    tokens = [(m.group(1), m.group(2)) for m in _TOKEN.finditer(d)]
    segs, i = [], 0
    cur = start = 0j
    last_ctrl = None
    cmd = None

    def nums(n):
        nonlocal i
        out = []
        while len(out) < n and i < len(tokens) and tokens[i][1] is not None:
            out.append(float(tokens[i][1]))
            i += 1
        return out if len(out) == n else None

    while i < len(tokens):
        if tokens[i][0] is not None:
            cmd = tokens[i][0]
            i += 1
            if cmd in "Zz":
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            v = nums(2)
            if v is None:
                break
            cur = (cur if rel else 0j) + complex(v[0], v[1])
            start, last_ctrl = cur, None
            cmd = "l" if rel else "L"
        elif c == "L":
            v = nums(2)
            if v is None:
                break
            p = (cur if rel else 0j) + complex(v[0], v[1])
            segs.append((cur, cur + (p - cur) / 3, cur + (p - cur) * 2 / 3, p))
            cur, last_ctrl = p, None
        elif c in "HV":
            v = nums(1)
            if v is None:
                break
            if c == "H":
                p = complex(v[0] + (cur.real if rel else 0), cur.imag)
            else:
                p = complex(cur.real, v[0] + (cur.imag if rel else 0))
            segs.append((cur, cur + (p - cur) / 3, cur + (p - cur) * 2 / 3, p))
            cur, last_ctrl = p, None
        elif c == "C":
            v = nums(6)
            if v is None:
                break
            o = cur if rel else 0j
            p1, p2, p3 = o + complex(v[0], v[1]), o + complex(v[2], v[3]), o + complex(v[4], v[5])
            segs.append((cur, p1, p2, p3))
            cur, last_ctrl = p3, p2
        elif c == "S":
            v = nums(4)
            if v is None:
                break
            o = cur if rel else 0j
            p1 = cur * 2 - last_ctrl if last_ctrl is not None else cur
            p2, p3 = o + complex(v[0], v[1]), o + complex(v[2], v[3])
            segs.append((cur, p1, p2, p3))
            cur, last_ctrl = p3, p2
        else:
            break
    return segs


def read_strokes(svg_text: str) -> list:
    """The strokes of one KanjiVG file, each a list of cubic segments in file coordinates."""
    out = []
    for m in re.finditer(r"<path\b[^>]*?\bd=\"([^\"]+)\"", svg_text):
        segs = [s for s in parse_path(m.group(1)) if abs(s[3] - s[0]) > 0.2]
        if segs:
            out.append(segs)
    return out


def _recipe(strokes: list, scale: float, weight_scale: float, taper: float):
    def to_em(p: complex) -> complex:
        return complex((p.real - BOX / 2) * scale + 500, (BOX / 2 - p.imag) * scale + 380)

    def draw(g: G):
        for segs in strokes:
            nodes = [Node(to_em(segs[0][0]), 1.0)]
            handles = []
            for k, s in enumerate(segs):
                handles.append((to_em(s[1]), to_em(s[2])))
                corner = False
                if k + 1 < len(segs):
                    a = unit(s[3] - s[2]) or unit(s[3] - s[0])
                    b = unit(segs[k + 1][1] - segs[k + 1][0]) or unit(segs[k + 1][3] - segs[k + 1][0])
                    ang = abs(math.degrees(math.atan2(cross(a, b), dot(a, b))))
                    corner = ang > 35
                last = k == len(segs) - 1
                nodes.append(Node(to_em(s[3]), taper if last else 1.0, None, corner))
            g.strokes.append(Stroke(nodes, handles, False, Cap(), Cap(), weight_scale, None, True, 2.0, "kana"))
        g._frame = (1000.0, 0, 0)

    return draw


def recipes(folder: str | Path, fill: float = 1.10, weight_scale: float = 0.95, taper: float = 0.78) -> Recipes:
    """Recipes for every kana SVG in ``folder``.

    ``fill`` is how much of the em the KanjiVG box takes. ``weight_scale`` is
    the stroke weight relative to Latin stems. ``taper`` thins the end of each
    stroke, like a brush lifting off; 1 keeps strokes even.
    """
    out = Recipes()
    scale = 1000.0 * fill / BOX
    for path in sorted(Path(folder).glob("*.svg")):
        try:
            cp = int(path.stem, 16)
        except ValueError:
            continue
        strokes = read_strokes(path.read_text(encoding="utf-8", errors="replace"))
        if strokes:
            name = f"uni{cp:04X}"
            out[name] = Recipe(name, _recipe(strokes, scale, weight_scale, taper), cp, "lower")
    return out
