"""Compile a family into font files: static TTF, WOFF2 and a variable font."""

from __future__ import annotations

import array
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from fontTools import varLib
from fontTools.cu2qu import curves_to_quadratic
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
    SourceDescriptor,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph as TTGlyph
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

from . import features, marks, spacing
from .family import Family, style_location
from .geom import xy

OVERLAP_SIMPLE = 0x40
MAX_ERR = 0.9
#: The date written into font files (January 1, 2026, UTC) unless SOURCE_DATE_EPOCH is set.
#: A fixed date makes a build reproducible: the same design gives the same bytes.
BUILD_EPOCH = 1767225600


@dataclass
class BuildResult:
    family: str
    files: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    #: style name -> path of the static TTF
    statics: dict = field(default_factory=dict)
    variable: Path | None = None
    kerning_pairs: int = 0
    #: Things the designer should know that are not faults: for example why a family has no variable font.
    notes: list = field(default_factory=list)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def note(self, msg: str):
        self.notes.append(msg)


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", name)


def _stamp(font: TTFont) -> TTFont:
    """Give the font a fixed date, so that building twice gives the same file."""
    from fontTools.misc.timeTools import timestampSinceEpoch
    when = timestampSinceEpoch(int(os.environ.get("SOURCE_DATE_EPOCH", BUILD_EPOCH)))
    font["head"].created = font["head"].modified = when
    font.recalcTimestamp = False
    return font


# --------------------------------------------------------------------------
# Outlines -> TrueType glyphs
# --------------------------------------------------------------------------

def _tt_glyph(contours_pts, overlap: bool = False) -> TTGlyph:
    """``contours_pts`` is a list of contours, each a list of (x, y, on_curve)."""
    g = TTGlyph()
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    contours_pts = [c for c in contours_pts if c]
    g.numberOfContours = len(contours_pts)
    if not contours_pts:
        return g
    coords, flags, ends = [], [], []
    for c in contours_pts:
        for x, y, on in c:
            coords.append((otRound(x), otRound(y)))
            flags.append(1 if on else 0)
        ends.append(len(coords) - 1)
    if overlap:
        flags[0] |= OVERLAP_SIMPLE
    g.coordinates = GlyphCoordinates(coords)
    g.flags = array.array("B", flags)
    g.endPtsOfContours = ends
    return g


def quadratic_points(masters: list) -> list:
    """Convert the same glyph in several masters to TrueType points.

    ``masters`` is a list (one entry per master) of contour lists with the
    same structure. Each cubic becomes a quadratic spline with the same
    number of points in every master, so the results interpolate.
    """
    n = len(masters)
    first = masters[0]
    for m in masters[1:]:
        if len(m) != len(first) or any(len(a) != len(b) for a, b in zip(m, first)):
            raise ValueError("masters do not have the same contours")
    out = [[] for _ in range(n)]
    for ci in range(len(first)):
        pts = [[] for _ in range(n)]
        for si in range(len(first[ci])):
            kinds = {len(m[ci][si]) for m in masters}
            if len(kinds) != 1:
                raise ValueError("a segment is a line in one master and a curve in another")
            if kinds == {2}:
                for mi in range(n):
                    x, y = xy(masters[mi][ci][si][1])
                    pts[mi].append((x, y, True))
                continue
            curves = [[xy(q) for q in masters[mi][ci][si]] for mi in range(n)]
            try:
                splines = curves_to_quadratic(curves, [MAX_ERR] * n)
            except Exception:
                # a degenerate curve: fall back to one off-curve point at the handle average
                splines = [[c[0], ((c[1][0] + c[2][0]) / 2, (c[1][1] + c[2][1]) / 2), c[3]] for c in curves]
            for mi in range(n):
                sp = splines[mi]
                for q in sp[1:-1]:
                    pts[mi].append((q[0], q[1], False))
                pts[mi].append((sp[-1][0], sp[-1][1], True))
        for mi in range(n):
            out[mi].append(pts[mi])
    return out


def _notdef(p) -> tuple:
    w, h, t = 500, p.cap, 50
    outer = [(60, 0, True), (60, h, True), (w - 60, h, True), (w - 60, 0, True)]
    inner = [(60 + t, t, True), (w - 60 - t, t, True), (w - 60 - t, h - t, True), (60 + t, h - t, True)]
    return _tt_glyph([outer, inner]), w


# --------------------------------------------------------------------------
# One font
# --------------------------------------------------------------------------

def _metrics(family: Family) -> dict:
    p = family.base
    asc = p.line_top if family.ascent is None else family.ascent
    desc = p.line_bottom if family.descent is None else -abs(family.descent)
    return {"asc": int(round(asc)), "desc": int(round(desc))}


def _where(exc: BaseException) -> str:
    """Where an error in a recipe or an effect happened: the last line of the project's own code."""
    import traceback
    cause = exc.__cause__ or exc
    here = str(Path(__file__).resolve().parent)
    frames = traceback.extract_tb(cause.__traceback__)
    own = [f for f in frames if not f.filename.startswith(here)] or frames
    if not own:
        return ""
    f = own[-1]
    return f" ({Path(f.filename).name}, line {f.lineno}: {(f.line or '').strip()})"


def _is_italic(p) -> bool:
    return abs(p.slant) > 0.5


def _weight_class(family: Family, location: dict, p) -> int:
    if "wght" in location:
        return int(round(location["wght"]))
    return int(max(100, min(900, round((400 + (p.weight - 82) * 4.4) / 100) * 100)))


def make_font(family: Family, glyphs: dict, tt: dict, p, style: str, location: dict,
              feature: str = "", result: BuildResult | None = None) -> TTFont:
    """Assemble a TTFont from finished glyphs. ``tt`` maps glyph name -> TTGlyph."""
    order = [".notdef"] + list(glyphs)
    nd, nd_w = _notdef(family.base)
    if p.mono > 0:
        nd_w = int(round(p.mono))
    tt = dict(tt)
    tt[".notdef"] = nd
    cmap = {g.unicode: n for n, g in glyphs.items() if g.unicode is not None}
    fb = FontBuilder(p.upm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(tt)
    hmtx = {".notdef": (nd_w, 60)}
    glyf = fb.font["glyf"]
    for n, g in glyphs.items():
        ttg = tt[n]
        ttg.recalcBounds(glyf)
        hmtx[n] = (int(g.advance), int(getattr(ttg, "xMin", 0) or 0))
    fb.setupHorizontalMetrics(hmtx)
    vm = _metrics(family)
    fb.setupHorizontalHeader(ascent=vm["asc"], descent=vm["desc"], lineGap=0)

    italic = _is_italic(p)
    weight = _weight_class(family, location, p)
    bold = weight >= 700
    ribbi = style in ("Regular", "Italic", "Bold", "Bold Italic")
    fam = family.name
    ps = f"{slug(fam)}-{slug(style)}"
    names = {
        "familyName": fam if ribbi else f"{fam} {style}",
        "styleName": style if ribbi else "Regular",
        "uniqueFontIdentifier": f"{family.version};{family.vendor};{ps}",
        "fullName": f"{fam} {style}",
        "psName": ps,
        "version": f"Version {family.version}",
    }
    if not ribbi:
        names["typographicFamily"] = fam
        names["typographicSubfamily"] = style
    if family.copyright:
        names["copyright"] = family.copyright
    if family.designer:
        names["designer"] = family.designer
    if family.description:
        names["description"] = family.description
    if family.license:
        names["licenseDescription"] = _license_text(family)
        names["licenseInfoURL"] = family.license_url
    fb.setupNameTable(names)

    sel = 0x80  # USE_TYPO_METRICS
    if italic:
        sel |= 0x01
    if bold and ribbi:
        sel |= 0x20
    if not italic and not (bold and ribbi):
        sel |= 0x40
    ymax = max([getattr(tt[n], "yMax", 0) or 0 for n in glyphs] + [vm["asc"]])
    ymin = min([getattr(tt[n], "yMin", 0) or 0 for n in glyphs] + [vm["desc"]])
    fb.setupOS2(
        sTypoAscender=vm["asc"], sTypoDescender=vm["desc"], sTypoLineGap=0,
        usWinAscent=int(ymax), usWinDescent=int(-ymin),
        sxHeight=int(p.xh), sCapHeight=int(p.cap),
        usWeightClass=weight, usWidthClass=5, fsSelection=sel, fsType=0,
        achVendID=(family.vendor + "    ")[:4], version=4,
    )
    fb.setupPost(italicAngle=-float(p.slant), underlinePosition=int(p.desc * 0.5),
                 underlineThickness=int(max(30, p.weight * 0.62)))
    font = fb.font
    if p.mono > 0:
        # tell programs that every glyph has one width, so terminals and editors accept the font
        font["post"].isFixedPitch = 1
        font["OS/2"].panose.bProportion = 9
        font["OS/2"].xAvgCharWidth = int(round(p.mono))
    font["head"].macStyle = (1 if bold and ribbi else 0) | (2 if italic else 0)
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 15}
    font["gasp"] = gasp
    if feature:
        try:
            fb.addOpenTypeFeatures(feature)
        except Exception as exc:
            if result is not None:
                result.warn(f"{style}: kerning and mark positioning were left out ({exc})")
    return font


def _license_text(family: Family) -> str:
    if family.license.upper().startswith("OFL"):
        return ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                "This license is available with a FAQ at https://openfontlicense.org")
    return family.license


# --------------------------------------------------------------------------
# Static and variable builds
# --------------------------------------------------------------------------

def draw_static(family: Family, location: dict, result: BuildResult | None = None):
    """Glyphs, TrueType glyphs and kerning for one static style."""
    p = family.params_at(location)
    failed, trouble = [], []
    glyphs = family.draw(location, on_error=lambda n, e: failed.append((n, e)),
                         on_trouble=lambda n, text: trouble.append((n, text)))
    for n, e in failed:
        if result is not None:
            result.warn(f"glyph {n!r} failed and was left out: {e}{_where(e)}")
    for n, text in trouble:
        if result is not None:
            result.warn(f"glyph {n!r}: {text}")
    tt = {}
    for n, g in glyphs.items():
        pts = quadratic_points([g.contours])[0]
        tt[n] = _tt_glyph(pts)
    kerns = spacing.kerning(glyphs, p)
    pairs = spacing.significant(kerns)
    # color layers become glyphs of their own
    from .glyph import Glyph
    colr = {}
    for n, g in list(glyphs.items()):
        if not g.layers:
            continue
        colr[n] = []
        for i, (key, contours) in enumerate(g.layers):
            ln = f"{n}.c{i}"
            glyphs[ln] = Glyph(ln, g.advance, contours)
            tt[ln] = _tt_glyph(quadratic_points([contours])[0])
            colr[n].append((ln, key))
    return p, glyphs, tt, kerns, pairs, colr


def build_static(family: Family, style: str, out_dir: Path, result: BuildResult, woff2: bool = True) -> Path:
    location = style_location(family, style)
    p, glyphs, tt, kerns, pairs, colr = draw_static(family, location, result)
    fea = feature_code(family, glyphs, p) + spacing.to_feature(kerns, pairs)
    font = make_font(family, glyphs, tt, p, style, location, fea, result)
    from .color import add_color
    add_color(font, family, colr, result)
    ttf_dir = out_dir / "ttf"
    ttf_dir.mkdir(parents=True, exist_ok=True)
    path = ttf_dir / f"{slug(family.name)}-{slug(style)}.ttf"
    _stamp(font).save(path)
    result.files.append(path)
    result.statics[style] = path
    result.kerning_pairs = max(result.kerning_pairs, len(pairs))
    if woff2:
        result.files.append(save_woff2(path, out_dir / "woff2"))
    return path


#: Brotli looks back 4 MB by default (a window of 2**22 bytes). A large color font of Chinese characters
#: repeats data farther apart than that: each letter layer copies its glyph. Above that size the WOFF2 data is
#: compressed with a window of 2**24 bytes, the largest of standard Brotli, which every WOFF2 decoder reads.
#: Last Bell Snow Traditional Chinese goes from 11.7 to 7.0 MB. A smaller font is compressed as before.
WIDE_WINDOW = 24


class _WideBrotli:
    """fontTools' brotli module, with the wide window for data larger than the default window."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def compress(self, data, **options):
        if len(data) > 1 << 22:
            options.setdefault("lgwin", WIDE_WINDOW)
        return self._real.compress(data, **options)


def save_woff2(ttf_path: Path, out_dir: Path) -> Path:
    from fontTools.ttLib import woff2
    out_dir.mkdir(parents=True, exist_ok=True)
    font = TTFont(ttf_path)
    font.flavor = "woff2"
    font.recalcTimestamp = False
    path = out_dir / (ttf_path.stem + ".woff2")
    real = woff2.brotli
    woff2.brotli = _WideBrotli(real)
    try:
        font.save(path)
    finally:
        woff2.brotli = real
    return path


def draw_master(family: Family, location: dict) -> tuple:
    """One master of the variable font: its glyphs, the names that failed, and its kerning."""
    failed = set()
    drawn = family.draw(location, keep_structure=True, on_error=lambda n, e: failed.add(n))
    kerns = spacing.kerning(_union_copy(drawn, list(drawn)), family.params_at(location))
    return drawn, failed, kerns


def serif_mismatch(family: Family) -> str | None:
    """Why the masters of a variable font cannot match because of serifs, or None.

    Slab serifs are extra strokes: a master with ``serif`` 0 has fewer of them than one with
    serifs, so a family must have serifs in every master or in none.
    """
    have = [family.params_at(loc).serif > 0 for loc in family.masters()]
    if any(have) and not all(have):
        return (f"{family.name}: serif is 0 in some masters of the variable font and more than 0 in others. "
                "Serifs add strokes, so the masters cannot match, and no variable font was built. Keep serif "
                "above 0 at every pole (an axis may change its length), or 0 at every pole.")
    return None


def build_variable(family: Family, out_dir: Path, result: BuildResult, woff2: bool = True,
                   masters: list | None = None) -> Path | None:
    """One variable font that covers every axis of the family.

    ``masters`` is the output of :func:`draw_master` for every location of
    ``family.masters()``, if they were drawn already.
    """
    if not family.axes:
        return None
    mismatch = serif_mismatch(family)
    if mismatch:
        result.warn(mismatch)
        return None
    locations = family.masters()
    params = [family.params_at(loc) for loc in locations]
    if masters is None:
        masters = [draw_master(family, loc) for loc in locations]
    drawn = [m[0] for m in masters]
    failed = set().union(*[m[1] for m in masters])
    fixed = [n for n, g in drawn[0].items() if g.static_only]
    if fixed:
        # a variable file would lose the cut (the bridges of a stencil) without a word
        result.note(f"{family.name}: {len(fixed)} glyphs are cut or redrawn after their strokes are drawn "
                    f"(a stencil, an effect; the first is {fixed[0]!r}), so no variable font was built. "
                    "Each named style is a static font; the stylesheet points to those.")
        return None
    names = [n for n in family.recipes if n not in failed and all(n in d for d in drawn)]
    for n in sorted(failed):
        result.warn(f"variable font: glyph {n!r} failed in a master and was left out")

    # quadratic outlines that interpolate
    tts = [dict() for _ in locations]
    kept = []
    for n in names:
        try:
            per_master = quadratic_points([d[n].contours for d in drawn])
        except ValueError as exc:
            result.warn(f"variable font: glyph {n!r} left out ({exc})")
            continue
        for mi in range(len(locations)):
            tts[mi][n] = _tt_glyph(per_master[mi], overlap=True)
        kept.append(n)

    # kerning: the same pairs in every master
    kern_sets = []
    in_font = set(kept)
    for mi, d in enumerate(drawn):
        if "n" in d and "n" not in in_font:
            # the n sets the target white; without it, measure again with what is left
            kern_sets.append(spacing.kerning(_union_copy(d, kept), params[mi]))
        else:
            kern_sets.append({pair: v for pair, v in masters[mi][2].items()
                              if pair[0] in in_font and pair[1] in in_font})
    pairs = sorted({pair for k in kern_sets for pair in spacing.significant(k)})

    def assemble(with_kerning: bool):
        fonts = []
        for mi, loc in enumerate(locations):
            glyphs = {n: drawn[mi][n] for n in kept}
            fea = feature_code(family, {n: drawn[mi][n] for n in kept}, params[mi])
            fea += spacing.to_feature(kern_sets[mi], pairs) if with_kerning else ""
            fonts.append(make_font(family, glyphs, {n: tts[mi][n] for n in kept}, params[mi],
                                   "Regular", loc, fea, result))
        ds = DesignSpaceDocument()
        for a in family.axes:
            ad = AxisDescriptor()
            ad.tag, ad.name = a.tag, a.name
            ad.minimum, ad.default, ad.maximum = a.minimum, a.default, a.maximum
            ds.addAxis(ad)
        by_tag = {a.tag: a.name for a in family.axes}
        for mi, loc in enumerate(locations):
            s = SourceDescriptor()
            s.font = fonts[mi]
            s.location = {by_tag[t]: v for t, v in loc.items()}
            s.familyName = family.name
            s.styleName = "Regular" if mi == 0 else f"Master {mi}"
            if mi == 0:
                s.copyInfo = s.copyFeatures = s.copyLib = s.copyGroups = True
            ds.addSource(s)
        for style, sloc in family.styles.items():
            inst = InstanceDescriptor()
            full = family.default_location()
            full.update(sloc)
            inst.location = {by_tag[t]: v for t, v in full.items()}
            inst.familyName = family.name
            inst.styleName = style
            inst.postScriptFontName = f"{slug(family.name)}-{slug(style)}"
            ds.addInstance(inst)
        vf, _, _ = varLib.build(ds)
        # The OS/2 table comes from the default master, but Windows clips every instance at its
        # usWinAscent and usWinDescent: they must hold the tallest and the deepest glyph of any master
        # (the marks of a bold Ẫ stand higher than those of a light one).
        vf["OS/2"].usWinAscent = max(f["OS/2"].usWinAscent for f in fonts)
        vf["OS/2"].usWinDescent = max(f["OS/2"].usWinDescent for f in fonts)
        return vf

    try:
        vf = assemble(True)
        result.kerning_pairs = max(result.kerning_pairs, len(pairs))
    except Exception as exc:
        result.warn(f"variable font: kerning could not be merged ({type(exc).__name__}: {exc}); built without it")
        try:
            vf = assemble(False)
        except Exception as exc2:
            result.warn(f"variable font failed: {type(exc2).__name__}: {exc2}")
            return None

    var_dir = out_dir / "variable"
    var_dir.mkdir(parents=True, exist_ok=True)
    tags = ",".join(a.tag for a in family.axes)
    path = var_dir / f"{slug(family.name)}[{tags}].ttf"
    _stamp(vf).save(path)
    result.files.append(path)
    result.variable = path
    if woff2:
        result.files.append(save_woff2(path, var_dir))
    return path


def _cases(family: Family) -> dict:
    return {n: r.case for n, r in family.recipes.items()}


def feature_code(family: Family, glyphs: dict, p) -> str:
    """The substitution and mark features of a font: marks and language forms, then the figure and
    case features of :mod:`whateverfont.features`. The kerning is added after."""
    fea = marks.feature(glyphs, _cases(family), p)
    more = features.code(glyphs, p)
    if more and not fea:
        fea = "\n".join(marks.languages(glyphs)) + "\n"
    return fea + more


def _union_copy(drawn: dict, names: list) -> dict:
    """Master glyphs with overlaps removed, for measuring only."""
    from .glyph import Glyph
    from .outline import union
    out = {}
    for n in names:
        g = drawn[n]
        out[n] = Glyph(g.name, g.advance, union(g.contours), g.unicode)
    return out


# --------------------------------------------------------------------------
# Building a family, with the styles and masters drawn in parallel
# --------------------------------------------------------------------------

#: What the worker processes build. Set just before they fork, so they inherit it:
#: a family holds recipe functions, which cannot be sent to another process.
_SHARED: dict = {}


def _job(kind: str, arg):
    family = _SHARED["family"]
    if kind == "static":
        result = BuildResult(family.name)
        build_static(family, arg, _SHARED["out"], result, _SHARED["woff2"])
        return result
    return draw_master(family, arg)


def default_jobs() -> int:
    """How many processes a build may use: WHATEVERFONT_JOBS, or the processor count (8 at most)."""
    try:
        return max(1, int(os.environ["WHATEVERFONT_JOBS"]))
    except (KeyError, ValueError):
        return max(1, min(8, os.cpu_count() or 1))


def _run(family: Family, out_dir: Path, woff2: bool, tasks: list, jobs: int) -> list:
    """Run (kind, argument) tasks, in forked worker processes where the platform has them."""
    import multiprocessing
    _SHARED.update(family=family, out=out_dir, woff2=woff2)
    try:
        n = min(jobs, len(tasks))
        if n > 1 and "fork" in multiprocessing.get_all_start_methods() and not multiprocessing.current_process().daemon:
            from concurrent.futures import ProcessPoolExecutor
            from concurrent.futures.process import BrokenProcessPool
            try:
                with ProcessPoolExecutor(n, mp_context=multiprocessing.get_context("fork")) as pool:
                    return list(pool.map(_job, [k for k, _ in tasks], [a for _, a in tasks]))
            except (BrokenProcessPool, OSError):
                pass                      # a worker died or could not start: build in this process
        return [_job(kind, arg) for kind, arg in tasks]
    finally:
        _SHARED.clear()


def build_family(family: Family, out_dir: Path | str, variable: bool = True, woff2: bool = True,
                 styles=None, jobs: int | None = None) -> BuildResult:
    """Build every static style, and the variable font if the family has axes.

    The styles and the masters of the variable font are drawn in ``jobs``
    processes (default: :func:`default_jobs`). ``jobs=1`` builds in this process.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = BuildResult(family.name)
    style_names = list(styles or family.styles)
    with_variable = bool(variable and family.axes and not family.palettes)
    if with_variable and serif_mismatch(family):
        result.warn(serif_mismatch(family))
        with_variable = False
    tasks = [("static", s) for s in style_names]
    if with_variable:
        tasks += [("master", loc) for loc in family.masters()]
    done = _run(family, out_dir, woff2, tasks, default_jobs() if jobs is None else jobs)
    for sub in done[:len(style_names)]:
        result.files += sub.files
        result.warnings += sub.warnings
        result.notes += sub.notes
        result.statics.update(sub.statics)
        result.kerning_pairs = max(result.kerning_pairs, sub.kerning_pairs)
    if variable and family.axes and family.palettes:
        # COLR version 0 has no variations, so a variable file would lose its color without a word.
        result.note(f"{family.name} has palettes, so no variable font was built: color fonts cannot have "
                    "axes yet. Each named style is a static color font; the stylesheet points to those.")
    if with_variable:
        build_variable(family, out_dir, result, woff2, masters=done[len(style_names):])
    return result
