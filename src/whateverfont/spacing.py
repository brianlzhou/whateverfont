"""Automatic kerning and spacing measurements.

Sidebearings come from the recipes (each side of a glyph declares whether it
is straight, round, diagonal or open). Kerning then fixes the pairs that
sidebearings cannot, such as ``AV`` or ``To``: it measures the white between
two glyphs and moves them until that white matches the white between two
straight stems.
"""

from __future__ import annotations

from operator import add

from .geom import flatten_contour

BANDS = 28


class Profile:
    """Left and right edges of a glyph, sampled in horizontal bands."""

    def __init__(self, glyph, y0: float, y1: float, bands: int = BANDS):
        self.advance = glyph.advance
        self.y0, self.y1, self.n = y0, y1, bands
        self.left = [None] * bands
        self.right = [None] * bands
        step = (y1 - y0) / bands
        # a color glyph is measured by its bottom layer (the field), not by the letter alone
        contours = glyph.layers[0][1] if getattr(glyph, "layers", None) else glyph.contours
        for c in contours:
            pts = flatten_contour(c, 2.0)
            m = len(pts)
            for i in range(m):
                a, b = pts[i], pts[(i + 1) % m]
                lo, hi = sorted((a.imag, b.imag))
                i0 = max(0, int((lo - y0) / step))
                i1 = min(bands - 1, int((hi - y0) / step))
                for k in range(i0, i1 + 1):
                    # the part of the edge inside this band
                    ya, yb = y0 + k * step, y0 + (k + 1) * step
                    xs = []
                    for y in (max(lo, ya), min(hi, yb)):
                        if abs(b.imag - a.imag) < 1e-9:
                            xs += [a.real, b.real]
                        else:
                            t = (y - a.imag) / (b.imag - a.imag)
                            xs.append(a.real + (b.real - a.real) * min(1, max(0, t)))
                    if not xs:
                        continue
                    lo_x, hi_x = min(xs), max(xs)
                    self.left[k] = lo_x if self.left[k] is None else min(self.left[k], lo_x)
                    self.right[k] = hi_x if self.right[k] is None else max(self.right[k], hi_x)

        # How close ink could come in each band, also counting the bands next to it.
        # Worked out once per glyph: every pair this glyph is in reads them.
        inf = float("inf")
        self.right_near, self.left_near = [], []
        for k in range(bands):
            near = [j for j in (k - 1, k, k + 1) if 0 <= j < bands]
            rs = [self.right[j] for j in near if self.right[j] is not None]
            ls = [self.left[j] for j in near if self.left[j] is not None]
            # distance from the ink to the advance on the right, and to the origin on the left
            self.right_near.append(self.advance - max(rs) if rs else inf)
            self.left_near.append(min(ls) if ls else inf)
        self._white: dict = {}

    def has_ink(self) -> bool:
        return any(v is not None for v in self.left)

    def white(self, side: str, depth: float, zone: tuple) -> list:
        """White on one side in each band of ``zone``, no deeper than ``depth``."""
        key = (side, depth, zone)
        got = self._white.get(key)
        if got is None:
            lo, hi = max(0, zone[0]), max(0, zone[1])
            if side == "right":
                got = [depth if v is None else min(depth, self.advance - v) for v in self.right[lo:hi]]
            else:
                got = [depth if v is None else min(depth, v) for v in self.left[lo:hi]]
            self._white[key] = got
        return got


def pair_kern(a: Profile, b: Profile, target: float, depth: float, floor: float,
              zone: tuple, strength: float = 0.5) -> float:
    """Kern for the pair ``a b`` (negative pulls them together).

    ``target`` is the white between two straight stems. ``depth`` limits how
    far into an open shape the measurement reaches. ``floor`` is the closest
    the two outlines may come. ``zone`` is the band range that counts.
    """
    closest = min(map(add, a.right_near, b.left_near))
    gaps = list(map(add, a.white("right", depth, zone), b.white("left", depth, zone)))
    if not gaps or closest == float("inf"):
        return 0.0
    mean = sum(gaps) / len(gaps)
    kern = (target - mean) * strength
    # never push outlines closer than the floor
    kern = max(kern, floor - closest)
    return kern


LEFT_GROUP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
#: The Cyrillic and Greek letters that are kerned: the ones without marks, as for Latin.
CYRILLIC_GROUP = ("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзиклмнопрстуфхцчшщъыьэюяЂЄЅІЈЉЊЋЏђєѕіјљњћџҐґ"
                  "ҒғҚқҢңҮүҰұҺһӘәӨө")
GREEK_GROUP = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρςστυφχψω"
PUNCT = ["period", "comma", "colon", "semicolon", "hyphen", "endash", "emdash", "quoteright", "quoteleft",
         "quotedblright", "quotedblleft", "quotesingle", "quotedbl", "parenleft", "parenright",
         "question", "exclam", "slash"]


def kerned_letters(glyphs: dict) -> dict:
    """The letters that are kerned: glyph name -> (script, lowercase). Each letter is kerned with the
    letters of its own script and with the punctuation; a Latin and a Cyrillic letter are not."""
    out = {c: ("latn", c.islower()) for c in LEFT_GROUP if c in glyphs}
    by_code = {g.unicode: n for n, g in glyphs.items() if getattr(g, "unicode", None) is not None}
    for script, chars in (("cyrl", CYRILLIC_GROUP), ("grek", GREEK_GROUP)):
        for ch in chars:
            name = by_code.get(ord(ch))
            if name is not None and name not in out:
                out[name] = (script, ch.islower())
    return out


def kerning(glyphs: dict, params, pairs=None) -> dict:
    """Kerning for a glyph set: {(left, right): value}."""
    if params.kerning <= 0 or params.mono > 0:
        return {}
    letters = kerned_letters(glyphs)
    punct = [p for p in PUNCT if p in glyphs]
    names = list(letters) + punct
    y0, y1 = params.desc, params.asc + 20
    prof = {n: Profile(glyphs[n], y0, y1) for n in names}
    step = (y1 - y0) / BANDS
    band = lambda y: int((y - y0) / step)
    if "n" in glyphs:
        from .glyph import G
        g = G(params, "n", "lower")
        target = g.sidebearing("s") * 1.94
    else:
        target = 120.0
    depth_lc = target * 1.05
    floor = max(24.0, target * 0.40, params.weight * 0.42)
    upper = lambda n: n in letters and not letters[n][1]
    out = {}
    if pairs is not None:
        candidates = pairs
    else:
        candidates = [(l, r) for l in names for r in names
                      if l not in letters or r not in letters or letters[l][0] == letters[r][0]]
    for l, r in candidates:
        if l not in prof or r not in prof:
            continue
        any_punct = l not in letters or r not in letters
        if l not in letters and r not in letters:
            continue
        both_caps = upper(l) and upper(r)
        top = params.cap if both_caps else params.xh
        if any_punct:
            top = params.cap if upper(l) or upper(r) else params.xh
        zone = (band(0.0), band(top) + 1)
        scale = 1.2 if both_caps else 1.0
        k = pair_kern(prof[l], prof[r], target * scale, depth_lc * scale, floor, zone)
        k *= params.kerning
        k = max(-0.11 * params.upm, min(0.025 * params.upm, k))
        out[(l, r)] = k
    return out


def significant(kerns: dict, threshold: float = 10.0) -> list:
    return [pair for pair, v in kerns.items() if abs(v) >= threshold]


def to_feature(kerns: dict, pairs: list) -> str:
    """A ``kern`` feature in feature-file syntax."""
    if not pairs:
        return ""
    lines = ["feature kern {"]
    for l, r in pairs:
        lines.append(f"    pos {l} {r} {int(round(kerns.get((l, r), 0.0)))};")
    lines.append("} kern;")
    return "\n".join(lines)
