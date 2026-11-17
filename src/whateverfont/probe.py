"""Numbers about a design, so problems can be found without looking.

``probe`` measures the drawn glyphs: stem and counter sizes, overshoot,
sidebearings, and the checks a type designer would make by eye. It returns
plain data, and a list of problems in plain words.
"""

from __future__ import annotations

from .geom import contour_area, contour_bounds
from .glyph import MONO_FULL, G
from .spacing import Profile


def _runs(glyph, y: float) -> list:
    """Ink runs (x0, x1) along the horizontal line at height ``y``."""
    from .geom import flatten_contour
    xs = []
    for c in glyph.contours:
        pts = flatten_contour(c, 0.5)
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if (a.imag > y) != (b.imag > y):
                xs.append(a.real + (b.real - a.real) * (y - a.imag) / (b.imag - a.imag))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def probe(family, location: dict | None = None, chars: str | None = None) -> dict:
    p = family.params_at(location)
    problems: list = []
    failed = []
    names = None
    if chars:
        by_char = {chr(r.unicode): n for n, r in family.recipes.items() if r.unicode}
        names = [by_char[c] for c in chars if c in by_char]
    glyphs = family.draw(location, names=names, on_error=lambda n, e: failed.append((n, str(e))))
    for n, e in failed:
        problems.append(f"{n}: the recipe failed ({e})")

    g = G(p, "n", "lower")
    cap = G(p, "H", "upper")
    design = {
        "stem": round(g.sw, 1), "hairline": round(g.hw, 1), "cap_stem": round(cap.sw, 1),
        "contrast": round(g.hw / g.sw, 3), "n_counter": round(p.n_counter, 1),
        "x_height": p.xh, "cap_height": p.cap, "ascender": p.asc, "descender": p.desc,
        "sidebearing_straight": round(g.sidebearing("s"), 1), "sidebearing_round": round(g.sidebearing("r"), 1),
    }
    if p.serif > 0:
        design["serif"] = round(p.serif, 1)
        design["serif_thickness"] = round(g.serif_t, 1)
    if g.sw > p.n_counter * 0.95:
        problems.append(f"stems ({g.sw:.0f}) are almost as wide as the counter of n ({p.n_counter:.0f}): "
                        "the bold is filling in; lower weight or raise counter/width")
    heaviest = max(g.sw * p.round_weight, cap.sw)
    if heaviest > 165:
        problems.append(f"stems are up to {heaviest:.0f} units thick. Above about 165 the bowls and hooks of "
                        "a e s f g 5 6 9 & start to close or merge: look at them on a proof, raise counter and "
                        "width with the weight, or lower weight")
    if g.hw < 14:
        problems.append(f"hairlines are {g.hw:.0f} units: they will vanish at text sizes; raise contrast")
    if p.xh / p.cap > 0.8 or p.xh / p.cap < 0.58:
        problems.append(f"x-height is {p.xh / p.cap:.0%} of the cap height; 62-76% is the usual range")

    from .compile import _metrics
    line = _metrics(family)
    design["line_ascent"], design["line_descent"] = line["asc"], line["desc"]
    table = {}
    for name, gl in glyphs.items():
        b = contour_bounds(gl.contours)
        if b is None:
            if gl.advance <= 0:
                problems.append(f"{name}: empty glyph with no advance")
            table[name] = {"advance": gl.advance}
            continue
        area = sum(-contour_area(c) for c in gl.contours)
        row = {"advance": gl.advance, "lsb": round(b[0], 1), "rsb": round(gl.advance - b[2], 1),
               "y_min": round(b[1], 1), "y_max": round(b[3], 1), "contours": len(gl.contours),
               "ink": round(area / max(1.0, gl.advance * (p.asc - p.desc)), 3)}
        table[name] = row
        if b[1] < line["desc"] or b[3] > line["asc"]:
            problems.append(f"{name}: reaches y {b[1]:.0f}..{b[3]:.0f}, outside the line "
                            f"({line['desc']}..{line['asc']}); it will be clipped in some programs. Make the "
                            f"drawing smaller, or give the family ascent={max(line['asc'], round(b[3]) + 10)} "
                            f"and descent={min(line['desc'], round(b[1]) - 10)}")
        if area <= 0:
            problems.append(f"{name}: outline has no area (wrong winding or a collapsed stroke)")
        joins = gl.unicode is not None and (chr(gl.unicode) in MONO_FULL or 0x2500 <= gl.unicode <= 0x259F)
        stands = glyphs.get(name.split(".")[0]) if gl.unicode is None and "." in name else None
        if stands is not None and stands.unicode is not None and chr(stands.unicode) in MONO_FULL:
            joins = True                        # emdash.case fills the cell as the em dash does
        if p.mono > 0 and not p.slant and gl.advance > 0 and not joins and (b[0] < -0.5 or b[2] > gl.advance + 0.5):
            # an upright monospaced glyph must stay in its cell, or it touches its neighbor
            problems.append(f"{name}: the ink runs past its cell ({b[0]:.0f}..{b[2]:.0f} in an advance of "
                            f"{gl.advance:.0f}), so it will touch the next letter. Draw it narrower, or give "
                            "it shorter serifs")
        if gl.advance < (b[2] - b[0]) * 0.6 and "comb" not in name:
            problems.append(f"{name}: advance {gl.advance:.0f} is much smaller than the drawing ({b[2] - b[0]:.0f}), "
                            "so it will run into its neighbors. For a mark above a narrow letter (Ï at a heavy "
                            "weight) that is usual; otherwise give the recipe a wider g.frame(...)")

    # The letter checks below assume the built-in Latin drawings. A project that
    # redraws a letter (a stencil, a picture font) gets no false alarms for it.
    from .recipes import latin
    builtin = latin()
    drawn_by = lambda rec: rec.plain or rec.fn          # an effect wraps a letter; it does not redraw it
    checked = ("e", "a", "o", "B", "eight", "n")
    redrawn = sorted(n for n in checked
                     if n in family.recipes and n in builtin and drawn_by(family.recipes[n]) is not builtin[n].fn)
    # an effect (an outline, a stencil, paint) changes the ink, so the counts of stems and counters do not hold
    finished = sorted(n for n in checked if n in family.recipes and n not in redrawn and family.recipes[n].plain)
    redrawn = sorted(set(redrawn) | set(finished))

    # counters: the white inside closed letters must stay open
    for name, frac in (("e", 0.74), ("a", 0.28), ("o", 0.5), ("B", 0.76), ("8", 0.76)):
        gl = glyphs.get(name if name != "8" else "eight")
        if gl is None or not gl.contours or (name if name != "8" else "eight") in redrawn:
            continue
        b = contour_bounds(gl.contours)
        height = p.xh if name.islower() else p.cap
        runs = _runs(gl, height * frac)
        if len(runs) >= 2:
            white = min(runs[i + 1][0] - runs[i][1] for i in range(len(runs) - 1))
            if white < g.hw * 0.5:
                problems.append(f"{name}: the counter is only {white:.0f} units wide at {frac:.0%} height; it will fill in")
        holes = sum(1 for c in gl.contours if contour_area(c) > 0)
        want = {"e": 1, "a": 1, "o": 1, "B": 2, "8": 2}[name]
        if holes < want:
            problems.append(f"{name}: expected {want} enclosed counter(s), found {holes}")

    # measured stems: the n should show two runs of ink below its arch
    measured = {}
    if "n" in glyphs and "n" not in redrawn:
        runs = _runs(glyphs["n"], p.xh * 0.45)     # between the flare at the foot and the arch
        if len(runs) == 2:
            measured["n_stems"] = [round(r[1] - r[0], 1) for r in runs]
            measured["n_counter"] = round(runs[1][0] - runs[0][1], 1)
        else:
            problems.append(f"n: expected two stems at 45% of the x-height, found {len(runs)} runs of ink")
    if "o" in glyphs:
        b = contour_bounds(glyphs["o"].contours)
        measured["o_overshoot"] = [round(-b[1], 1), round(b[3] - p.xh, 1)]
    out = {"family": family.name, "location": location or family.default_location(), "design": design,
           "measured": measured, "glyphs": table, "problems": problems}
    if redrawn:
        why = "an effect changes their outlines" if finished == redrawn else "the project draws or finishes these itself"
        out["skipped"] = f"letter checks skipped for {', '.join(redrawn)}: {why}, so look at them on a proof"
    return out
