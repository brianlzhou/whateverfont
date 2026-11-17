"""Retrace: four whateverfont families in Arabic, Devanagari, Japanese, Simplified and Traditional Chinese and
Korean, drawn over the centerlines of open fonts.

Run from the repository root:  python examples/retrace/build.py [SCRIPT ...]
A script is Arabic, Devanagari, Japanese, Chinese (Simplified), Traditional (or "Traditional Chinese") or
Korean. It needs the trace extra (pip install 'whateverfont[trace]'). It writes fonts/<Family>/ttf, woff2
and a CSS file for each family, fonts/index.json, and proofs in proofs/.

The letter shapes come from the source fonts, all under the SIL Open Font License 1.1: this project traces
their centerlines and keeps their shaping tables. The pens and the effects are whateverfont's. Each family
gets the source that suits it: the marker letters of Last Bell are traced from handwriting (Kalam, Playpen
Sans Arabic, Klee One, LXGW WenKai GB and TC, Gaegu), the technical Gantry and the tube of Neon Glow from
Noto Sans.

The Arabic and Devanagari sources are in the repository. The Japanese, Chinese and Korean ones are 3 to 26 MB
each: sources.json lists where they come from and their SHA-256, and a missing one is fetched into
.cache/sources/ (which git ignores) and checked.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

from whateverfont import charsets, proof, trace
from whateverfont.compile import slug
from whateverfont.project import grounds

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
CACHE = HERE / ".cache" / "sources"

#: source key -> (file, name), for the sources kept in the repository
SOURCES = {
    "noto-arabic": ("noto/NotoSansArabic-Regular.ttf", "Noto Sans Arabic"),
    "noto-devanagari": ("noto/NotoSansDevanagari-Regular.ttf", "Noto Sans Devanagari"),
    "playpen": ("playpen/PlaypenSansArabic[wght].ttf", "Playpen Sans Arabic"),
    "kalam": ("kalam/Kalam-Regular.ttf", "Kalam"),
}

#: source key -> its entry in sources.json, for the sources fetched on demand
FETCHED = {s["key"]: s for s in json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]}

#: script -> (the sample: the site's tagline in that language, its language tag)
SCRIPTS = {
    "Arabic": ("الخط الذي تريده، أيًّا كان.", "ar"),
    "Devanagari": ("जैसा फ़ॉन्ट चाहें, वैसा पाएँ।", "hi"),
    "Japanese": ("どんなフォントでも、思いのままに。", "ja"),
    "Chinese": ("想要什么字体，就有什么字体。", "zh"),
    "Traditional Chinese": ("想要什麼字型，就有什麼字型。", "zh-Hant"),
    "Korean": ("어떤 폰트든 원하는 대로.", "ko"),
}

#: The name of a script in index.json and on the site, where it is not the one in the font's name. The
#: Simplified fonts kept their first names ("Last Bell Chinese").
LABEL = {"Chinese": "Simplified Chinese"}

#: Simplified Chinese is traced from the GB release of LXGW WenKai, with the forms and the stops of mainland
#: China. Traditional Chinese is traced from LXGW WenKai TC, with Taiwan's forms and its centered stops.
HAND = {"Arabic": "playpen", "Devanagari": "kalam", "Japanese": "klee", "Chinese": "lxgw-gb",
        "Traditional Chinese": "lxgw", "Korean": "gaegu"}
TYPE = {"Arabic": "noto-arabic", "Devanagari": "noto-devanagari", "Japanese": "noto-jp", "Chinese": "noto-sc",
        "Traditional Chinese": "noto-tc", "Korean": "noto-kr"}

#: the characters a font of a script keeps (see whateverfont.charsets); a script not named keeps every glyph
ONLY = {"Japanese": "japanese", "Chinese": "chinese", "Traditional Chinese": "traditional", "Korean": "korean"}

#: the corners the committed Arabic and Devanagari fonts were built with
CORNERS = {"Arabic": "sharp", "Devanagari": "sharp"}

#: Snow on the thinner strokes of Chinese characters and Hangul lies shallower, so the letter's color shows,
#: and has no drips: a lump under a stroke reads as a dot, which is a stroke of its own (大, 犬).
SNOW_CJK = "lastbell/snow.py:capped:depth=44,drips=0"
#: A narrower glow for the same scripts: a wide one fills the white between their strokes.
GLOW_CJK = "glow:size=40"

#: (the Latin family, its project, the source for each script, the effect, the effect for a script if it differs)
PENS = [
    ("Last Bell", "lastbell", HAND, None, {}),
    # Snow on a Devanagari headline lies shallower, so the letter's color still shows under it.
    ("Last Bell Snow", "lastbell", HAND, "lastbell/snow.py:capped",
     {"Devanagari": "lastbell/snow.py:capped:depth=72", "Japanese": SNOW_CJK, "Chinese": SNOW_CJK,
      "Traditional Chinese": SNOW_CJK, "Korean": SNOW_CJK}),
    ("Neon Glow", "neon", TYPE, "glow:size=80", {"Japanese": GLOW_CJK, "Chinese": GLOW_CJK,
                                                 "Traditional Chinese": GLOW_CJK, "Korean": GLOW_CJK}),
    ("Gantry", "caliper", TYPE, None, {}),
]

COPYRIGHT = "Copyright 2026 Brian Zhou"
REDRAWING = f"{COPYRIGHT} (the redrawing: https://github.com/brianlzhou/whateverfont)"

PROOF_TEXT = {
    "Arabic": ["الخط الذي تريده، أيًّا كان.", "«ممتاز. الآن ضع عليه ثلجًا.»",
               "ب ت ث ج ح خ س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي ة ى ٠١٢٣٤٥٦٧٨٩"],
    "Devanagari": ["जैसा फ़ॉन्ट चाहें, वैसा पाएँ।", "“एकदम सही। अब इस पर बर्फ़ डाल दो।”",
                   "क ख ग घ ङ च छ ज झ ञ ट ठ ड ढ ण त थ द ध न प फ ब भ म य र ल व श ष स ह",
                   "क्ष त्र ज्ञ श्र द्ध ह्म क्त स्त्र र्क ०१२३४५६७८९"],
    "Japanese": ["どんなフォントでも、思いのままに。", "「最高。では、雪を降らせて。」",
                 "あいうえお かきくけこ がぎぐげご ぱぴぷぺぽ", "アイウエオ ガギグゲゴ パピプペポ ー・",
                 "冬休みの雪 意想要議曜機警 書類"],
    "Chinese": ["想要什么字体，就有什么字体。", "“完美。现在给它下点雪。”",
                "一二三四五六七八九十 人大天中国", "意要赢量疆镶餐燃 警衡德戴 囊颤"],
    "Traditional Chinese": ["想要什麼字型，就有什麼字型。", "「完美。現在幫它加點雪。」",
                            "一二三四五六七八九十 人大天中國", "臺灣 鬱讓廳體驗 龜鑼囊顫"],
    "Korean": ["어떤 폰트든 원하는 대로.", "“완벽해. 이제 눈을 내려 줘.”",
               "가나다라마바사아자차카타파하", "원영웅흥꽃잉쬐 괜찮아요 읽을 흙"],
}

OFL_BODY = (HERE / "noto" / "OFL.txt").read_text(encoding="utf-8").split("This Font Software is licensed", 1)[1]

def code_ranges(ttf) -> str:
    """The characters of a font as hexadecimal ranges: "20 A0 3041-3096"."""
    from fontTools.ttLib import TTFont
    runs = []
    for cp in sorted(TTFont(str(ttf), lazy=True).getBestCmap()):
        if runs and cp == runs[-1][1] + 1:
            runs[-1][1] = cp
        else:
            runs.append([cp, cp])
    return " ".join(f"{a:X}" if a == b else f"{a:X}-{b:X}" for a, b in runs)


def source_path(key: str) -> Path:
    """The file of a source: in the repository, or in the cache, fetched and checked if it is missing."""
    if key in SOURCES:
        return HERE / SOURCES[key][0]
    entry = FETCHED[key]
    path = CACHE / entry["file"]
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"fetching {entry['name']} from {entry['url']}")
        part = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(entry["url"], timeout=120) as response, open(part, "wb") as out:
            shutil.copyfileobj(response, out)
        part.replace(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"{path} is not the file sources.json names (its SHA-256 is {digest}, not "
                         f"{entry['sha256']}). Delete it to fetch it again; if the file changed upstream, check "
                         "the new one and update sources.json")
    return path


def source_name(key: str) -> str:
    return SOURCES[key][1] if key in SOURCES else FETCHED[key]["name"]


def write_license(key: str, folder: Path):
    """The Open Font License travels with a modified font: the source's copyright lines, ours, and the text."""
    lines = [FETCHED[key]["copyright"] + f" ({FETCHED[key]['name']})", REDRAWING]
    (folder / "OFL.txt").write_text("\n".join(lines) + "\n\nThis Font Software is licensed" + OFL_BODY,
                                    encoding="utf-8")


def effect_for(spec: str | None):
    if spec is None:
        return None, ""
    if ".py:" in spec:
        spec = str(EXAMPLES / spec)
    return trace.load_effect(spec)


def wanted(script: str, asked: set) -> bool:
    """True if the command line asks for ``script``: "Traditional Chinese", "TraditionalChinese" or "Traditional"."""
    key = script.replace(" ", "").lower()
    return not asked or key in asked or key.removesuffix("chinese") in asked


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=" ".join(__doc__.split("\n\n")[0].split()))
    ap.add_argument("scripts", nargs="*", help="build only these scripts (default: all)")
    ap.add_argument("--family", action="append", default=[], metavar="NAME",
                    help="build only the fonts of this Latin family (Last Bell, Last Bell Snow, Neon Glow, Gantry)")
    args = ap.parse_args(argv)
    only = {a.replace(" ", "").lower() for a in args.scripts}
    pens = [pen for pen in PENS if not args.family or pen[0] in args.family]
    if not pens:
        raise SystemExit(f"no family named {args.family}: the families are {', '.join(p[0] for p in PENS)}")
    fonts = HERE / "fonts"
    proofs = HERE / "proofs"
    fonts.mkdir(exist_ok=True)
    proofs.mkdir(exist_ok=True)
    rel = lambda p: str(Path(p).relative_to(HERE))
    traced = {}
    index = []
    for script, (sample, lang) in SCRIPTS.items():
        if not wanted(script, only):
            continue
        script_label = LABEL.get(script, script)
        built = []
        for latin, folder, sources, effect, per_script in pens:
            key = sources[script]
            src_name = source_name(key)
            if (key, script) not in traced:
                keep = None
                if script in ONLY:
                    keep = charsets.named(ONLY[script]) | {ord(c) for c in sample}
                traced[key, script] = trace.trace_font(source_path(key), only=keep,
                                                       corners=CORNERS.get(script, "auto"))
                t = traced[key, script]
                print(f"{src_name}: traced {len(t.glyphs)} glyphs ({len(t.composites)} composites kept) "
                      f"in {t.seconds:.1f}s" + (f", {t.corners} corners" if t.cjk else ""))
                for w in t.warnings:
                    print(f"  warning: {w}")
                proof.compare([(t.path, {}, f"{src_name}, the source" if i == 0 else "")
                               for i in range(len(PROOF_TEXT[script]))],
                              proofs / f"{slug(src_name)}.png", PROOF_TEXT[script], px=64, per_row_text=True)
            t = traced[key, script]
            family = trace.load_family(f"{EXAMPLES / folder}:{latin}")
            fn, label = effect_for(per_script.get(script, effect))
            name = f"{latin} {script}"
            t0 = time.time()
            res = trace.redraw(t, fonts / slug(name), name, family, fn, copyright=COPYRIGHT, effect_label=label)
            took = time.time() - t0
            if key in FETCHED:
                write_license(key, fonts / slug(name))
            print(f"  {name}: {len(res.flagged)} of {res.traced} glyphs flagged, {len(res.plain)} without the "
                  f"effect, {len(res.failed)} failed, {took:.1f}s")
            for n in res.notes:
                print(f"    note: {n}")
            chars = {}
            for cp, n in sorted((t.font.getBestCmap() or {}).items()):
                chars.setdefault(n, chr(cp))
            for n, problems in res.flagged.items():
                print(f"    warning: {n}{' ' + chars[n] if n in chars else ''}: {'; '.join(problems)}")
            for n, e in res.plain.items():
                print(f"    warning: {n}: the effect failed ({e})")
            for n, e in res.failed.items():
                print(f"    warning: {n}: left empty ({e})")
            colored = fn is not None and bool(family.palettes)
            index.append({
                "name": name,
                "description": f"{script_label} {'characters' if script in ONLY else 'letters'} traced from {src_name} "
                               f"and drawn with the pen of {latin}. "
                               f"{family.description}",
                "sample": sample,
                "language": lang,
                "script": script_label,
                "source": src_name,
                "pen": latin,
                "pen_project": folder,
                "styles": ["Regular"],
                "palettes": list(family.palettes) if colored else [],
                "grounds": grounds(family) if colored else {},
                "axes": [],
                "glyphs": len(t.font.getGlyphOrder()),
                "traced": res.traced,
                "flagged": len(res.flagged),
                "license": "OFL-1.1",
                "css": rel(res.css),
                "ttf": {"Regular": rel(res.ttf)},
                "woff2": {"Regular": rel(res.woff2)},
                # the site reads the characters from here: the large TTF files are not in the repository
                "codepoints": code_ranges(res.ttf),
                "variable": None,
            })
            look = {}
            if colored:
                palette = next(iter(family.palettes))
                look = {"palette": palette, "paper": grounds(family).get(palette, proof.PAPER)}
            lines = PROOF_TEXT[script]
            proof.compare([(res.ttf, {}, name if i == 0 else "") for i in range(len(lines))],
                          proofs / f"{slug(name)}.png", lines, px=64, per_row_text=True, **look)
            flagged = "".join(chars[n] for n in res.flagged if n in chars and chars[n].isprintable())[:24]
            if script in ONLY and flagged:
                # the characters the self-check flags, under their source, to look at first
                halves = [flagged[:12], flagged[12:]] if len(flagged) > 12 else [flagged]
                rows = [row for i in range(len(halves)) for row in
                        ((t.path, {}, f"{src_name}: the characters flagged in {name}" if i == 0 else ""),
                         (res.ttf, {}, name if i == 0 else ""))]
                proof.compare(rows, proofs / f"{slug(name)}-flagged.png", [h for h in halves for _ in range(2)],
                              px=64, per_row_text=True, **look)
            built.append((res.ttf, name, look))
        if script in ONLY:
            # the two sources and the four families, for a reader of the script. A family not built this
            # time shows the font it has from before.
            fonts_of = {n: f for f, n, _ in built}

            def font_of(latin):
                name = f"{latin} {script}"
                return fonts_of.get(name) or fonts / slug(name) / "ttf" / f"{slug(name)}-Regular.ttf"

            def source_of(key):
                return traced[key, script].path if (key, script) in traced else source_path(key)

            rows = [(source_of(HAND[script]), f"{source_name(HAND[script])} (the source of Last Bell)")]
            rows += [(font_of(latin), f"{latin} {script}") for latin in ("Last Bell", "Last Bell Snow")]
            rows += [(source_of(TYPE[script]), f"{source_name(TYPE[script])} (the source of Neon Glow and Gantry)")]
            rows += [(font_of(latin), f"{latin} {script}") for latin in ("Neon Glow", "Gantry")]
            rows = [(f, caption) for f, caption in rows if Path(f).is_file()]
            picked = [PROOF_TEXT[script][0], PROOF_TEXT[script][-1]]
            proof.compare([(f, {}, caption if i == 0 else "") for f, caption in rows for i in range(len(picked))],
                          proofs / f"{slug(script).lower()}-families.png", [t for _ in rows for t in picked],
                          px=64, per_row_text=True)
    if only or args.family:
        try:
            old = json.loads((fonts / "index.json").read_text())["families"]
        except (OSError, ValueError, KeyError):
            old = []
        built_names = {f["name"] for f in index}
        index = [f for f in old if f["name"] not in built_names] + index
    order = [f"{latin} {script}" for script in SCRIPTS for latin, *_ in PENS]
    index.sort(key=lambda f: order.index(f["name"]) if f["name"] in order else len(order))
    (fonts / "index.json").write_text(json.dumps({"families": index}, indent=1, ensure_ascii=False) + "\n")
    print(f"index: {fonts / 'index.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
