"""The page's own small fonts: site/page-fonts, made by scripts/build_page_fonts.py.

Each one holds the letters of the words that the site sets in one family in one language, so that the
family can show those words in Arabic, Devanagari, Japanese, Chinese or Korean.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


fonts = _load("build_page_fonts", ROOT / "scripts" / "build_page_fonts.py")
site = fonts.site
FOLDER = site.PAGE_FONTS
INDEX = json.loads((FOLDER / "index.json").read_text(encoding="utf-8"))["families"] \
    if (FOLDER / "index.json").is_file() else []

pytestmark = pytest.mark.skipif(not INDEX, reason="no page fonts are built")


@pytest.fixture(scope="module")
def families():
    return {f["name"]: f for f, _ in fonts.site_families()}


def test_every_file_is_there_and_every_name_is_its_own():
    names = [c["name"] for c in INDEX]
    assert len(set(names)) == len(names)
    assert len({site.slug(n) for n in names}) == len(names)       # the site names the web file after it
    files = [c["woff2"]["Regular"] for c in INDEX]
    assert all((FOLDER / f).is_file() for f in files)
    assert sorted(p.name for p in FOLDER.glob("*.woff2")) == sorted(files)     # no font that nothing uses
    assert (FOLDER / "OFL.txt").is_file() and (FOLDER / "README.md").is_file()


def test_every_pen_is_a_family_of_the_site(families):
    assert {c["pen"] for c in INDEX} <= set(families)
    assert not {c["pen"] for c in INDEX} & fonts.LEFT_OUT


def test_every_letter_belongs_to_the_script_of_its_language():
    for c in INDEX:
        assert c["language"] in fonts.SCRIPTS and c["script"] == fonts.SCRIPTS[c["language"]]
        cps = c["codepoints"]
        assert cps and cps == sorted(set(cps))
        wrong = [f"U+{cp:04X}" for cp in cps if not site.in_script(cp, c["language"])]
        assert not wrong, f"{c['name']}: {wrong}"


def test_no_page_font_stands_in_for_a_whole_font():
    whole = site.OTHER_SCRIPTS / "fonts" / "index.json"
    have = {(c["pen"], c["language"]) for c in json.loads(whole.read_text(encoding="utf-8"))["families"]}
    for pen, code in list(have):
        have |= {(sister, code) for sister in site.SAME_LETTERS.get(pen, [])}
    assert not [c["name"] for c in INDEX if (c["pen"], c["language"]) in have]


def test_each_font_maps_exactly_its_letters():
    for c in INDEX:
        font = TTFont(FOLDER / c["woff2"]["Regular"])
        assert sorted(font.getBestCmap()) == c["codepoints"], c["name"]
        records = font["name"].names
        names = {r.nameID: r.toUnicode() for r in records if r.platformID == 3 and r.langID == 0x409}
        # the new name in every language, and nothing of the source's name or trademark
        assert {r.toUnicode() for r in records if r.nameID in (1, 16)} == {c["name"]}, c["name"]
        assert not [r for r in records if r.nameID == 7]
        # a modified version of an open font keeps its copyright and its license
        assert c["source_copyright"].rstrip(".") in names[0] and "Open Font License" in names[13]


def test_every_word_shapes_with_no_missing_glyph():
    """The font keeps the glyphs that shaping its words reaches (joined Arabic forms, conjuncts), not only
    the letters: each run of the script's letters shapes with no empty box."""
    hb = pytest.importorskip("uharfbuzz")
    import io
    for c in INDEX:
        font = TTFont(FOLDER / c["woff2"]["Regular"])
        font.flavor = None
        buf = io.BytesIO()
        font.save(buf)
        shaper = hb.Font(hb.Face(hb.Blob(buf.getvalue())))
        for text in c["words"]:
            for run in fonts.runs_of(text, c["language"]):
                b = hb.Buffer()
                b.add_str(run)
                b.guess_segment_properties()
                hb.shape(shaper, b, {})
                assert all(i.codepoint for i in b.glyph_infos), f"{c['name']}: {run}"


def test_every_family_has_the_letters_of_its_translated_words(families):
    """A family that sets translated words in a script has a page font with all their letters, or a whole font."""
    built = {(c["pen"], c["language"]): set(c["codepoints"]) for c in INDEX}
    whole = fonts.whole_fonts()
    short = []
    for name, f in families.items():
        if name in fonts.LEFT_OUT:
            continue
        for code in fonts.SCRIPTS:
            if (name, code) in whole:
                continue
            need = {ord(ch) for t in fonts.texts_of(f, code) for ch in t if site.in_script(ord(ch), code)}
            if need - built.get((name, code), set()):
                short.append(f"{name} ({code})")
    assert not short, "run scripts/build_page_fonts.py: " + ", ".join(short)
