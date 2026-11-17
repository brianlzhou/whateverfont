"""Build the small fonts that let every family on the site show its own words in six more languages.

Run from the repository root:

    python scripts/build_page_fonts.py --east-asian DIR

The site sets some words in each family's own font: its sample, its word on the wall, its block in the
footer and the poster. When a reader picks another language, a family shows the translated words only if
its font has every letter of them (see text_langs in scripts/build_site.py). Most families have no Arabic,
Devanagari, Japanese, Chinese (Simplified or Traditional) or Korean letters, so they stay in English.

This script makes one small font for each family and each of those languages. It holds only the letters
of that family's own words in that language. The script cuts an open font of the script down to those
letters, traces their centerlines and draws them again with the family's pen and effect, as
`whateverfont retrace` does (docs/scripts.md). The fonts go to site/page-fonts/, with index.json, the
license and a README. A family that has a whole font of the script in examples/retrace gets none.

It needs the trace extra (pip install 'whateverfont[trace]'). The Arabic and Devanagari sources are in
examples/retrace. The Japanese, Chinese and Korean sources are large, so they are not in the repository:
give the folder that holds them with --east-asian (the file names are in SOURCES). The script rebuilds
only the fonts whose words, source, pen or effect changed. Use --all after a change to the engine.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import inspect
import io
import json
import re
import shutil
import sys
import tempfile
import time
import unicodedata
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "page-fonts"
RETRACE = ROOT / "examples" / "retrace"
sys.path.insert(0, str(ROOT / "src"))

from fontTools import subset as ft_subset            # noqa: E402
from fontTools.ttLib import TTFont                    # noqa: E402

from whateverfont import effects, remix, trace       # noqa: E402
from whateverfont.compile import save_woff2           # noqa: E402

_spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site)

#: Change this when the way the fonts are made changes: every font is rebuilt.
VERSION = 4
COPYRIGHT = "Copyright 2026 Brian Zhou"

#: language -> the name of its script in the font names and in index.json. "Chinese" is Simplified: the
#: first page fonts were named so, and a new name would rebuild them all.
SCRIPTS = {"ar": "Arabic", "hi": "Devanagari", "ja": "Japanese", "zh": "Chinese", "zh-Hant": "Traditional Chinese",
           "ko": "Korean"}

#: source key -> (file, the source's family name). A file without a folder is one of the East Asian
#: sources: the script looks for it in the folders given with --east-asian.
SOURCES = {
    "playpen": (RETRACE / "playpen" / "PlaypenSansArabic[wght].ttf", "Playpen Sans Arabic"),
    "noto-arabic": (RETRACE / "noto" / "NotoSansArabic-Regular.ttf", "Noto Sans Arabic"),
    "kalam": (RETRACE / "kalam" / "Kalam-Regular.ttf", "Kalam"),
    "noto-devanagari": (RETRACE / "noto" / "NotoSansDevanagari-Regular.ttf", "Noto Sans Devanagari"),
    "klee": (Path("KleeOne-Regular.ttf"), "Klee One"),
    "noto-jp": (Path("NotoSansJP-Light.otf"), "Noto Sans JP"),
    "wenkai-gb": (Path("LXGWWenKaiGB-Regular.ttf"), "LXGW WenKai GB"),
    "noto-sc": (Path("NotoSansSC-Light.otf"), "Noto Sans SC"),
    "wenkai": (Path("LXGWWenKaiTC-Regular.ttf"), "LXGW WenKai TC"),
    "noto-tc": (Path("NotoSansTC-Light.otf"), "Noto Sans TC"),
    "gaegu": (Path("Gaegu-Regular.ttf"), "Gaegu"),
    "noto-kr": (Path("NotoSansKR-Light.otf"), "Noto Sans KR"),
    # the Regular weight, for Pebble Sans, which is not traced. If it is missing, Pebble takes the Light.
    "noto-jp-regular": (Path("NotoSansJP-Regular.otf"), "Noto Sans JP"),
    "noto-sc-regular": (Path("NotoSansSC-Regular.otf"), "Noto Sans SC"),
    "noto-tc-regular": (Path("NotoSansTC-Regular.otf"), "Noto Sans TC"),
    "noto-kr-regular": (Path("NotoSansKR-Regular.otf"), "Noto Sans KR"),
}

#: A handwritten family takes a handwritten source. Every other family takes Noto Sans. Simplified Chinese
#: takes the GB release of LXGW WenKai, with mainland forms and stops; Traditional takes LXGW WenKai TC.
HAND_SOURCE = {"ar": "playpen", "hi": "kalam", "ja": "klee", "zh": "wenkai-gb", "zh-Hant": "wenkai", "ko": "gaegu"}
TYPE_SOURCE = {"ar": "noto-arabic", "hi": "noto-devanagari", "ja": "noto-jp", "zh": "noto-sc", "zh-Hant": "noto-tc",
               "ko": "noto-kr"}
REMIX_SOURCE = {"ar": ["noto-arabic"], "hi": ["noto-devanagari"], "ja": ["noto-jp-regular", "noto-jp"],
                "zh": ["noto-sc-regular", "noto-sc"], "zh-Hant": ["noto-tc-regular", "noto-tc"],
                "ko": ["noto-kr-regular", "noto-kr"]}
HANDWRITTEN = {"Last Bell", "Last Bell Snow", "Last Bell Rounds", "Starry", "Starry Initials", "Haystack",
               "Haystack Initials", "Wassail", "Wassail Initials", "Kanagawa Brush", "Cutout", "Cutout Color"}

#: Families whose words are code, figures or pictures. Their keys are left out of the translations too.
LEFT_OUT = {"Hopstep", "Hopstep Solid", "Hopstep Line", "Aviary", "Aviary Color", "Aviary Line", "Greenbar",
            "Halation", "Tally Mono", "Pinout", "Turbo"}

#: Whole fonts that another build is adding to examples/retrace. A family that has one gets no page font.
COMING = [(pen, code) for pen in ("Last Bell", "Last Bell Snow", "Neon Glow", "Gantry")
          for code in ("ja", "zh", "zh-Hant", "ko")]

#: The families of the talking demo (build() in build_site.py sets demo.big and demo.small in both).
DEMO = ("Last Bell Rounds", "Last Bell Snow")

#: Pebble Sans is not drawn with a pen: it is Inter with round corners. Its page fonts round Noto Sans.
REMIXED = {"Pebble Sans": 46.0}

#: In Han characters, kana and Hangul, many strokes share one em. A heavy pen fills them in, so there a
#: pen takes only this share of the weight it adds to the source's strokes.
DENSE = {"ja": 0.5, "zh": 0.5, "zh-Hant": 0.5, "ko": 0.6}

#: The features that a browser applies to text on its own (HarfBuzz's defaults). A page font keeps their
#: rules among its glyphs, so that Arabic letters join and Devanagari conjuncts and marks form.
SHAPING = ["abvf", "abvm", "abvs", "akhn", "blwf", "blwm", "blws", "calt", "ccmp", "cfar", "cjct", "clig", "curs",
           "dist", "fin2", "fin3", "fina", "half", "haln", "init", "isol", "kern", "liga", "ljmo", "locl", "mark",
           "med2", "medi", "mkmk", "mset", "nukt", "pref", "pres", "pstf", "psts", "rclt", "rkrf", "rlig", "rphf",
           "stch", "tjmo", "vatu", "vjmo"]


# --------------------------------------------------------------------------
# The finish of each family: the effect that its font.py puts on its letters
# --------------------------------------------------------------------------

def pointille_tone(along, across, x, y, rng):
    """The tone of Pointille's dots, as in examples/effects/font.py: lighter toward the top."""
    return 0.25 + 0.5 * y + rng.uniform(-0.3, 0.3)


def cut_sheets(recipes):
    """Cutout Color: each letter cut by hand from one sheet of painted paper (cutpaper.painted_paper).

    cutpaper chooses the sheet by the Latin letter. A letter of another script takes a sheet by its glyph
    name, so that neighbors seldom share one."""
    cutpaper = module("cutout", "cutpaper.py")

    def effect(g, ink):
        shape = cutpaper.cut(g, ink)
        effects.redraw(g, shape)
        g.layers = [(f"sheet{zlib.crc32(g.name.encode()) % 5}", shape)]
    return effects.wrapped(recipes, effect)


def typed(recipes):
    """Platen Ribbon: the ribbon of ribbon.py. On a few dense Han characters the fine grain of the edge
    folds the outline, skia-pathops fails, and the engine would leave the glyph clean. Such a glyph is
    typed again without the fine grain (the slow unevenness, the spread ink and the dry spots stay)."""
    from whateverfont.glyph import Recipe
    ribbon = module("platen", "ribbon.py").ribbon
    tries = [ribbon(recipes), ribbon(recipes, grain=0.0), ribbon(recipes, edge=0.0, grain=0.0)]
    out = recipes.copy()
    for name, rec in recipes.items():
        def fn(g, name=name):
            for i, t in enumerate(tries):
                try:
                    return t[name].fn(g)
                except Exception:
                    if i == len(tries) - 1:
                        raise
                    g.strokes, g.shapes, g.cutouts, g.layers = [], [], [], []
        out[name] = Recipe(name, fn, rec.unicode, rec.case, rec.plain or rec.fn)
    return out


def gilded(recipes, rim: float = 7.0, **options):
    """Gilt: the klimt effect of klimt.py. Its dark edge is the letter grown by ``rim`` with its counters
    kept. On some traced letters (the 어 of Noto Sans KR) the counter of the edge came back filled, a
    dark blot inside the letter, so the counters are cut out of the edge once more."""
    from whateverfont.glyph import Recipe
    from whateverfont.outline import difference
    tiled = module("gilt", "klimt.py").klimt(recipes, rim=rim, **options)
    out = recipes.copy()
    for name, rec in tiled.items():
        def fn(g, first=rec.fn):
            first(g)
            holes = [effects.reverse_contour(c) for c in effects.ink(g) if effects.contour_area(c) > 0]
            if holes and g.layers and g.layers[0][0] == "edge":
                inner = effects.erode(holes, rim) or holes
                g.layers[0] = ("edge", difference(g.layers[0][1], inner))
        out[name] = Recipe(name, fn, rec.unicode, rec.case, rec.plain)
    return out


def bridged(recipes, gap: float = 0.30, least: float = 20.0):
    """A stencil: a vertical bridge through the strokes above and below every closed counter.

    Crate places its bridges by hand for each Latin letter. effects.stencil cuts one through the whole
    height of the letter, which in a Han character would cut every stroke on that line. Here each bridge
    reaches only one stroke past its counter, so a counter is held and the rest of the character stays."""
    def effect(g, shape):
        w = max(least, gap * g.sw)
        reach = g.sw * 1.8
        for hole in (c for c in shape if effects.contour_area(c) > 0):
            x0, y0, x1, y1 = effects.contour_bounds([hole])
            cx = (x0 + x1) / 2
            g.cutouts.append(effects.rect(cx - w / 2, y0 - reach, cx + w / 2, y1 + reach))
    return effects.wrapped(recipes, effect)


#: family -> (where the effect is, its function, its options). "effects" is whateverfont.effects, "here"
#: this script, and a file name a file of the family's project. Families not named here have a pen only.
#: The options are the ones the family's font.py gives. The three Initials families decorate capitals,
#: and these scripts have none: their letters take the family's text style (painted, or plain for Wassail).
FINISH = {
    "Last Bell Snow": ("snow.py", "capped", {}),
    "Neon Glow": ("effects", "glow", {"size": 80}),
    "Starry Initials": ("starry.py", "painted", {}),
    "Starry": ("starry.py", "painted", {}),
    "Haystack Initials": ("haystack.py", "painted", {}),
    "Haystack": ("haystack.py", "painted", {}),
    "Platen Ribbon": ("here", "typed", {}),
    "Gilt": ("here", "gilded", {"circles": 1.25, "spirals": 0.85, "blocks": 1.5}),
    "Gilt Robe": ("here", "gilded", {"tile": (36.0, 62.0), "courses": (64.0, 84.0, 104.0, 124.0),
                                     "circles": 0.3, "spirals": 1.1, "blocks": 1.8, "seed": 3}),
    "Gilt Bloom": ("here", "gilded", {"tile": (30.0, 52.0), "courses": (40.0, 50.0, 60.0, 72.0),
                                      "share": (0.13, 0.06), "circles": 2.2, "spirals": 0.3, "blocks": 0.3,
                                      "seed": 5}),
    "Kanagawa": ("breaker.py", "breaker", {}),
    "Kanagawa Brush": ("breaker.py", "breaker", {"streaks": 2, "every": 132}),
    "Kanagawa Swell": ("breaker.py", "breaker", {"streaks": 3, "foam": 0.22}),
    "Cutout": ("cutpaper.py", "scissors", {}),
    "Cutout Color": ("here", "cut_sheets", {}),
    "Crate Stencil": ("here", "bridged", {"gap": 0.30, "least": 20}),
    "Crate Stencil Square": ("here", "bridged", {"gap": 0.30, "least": 20}),
    "Crate Stencil Sprayed": ("here", "bridged", {"gap": 0.45, "least": 30}),
    "Marquee": ("effects", "inline", {"width": 0.17, "rim": 0.24}),
    "Billboard": ("effects", "layered_shadow", {"dx": 34, "dy": -34}),
    "Pointille": ("effects", "dotted", {"size": 27, "colors": 5, "tone": "pointille_tone"}),
    "Meridian": ("effects", "banded", {"bands": 6}),
}

_MODULES: dict = {}


def module(project: str, file: str):
    """A Python file of an example project, loaded once, with its folder on the path for its own imports."""
    path = ROOT / "examples" / project / file
    if path not in _MODULES:
        spec = importlib.util.spec_from_file_location(f"page_fonts_{project}_{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.path.remove(str(path.parent))
        _MODULES[path] = mod
    return _MODULES[path]


def finish(family: str, project: str):
    """(a function from a recipe set to a recipe set or None, a label for the font's description, what it
    depends on: files, or the code of a function of this script)."""
    if family not in FINISH:
        return None, "", []
    where, name, options = FINISH[family]
    options = {k: (globals()[v] if k == "tone" else v) for k, v in options.items()}
    if where == "effects":
        fn, files, label = getattr(effects, name), [Path(effects.__file__)], name
    elif where == "here":
        fn = globals()[name]
        files = [inspect.getsource(fn)]
        helper = {"cut_sheets": "cutpaper.py", "typed": "ribbon.py", "gilded": "klimt.py"}.get(name)
        if helper:
            files.append(ROOT / "examples" / project / helper)
        label = {"cut_sheets": "painted_paper from cutpaper.py", "typed": "ribbon from ribbon.py",
                 "gilded": "klimt from klimt.py", "bridged": "stencil"}[name]
    else:
        fn, files = getattr(module(project, where), name), [ROOT / "examples" / project / where]
        label = f"{name} from {where}"
    files += [inspect.getsource(t) for k, t in options.items() if k == "tone"]
    return (lambda recipes: fn(recipes, **options)), label, files


class Lighter:
    """A family whose pen draws a little lighter: for scripts with many strokes in one em (see DENSE)."""

    def __init__(self, family, factor: float):
        self._family, self._factor = family, factor

    def __getattr__(self, name):
        return getattr(self._family, name)

    def params_at(self, location=None):
        p = self._family.params_at(location)
        return p.but(weight=p.weight * self._factor)


# --------------------------------------------------------------------------
# What the site sets in each family
# --------------------------------------------------------------------------

def site_families() -> list:
    """Every family on the site, in the order the site reads them: (family dict, its project folder)."""
    out = []
    for p in site.load():
        folder = site.EXAMPLES / p["id"]
        out += [(f, folder) for f in p["families"]]
    for entry in site.load_library():
        out += [(f, site.LIBRARY / entry["id"]) for f in entry["families"]]
    for f, _ in out:
        f["key"] = site.sample_key(f)             # in the site's order, so that every key is the site's
    return out


def keys_of(f: dict) -> list:
    """The keys of the texts that the site sets in family ``f``, as hero(), wall() and drops() do."""
    keys = [f["key"]]
    wall = [(w[0], w[1]) for w in site.WALL]
    if f["name"] in [w[0] for w in wall]:
        keys.append(f"word.{f['id']}")
    for name, word, *_ in site.DROPS:
        if name == f["name"]:
            keys.append(f"word.{f['id']}" if (name, word) in wall else f"block.{f['id']}")
    if f["name"] in [h[0] for h in site.HERO]:
        keys.append("poster.text")
    if f["name"] in DEMO:
        keys += ["demo.big", "demo.small"]
    return list(dict.fromkeys(keys))


def texts_of(f: dict, code: str) -> list:
    """The words the site sets in ``f`` in language ``code``. A key the translation leaves out shows nothing."""
    words = site.translations().get(code, {})
    out = []
    for key in keys_of(f):
        text = re.sub(r"<[^>]+>", " ", words.get(key) or "")
        text = unicodedata.normalize("NFC", " ".join(text.split()))
        if text:
            out.append(text)
    return out


def whole_fonts() -> set:
    """(family, language) for every family that has a whole font of the script, or borrows one."""
    have = set(COMING)
    index = site.OTHER_SCRIPTS / "fonts" / "index.json"
    if index.is_file():
        have |= {(c["pen"], c["language"]) for c in json.loads(index.read_text(encoding="utf-8"))["families"]}
    for pen, code in list(have):
        have |= {(sister, code) for sister in site.SAME_LETTERS.get(pen, [])}
    return have


def runs_of(text: str, code: str) -> list:
    """The runs of the script's own letters in ``text``. The browser sets each run in the page font on its
    own: the spaces, figures and signs between them come from the family's own font."""
    runs, cur = [], ""
    for ch in text:
        if site.in_script(ord(ch), code):
            cur += ch
        elif cur:
            runs.append(cur)
            cur = ""
    return runs + ([cur] if cur else [])


_HB: dict = {}


def shaped(path: Path, texts: list, code: str) -> list:
    """The names of the glyphs that shaping the words with the font at ``path`` reaches.

    HarfBuzz shapes each run as a browser does, and every glyph the buffer holds after each lookup is
    kept: the final ones, and the ones on the way, such as the half form inside a Devanagari conjunct.
    A page font keeps only these, so a word shapes as it does in the source and nothing else is drawn."""
    import uharfbuzz as hb
    if path not in _HB:
        _HB[path] = (hb.Font(hb.Face(hb.Blob.from_file_path(str(path)))), TTFont(str(path), lazy=True).getGlyphOrder())
    font, order = _HB[path]
    seen = set()
    for run in {r for t in texts for r in runs_of(t, code)}:
        for language in (None, code):
            buf = hb.Buffer()
            buf.add_str(run)
            buf.guess_segment_properties()
            if language:
                buf.language = language

            def message(msg, buf=buf):
                if msg.startswith(("start lookup", "end lookup")):
                    seen.update(i.codepoint for i in buf.glyph_infos)
                return True
            buf.set_message_func(message)
            hb.shape(font, buf, {})
            seen.update(i.codepoint for i in buf.glyph_infos)
    return sorted(order[g] for g in seen if 0 < g < len(order))


@dataclasses.dataclass
class Job:
    """One page font: a family in one language."""
    name: str                  # the font's family name
    family: str                # the Latin family on the site
    folder: Path               # its project
    code: str                  # the language
    source: str                # a key of SOURCES
    chars: list                # the letters it holds
    texts: list                # the words it sets
    glyphs: list = dataclasses.field(default_factory=list)      # the source's glyphs that shaping them reaches
    stamp: str = ""

    @property
    def file(self) -> str:
        return f"{site.slug(self.name)}.woff2"


def plan(find) -> tuple:
    """Every page font the site needs, and notes on the ones it cannot have."""
    jobs, notes = [], []
    whole = whole_fonts()
    for f, folder in site_families():
        if f["name"] in LEFT_OUT:
            continue
        for code in SCRIPTS:
            if (f["name"], code) in whole:
                continue
            texts = texts_of(f, code)
            chars = sorted({c for t in texts for c in t if site.in_script(ord(c), code)})
            if not chars:
                continue
            if f["name"] in REMIXED:
                keys = REMIX_SOURCE[code]
                key = next((k for k in keys if find(k) is not None), keys[-1])
            else:
                key = (HAND_SOURCE if f["name"] in HANDWRITTEN else TYPE_SOURCE)[code]
            path = find(key)
            if path is not None:
                cmap = TTFont(path, lazy=True).getBestCmap()
                missing = [c for c in chars if ord(c) not in cmap]
                other = TYPE_SOURCE[code] if key == HAND_SOURCE[code] else HAND_SOURCE[code]
                if missing and find(other) is not None:
                    notes.append(f"{f['name']} ({code}): {SOURCES[key][1]} lacks {''.join(missing)}; "
                                 f"using {SOURCES[other][1]}")
                    key = other
            # the Latin letters, figures and signs of the words come from the family's own font
            latin = {cp for cp in f.get("codepoints", [])}
            short = sorted({c for t in texts for c in t if not site.in_script(ord(c), code) and not c.isspace()
                            and ord(c) not in latin})
            if short and f.get("codepoints"):
                notes.append(f"{f['name']} ({code}): its own font lacks {' '.join(short)}, so its words stay "
                             "in English even with a page font")
            job = Job(f"{f['name']} Page {SCRIPTS[code]}", f["name"], folder, code, key, chars, texts)
            if find(key) is not None:
                job.glyphs = shaped(find(key), texts, code)
            job.stamp = stamp(job, find)
            jobs.append(job)
    return jobs, notes


def _digest(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12] if path.is_file() else "-"


def stamp(job: Job, find) -> str:
    """What the font depends on. A font whose stamp is unchanged is not built again."""
    src = find(job.source)
    files = [job.folder / "font.py"] + (finish(job.family, job.folder.name)[2] if job.family in FINISH else [])
    data = [VERSION, job.name, job.code, job.texts, job.source,
            src.stat().st_size if src is not None else None,
            [(p.name, _digest(p)) if isinstance(p, Path) else hashlib.sha1(p.encode()).hexdigest()[:12]
             for p in files],
            repr(FINISH.get(job.family)), REMIXED.get(job.family), DENSE.get(job.code)]
    return hashlib.sha1(json.dumps(data, ensure_ascii=False).encode()).hexdigest()[:16]


# --------------------------------------------------------------------------
# Cutting, tracing and drawing
# --------------------------------------------------------------------------

def _named(font: TTFont):
    """Keep the glyph names when the font is saved: the traced glyphs are found by name."""
    if "glyf" in font:
        post = font["post"]
        post.formatType = 2.0
        post.extraNames = []
        post.mapping = {}


def cut(font: TTFont, chars, glyphs) -> TTFont:
    """A copy of ``font`` with only ``chars`` and ``glyphs``, and the shaping rules among them.

    The subsetter's own closure would keep every glyph that any mix of these letters can reach: in
    Devanagari every conjunct of every pair of them. Only the glyphs that the words reach are kept."""
    buf = io.BytesIO()
    _named(font)
    font.save(buf)
    buf.seek(0)
    out = TTFont(buf)
    have = set(out.getGlyphOrder())
    opts = ft_subset.Options()
    opts.layout_closure = False
    opts.layout_features = SHAPING
    opts.layout_scripts = ["*"]
    opts.glyph_names = True
    opts.notdef_outline = True
    opts.name_IDs = ["*"]
    opts.name_languages = ["*"]
    opts.name_legacy = True
    opts.hinting = False
    opts.prune_unicode_ranges = True
    sub = ft_subset.Subsetter(opts)
    sub.populate(unicodes=[ord(c) for c in chars], glyphs=[g for g in glyphs if g in have])
    sub.subset(out)
    # A kept glyph keeps every code point that maps to it: the Kangxi radicals of Noto Sans CJK share
    # their glyphs with the ideographs, and Kalam maps its conjuncts to private code points. The font
    # maps only its own letters.
    wanted = {ord(c) for c in chars}
    for table in out["cmap"].tables:
        if table.format != 14:
            table.cmap = {cp: g for cp, g in table.cmap.items() if cp in wanted}
    _named(out)
    for tag in out.keys():
        out[tag]
    return out


def load_source(path: Path, key: str = "") -> TTFont:
    font = TTFont(str(path))
    if "fvar" in font:
        from fontTools.varLib import instancer
        font = instancer.instantiateVariableFont(font, {a.axisTag: a.defaultValue for a in font["fvar"].axes})
    return font


def narrowed(traced, job: Job) -> object:
    """The traced font cut down to one job's letters: the traces are the same, the glyphs fewer."""
    font = cut(traced.font, job.chars, job.glyphs)
    keep = set(font.getGlyphOrder())
    return dataclasses.replace(
        traced, font=font, glyphs={n: g for n, g in traced.glyphs.items() if n in keep},
        sources={n: s for n, s in traced.sources.items() if n in keep},
        composites=[n for n in traced.composites if n in keep], marks={n for n in traced.marks if n in keep},
        failed={n: e for n, e in traced.failed.items() if n in keep})


def describe(job: Job, label: str) -> str:
    src = SOURCES[job.source][1]
    how = f"the pen of {job.family}" + (f" and the effect {label}" if label else "")
    return (f"The letters of {src} that the WhateverFont site needs for the words it sets in {job.family} in "
            f"{SCRIPTS[job.code]} script, traced along their centerlines and redrawn with {how}. The letter "
            f"shapes and the shaping are the work of the authors of {src}; this modified version is "
            "distributed under the same license.")


def draw(job: Job, traced, work: Path, jobs: int | None) -> tuple:
    """Draw one page font from the trace of its source. Returns (the WOFF2, notes)."""
    family = trace.load_family(f"{job.folder}:{job.family}")
    fn, label, _ = finish(job.family, job.folder.name)
    small = narrowed(traced, job)
    notes = []
    if job.code in DENSE:
        pen = trace.make_pen(small, family.params_at(family.default_location()))
        if pen.stem > pen.width:
            target = pen.width + (pen.stem - pen.width) * DENSE[job.code]
            family = Lighter(family, target / pen.stem)
    res = trace.redraw(small, work / site.slug(job.name), job.name, family, fn, copyright=COPYRIGHT,
                       description=describe(job, label), effect_label=label, jobs=jobs)
    for n, problems in res.flagged.items():
        notes.append(f"{n}: {'; '.join(problems)}")
    for n, e in res.plain.items():
        notes.append(f"{n}: the effect failed, drawn plain ({e})")
    for n, e in res.failed.items():
        notes.append(f"{n}: failed ({e})")
    return res.woff2, notes


def round_off(job: Job, path: Path, work: Path) -> tuple:
    """Pebble Sans: the source's own outlines with round corners (whateverfont remix), not a pen."""
    tmp = work / f"{site.slug(job.name)}-cut.ttf"
    cut(load_source(path), job.chars, job.glyphs).save(tmp)
    trace.open_font(tmp).save(tmp)               # TrueType outlines, which remix needs
    ttf = remix.remix_file(tmp, work / site.slug(job.name), job.name, round_=REMIXED[job.family])
    out = TTFont(ttf)
    names = out["name"]
    copyright_line = (names.getDebugName(0) or "").strip().rstrip(".")
    # As retrace does: Windows records in English only, and the source's trademark does not travel with
    # the new font. The license records stay in every language.
    names.names = [r for r in names.names if r.platformID == 3 and r.nameID != 7
                   and (r.langID == 0x409 or r.nameID in (13, 14))]
    names.setName(f"{copyright_line}. {COPYRIGHT} (the rounding).", 0, 3, 1, 0x409)
    out.save(ttf)
    return save_woff2(ttf, ttf.parent / "woff2"), []


# --------------------------------------------------------------------------
# The folder: fonts, index, license, proofs
# --------------------------------------------------------------------------

def read_index() -> dict:
    path = OUT / "index.json"
    if not path.is_file():
        return {}
    return {c["name"]: c for c in json.loads(path.read_text(encoding="utf-8"))["families"]}


def entry(job: Job, woff2: Path, source_copyright: str) -> dict:
    cps = sorted(TTFont(woff2).getBestCmap())
    return {"name": job.name, "language": job.code, "script": SCRIPTS[job.code], "source": SOURCES[job.source][1],
            "source_copyright": source_copyright, "pen": job.family,
            "effect": finish(job.family, job.folder.name)[1] if job.family not in REMIXED else
            f"round {REMIXED[job.family]:g}", "words": job.texts, "woff2": {"Regular": job.file},
            "codepoints": cps, "stamp": job.stamp}


def write_license(entries: list):
    """OFL.txt: the copyright line of every source used, and the license."""
    body = (RETRACE / "OFL.txt").read_text(encoding="utf-8")
    body = body[body.index("This Font Software is licensed"):]
    lines = sorted({f"{c['source_copyright']} ({c['source']})" for c in entries})
    lines.append(f"{COPYRIGHT} (the redrawing and the rounding: {site.REPO})")
    (OUT / "OFL.txt").write_text("\n".join(lines) + "\n\n" + body, encoding="utf-8")


def proof(entries: list, folder: Path):
    """One HTML sheet for each language: every family's words in its own font and its page font."""
    folder.mkdir(parents=True, exist_ok=True)
    fams = {f["name"]: f for f, _ in site_families()}
    for code in SCRIPTS:
        rows, faces = [], []
        for c in [c for c in entries if c["language"] == code]:
            f = fams[c["pen"]]
            fid = f["id"]
            cps = [cp for cp in c["codepoints"] if site.in_script(cp, code)]
            own, page = f["web"].resolve().as_uri(), (OUT / c["woff2"]["Regular"]).as_uri()
            faces.append(f'@font-face {{ font-family: "pf-{fid}"; src: url("{own}"); }}')
            faces.append(f'@font-face {{ font-family: "pf-{fid}"; src: url("{page}"); '
                         f'unicode-range: {site.unicode_range(cps)}; }}')
            style = f'font-family: "pf-{fid}", "Courier New", monospace;'
            ground, ink = "#FFFFFF", "#1B1A17"
            if f["palettes"]:
                faces.append(f'@font-palette-values --pf-{fid} {{ font-family: "pf-{fid}"; base-palette: 0; }}')
                style += f" font-palette: --pf-{fid};"
                ground, ink = site.ground_of(f, f["palettes"][0])
            words = " · ".join(f'<span>{site.e(t)}</span>' for t in c["words"])
            rows.append(f'<div class="row" style="background: {ground}; color: {ink}">'
                        f'<p class="name">{site.e(c["pen"])} <small>{site.e(c["source"])}'
                        f'{", " + site.e(c["effect"]) if c["effect"] else ""}</small></p>'
                        f'<p class="words" lang="{code}" dir="{"rtl" if code == "ar" else "ltr"}" '
                        f"style='{style}'>{words}</p></div>")
        page = (f'<!doctype html><meta charset="utf-8"><title>Page fonts: {SCRIPTS[code]}</title><style>\n'
                + "\n".join(faces) + "\nbody { margin: 0; font: 13px system-ui, sans-serif; background: #ddd; }"
                ".row { padding: 10px 18px 14px; border-bottom: 1px solid #0002; }"
                ".name { margin: 0 0 4px; opacity: .75 } .words { margin: 0; font-size: 72px; line-height: 1.3; }"
                "</style>\n" + "\n".join(rows))
        (folder / f"{code}.html").write_text(page, encoding="utf-8")
        print(f"proof: {folder / f'{code}.html'}")


# --------------------------------------------------------------------------

def finder(folders: list):
    """A function from a source key to its file, or None if it is not here."""
    cache = {}

    def find(key: str):
        if key not in cache:
            path = SOURCES[key][0]
            if path.is_absolute():
                cache[key] = path if path.is_file() else None
            else:
                cache[key] = next((p for d in folders for p in sorted(Path(d).rglob(path.name))), None)
        return cache[key]
    return find


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--east-asian", action="append", default=[], metavar="DIR",
                    help="a folder that holds the Japanese, Chinese and Korean sources (searched with its subfolders)")
    ap.add_argument("--all", action="store_true", help="rebuild every font, changed or not")
    ap.add_argument("--only", action="append", default=[], metavar="FAMILY", help="build only this family")
    ap.add_argument("--lang", action="append", default=[], choices=list(SCRIPTS), help="build only this language")
    ap.add_argument("--list", action="store_true", help="say what would be built, and build nothing")
    ap.add_argument("--proof", metavar="DIR", help="write an HTML proof sheet for each language into DIR")
    ap.add_argument("--jobs", type=int, default=None, help="worker processes (default: one for each core)")
    args = ap.parse_args(argv)

    find = finder(args.east_asian)
    jobs, notes = plan(find)
    for n in notes:
        print(f"note: {n}")
    old = read_index()
    chosen = [j for j in jobs if (not args.only or j.family in args.only) and (not args.lang or j.code in args.lang)]
    todo = [j for j in chosen if args.all or j.name not in old or old[j.name].get("stamp") != j.stamp
            or not (OUT / j.file).is_file()]
    missing = sorted({j.source for j in todo if find(j.source) is None})
    for key in missing:
        print(f"note: {SOURCES[key][0].name} ({SOURCES[key][1]}) is not in the --east-asian folders: "
              "its fonts are kept as they are")
    todo = [j for j in todo if find(j.source) is not None]
    print(f"{len(jobs)} page fonts on the site, {len(todo)} to build")
    for j in todo:
        print(f"  {j.name}: {SOURCES[j.source][1]}, {len(j.chars)} letters")
    if args.list:
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    built = {}
    groups = {}
    for j in todo:
        groups.setdefault((j.code, j.source, j.family in REMIXED), []).append(j)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for (code, key, remixed), group in groups.items():
            path = find(key)
            copyright_line = (TTFont(path, lazy=True)["name"].getDebugName(0) or "").strip()
            t0 = time.time()
            traced = None
            if not remixed:
                # One trace for every family of this source and language: a few hundred letters find the
                # height of the joins (Arabic) or of the headline (Devanagari) better than a few.
                sharing = [j for j in jobs if j.code == code and j.source == key and j.family not in REMIXED]
                union = sorted({c for j in sharing for c in j.chars})
                cut_path = work / f"{key}-{code}.ttf"
                cut(load_source(path, key), union, sorted({g for j in sharing for g in j.glyphs})).save(cut_path)
                traced = trace.trace_font(cut_path, jobs=args.jobs)
                print(f"{SOURCES[key][1]} ({code}): traced {len(traced.glyphs)} glyphs for {len(union)} letters "
                      f"in {traced.seconds:.1f}s")
                for w in traced.warnings:
                    print(f"  warning: {w}")
            for j in group:
                t1 = time.time()
                woff2, problems = round_off(j, path, work) if remixed else draw(j, traced, work, args.jobs)
                shutil.copyfile(woff2, OUT / j.file)
                built[j.name] = entry(j, OUT / j.file, copyright_line)
                print(f"  {j.name}: {(OUT / j.file).stat().st_size / 1000:.0f} KB, {len(problems)} flagged, "
                      f"{time.time() - t1:.1f}s")
                for p in problems:
                    print(f"    warning: {p}")
            print(f"  ({time.time() - t0:.0f}s)")

    # The index: what was built, and the fonts kept from before. A font the site no longer needs goes,
    # unless this run was limited to some families or languages, or could not see its source.
    planned = {j.name for j in jobs}
    limited = bool(args.only or args.lang)
    entries = []
    for j in jobs:
        if j.name in built:
            entries.append(built[j.name])
        elif j.name in old and (OUT / j.file).is_file():
            entries.append(old[j.name])
    if limited or missing:
        entries += [c for n, c in old.items() if n not in planned and (OUT / c["woff2"]["Regular"]).is_file()]
    else:
        for c in old.values():
            if c["name"] not in planned:
                (OUT / c["woff2"]["Regular"]).unlink(missing_ok=True)
                print(f"removed {c['woff2']['Regular']}: the site no longer needs it")
    order = {code: i for i, code in enumerate(SCRIPTS)}
    entries.sort(key=lambda c: (order[c["language"]], c["name"]))
    (OUT / "index.json").write_text(json.dumps({"families": entries}, indent=1, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    write_license(entries)
    total = sum((OUT / c["woff2"]["Regular"]).stat().st_size for c in entries)
    print(f"index: {OUT / 'index.json'} ({len(entries)} fonts, {total / 1e6:.2f} MB)")
    if args.proof:
        proof(entries, Path(args.proof))
    return 0


if __name__ == "__main__":
    sys.exit(main())
