"""The site: the texts that the language menu changes, and the translations of them."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

EN = json.loads((site.I18N / "en.json").read_text(encoding="utf-8"))
CODES = [code for code, _, _ in site.LANGS[1:] if (site.I18N / f"{code}.json").is_file()]


def test_the_build_reads_the_english_texts_from_a_page():
    page = ('<h2 data-i18n="a.h" data-n="364">364 characters in the <b>basic</b> set</h2>'
            '<p data-i18n="a.p">One<br>two &amp; three</p>'
            '<input data-i18n-attr="placeholder:a.box" placeholder="Type here">'
            '<span data-i18n="a.n" data-n="9">9 styles</span><span data-i18n="a.n" data-n="4">4 styles</span>')
    texts = site.english([page])
    assert {key: text for key, text in texts.items() if key.startswith("a.")} == {
        "a.h": "{n} characters in the <b>basic</b> set", "a.p": "One<br>two &amp; three",
        "a.box": "Type here", "a.n": "{n} styles"}
    assert texts["chars.g11"] == "Han characters"              # a name that only the page's script writes


def _family(name, **more):
    return dict({"name": name, "id": site.slug(name), "sample": "Sphinx of black quartz", "description": "A plain face.",
                 "axes": [], "palettes": [], "codepoints": list(range(32, 127))}, **more)


def test_a_font_of_the_shelf_shows_its_word_of_the_wall_or_the_start_of_its_sample():
    name, word = site.WALL[0][0], site.WALL[0][1]
    on_wall = {"id": "one", "title": "One", "families": [_family("Other Face"), _family(name)]}
    f, shown, *_, key = site.tile_of(on_wall)
    assert (f["name"], shown, key) == (name, word, "word." + site.slug(name))
    plain = {"id": "two", "title": "Two", "families": [_family("Nobody Knows This Face")]}
    f, shown, *_, key = site.tile_of(plain)
    assert (shown, key) == ("Sphinx of", "word.nobody-knows-this-face")
    assert site.tile_of(dict(plain, word="Yes"))[1] == "Yes"          # an entry can name its word


def test_the_wall_of_the_first_page_has_a_tile_for_every_font_of_the_library():
    books = [{"id": "one", "page": "one", "title": "One", "github": "octocat", "families": [_family(site.WALL[0][0])]},
             {"id": "two", "page": "two", "title": "Two", "github": "someone", "families": [_family("Nobody Knows This Face")]}]
    tiles = site.wall(books)
    assert tiles.count('<a class="tile') == 2
    assert 'href="library/one/"' in tiles and 'href="library/two/"' in tiles
    assert tiles.count('class="tile-title"') == 2 and "@octocat" in tiles and "@someone" in tiles
    assert 'data-i18n="lib.by"' in tiles                              # "by" follows the language of the page


def test_a_wide_tile_of_the_wall_shows_the_sample_line_and_the_wall_keeps_its_order():
    wide, narrow = next(iter(site.WALL_WIDE)), next(page for page in site.WALL_ORDER if page not in site.WALL_WIDE)
    books = [{"id": "new", "page": "a-font-nobody-placed", "title": "New", "github": "someone", "families": [_family("Face Three")]},
             {"id": narrow, "page": narrow, "title": "Narrow", "github": "octocat", "families": [_family("Face Two")]},
             {"id": wide, "page": wide, "title": "Wide", "github": "octocat", "families": [_family("Face One", sample="A line of several words")]}]
    tiles = site.wall(books)
    assert [tiles.index(f'href="library/{page}/"') for page in site.WALL_ORDER if f'href="library/{page}/"' in tiles] == \
        sorted(tiles.index(f'href="library/{b["page"]}/"') for b in books[1:])        # in the order of the wall
    assert tiles.index('href="library/a-font-nobody-placed/"') > tiles.index(f'href="library/{narrow}/"')   # then the others
    assert tiles.count('class="tile wide') == 1
    first = tiles[tiles.index('class="tile wide'):]
    assert ">A line of several words</span>" in first[:first.index("</a>")]
    assert 'data-font-text="sample.' in first[:first.index("</a>")]              # the line follows the language


def test_the_sliders_show_the_numbers_of_the_design_file():
    source = (site.LIBRARY / site.DIALS / "font.py")
    if not source.is_file():
        pytest.skip("the font of the sliders is not in the library")
    axes = [{"tag": "wght", "min": 200, "default": 400, "max": 800}, {"tag": "slnt", "min": -14, "default": 0, "max": 0},
            {"tag": "CNTR", "min": 0, "default": 60, "max": 100}]
    books = [{"id": site.DIALS, "page": site.DIALS, "title": "Eight Dials", "github": "octocat",
              "families": [_family("Eight Dials", id="lib-eight-dials", axes=axes, sample="Every letter is a decision")]}]
    figure = site.dials(books)
    # the weight of the base at rest, and the weights at the ends of the axis
    assert 'data-tag="wght" min="200" max="800" step="any" value="400" data-default="400" data-ends="40 84 158" data-places="0"' in figure
    # a slant rests at the far end of its axis: the slider is turned over, and rests at 0 on the near side
    assert 'data-tag="slnt" min="0" max="14" step="any" value="0" data-default="0" data-turned data-ends="0 0 14"' in figure
    assert 'data-ends="1 0.78 0.24" data-places="2"' in figure and "<output>0.78</output>" in figure
    assert figure.index(">weight<") < figure.index(">contrast<") < figure.index(">slant<")
    assert site.dials([]) == ""                                    # without the font, the page has no sliders


def test_the_shelf_leads_to_the_page_of_a_font_and_names_who_added_it():
    entry = {"id": "two", "page": "two", "title": "Two & Co", "github": "someone", "families": [_family("Nobody Knows This Face")]}
    tile = site.book(entry)
    assert 'href="library/two/"' in tile and "Two &amp; Co" in tile and "@someone" in tile
    assert tile.count('data-id="two"') == 3                   # the tile, its views and its vote
    assert "hidden" in tile                                   # no number shows before the store answers


def test_the_search_reads_the_chosen_mood_words_first_and_the_other_text_too():
    p = {"id": "two", "page": "two", "title": "Two", "prompt": "A calm sans.", "families": [_family("Face")]}
    assert site.mood_words(p, {"two": "quiet office"}) == ("quiet office", "Two A calm sans. Face A plain face.")
    assert site.mood_words(dict(p, moods="from the entry"), {})[0] == "from the entry"


def test_fonts_with_moods_that_mean_the_same_are_alike():
    vectors = site._Vectors(site.SEARCH)
    sea, office = ["ocean", "wave", "water"], ["office", "report", "invoice"]
    assert vectors.alike(sea, sea) == 1
    assert vectors.alike(sea, ["sea", "beach"]) > vectors.alike(sea, office) + 0.2
    assert vectors.alike(sea, []) == 0 and vectors.near("zzzzqq", "ocean") == 0


def test_the_table_of_a_font_page_has_every_character_in_a_group():
    cps = list(range(0x41, 0x5B)) + [0x20, 0xE9, 0x3C0, 0x31, 0x2166, 0x21, 0x20AC, 0x301] + list(range(0x410, 0x430))
    page, count = site.font_charset({"families": [_family("Plain Face", codepoints=cps)]})
    assert count == len(cps)                                   # the number of the heading counts the space too
    assert page.count("<button type=\"button\" data-cp=") == len(cps) - 1     # and the table leaves the space out
    assert "charset-fonts" not in page                         # one family: nothing to pick
    assert 'data-i18n="chars.g8"' in page and ">32<" in page   # 32 Cyrillic letters have a group of their own
    assert 'data-i18n="chars.g7"' not in page                  # one Greek letter stays with the accented letters
    assert 'data-cp="2166"' in page and 'data-cp="20AC"' in page   # a Roman numeral and a currency sign
    assert ">ó<" in page                                 # a combining mark is shown on a letter
    assert page.index("chars.g5") < page.index("chars.g6")     # the marks come last


def test_the_table_of_a_color_font_stands_on_the_ground_of_its_first_palette():
    plain = _family("Plain Face")
    color = _family("Color Face", palettes=["Night", "Day"], grounds={"Night": "#101820", "Day": "#F4F0E6"})
    page, _ = site.font_charset({"families": [color, plain]})
    body = page[page.index('<div class="charset-body'):]
    assert body.startswith('<div class="charset-body dressed"')
    assert "font-palette: --ff-color-face-0; --ground: #101820; --tone: #F1EEE7;" in body
    assert "data-ground='#101820'" in page and page.count("data-ground=") == 1     # only the color font brings a ground
    assert "data-has=" not in page                             # both have the same characters


def test_families_with_other_characters_show_their_own():
    letters = _family("Letters Only", codepoints=list(range(0x41, 0x5B)))
    more = _family("With Figures", codepoints=list(range(0x30, 0x3A)) + list(range(0x41, 0x5B)))
    page, count = site.font_charset({"families": [letters, more]})
    assert count == 26
    assert "data-has='41-5A'" in page and "data-has='30-39 41-5A'" in page
    # ten figures, the heading and the box of their group, the empty row of other scripts, and the button that
    # opens a long table
    assert page.count(" hidden>") == 10 + 2 + 1 + 1
    assert '<span class="muted">0</span>' in page
    assert site.hex_runs([5, 1, 2, 3, 9]) == "1-3 5 9"


def test_a_family_names_its_whole_fonts_of_other_scripts_for_its_table():
    part = {"id": "plain-face-japanese", "language": "ja", "script": "Japanese", "whole": True,
            "codepoints": [0x3042, 0x30A2, 0x4E00, 0x4E8C, 0x3001, 0xAC00, 0xFF21]}
    small = dict(part, id="plain-face-japanese-page", whole=False)
    f = _family("Plain Face", parts=[part, small])
    assert site.scripts_of(f) == [{"name": "Japanese", "font": "ff-plain-face-ja", "file": "chars/plain-face-japanese.json", "n": 7}]
    page, _ = site.font_charset({"families": [f]})
    assert "data-scripts='[{&quot;name&quot;:&quot;Japanese&quot;" in page and 'class="chips charset-scripts"' in page
    chars = site.part_chars(part)
    assert chars["count"] == 7
    assert [(key, runs) for key, _, runs in chars["groups"]] == [             # the script's letters before the Latin ones
        ("chars.g10", "3042 30A2"), ("chars.g11", "4E00 4E8C"), ("chars.g12", "AC00"), ("chars.g2", "FF21"), ("chars.g4", "3001")]
    assert chars["names"]["3042"] == "hiragana letter a" and "4E00" not in chars["names"]     # a Han character has no name


def test_a_font_cut_in_two_files_lists_all_its_characters():
    # The page loads a large font as two files: a small one with the letters of the page's own words, and the
    # whole font for the others. The table of the font's page lists the letters of both.
    part = {"id": "plain-face-japanese", "language": "ja", "script": "Japanese", "whole": True,
            "codepoints": [0x3042, 0x4E00], "listed": [0x3042, 0x3044, 0x4E00, 0x96EA]}
    small = dict(part, id="plain-face-japanese-page", whole=False, codepoints=[0x3044, 0x96EA])
    f = _family("Plain Face", parts=[part, small])
    assert site.scripts_of(f)[0]["n"] == 4
    chars = site.part_chars(part)
    assert chars["count"] == 4
    assert [(key, runs) for key, _, runs in chars["groups"]] == [("chars.g10", "3042 3044"), ("chars.g11", "4E00 96EA")]


def test_a_character_table_has_the_button_that_opens_it():
    page, _ = site.font_charset({"families": [_family("Plain Face")]})
    assert page.count('<p class="charset-more" hidden>') == 1 and page.endswith("</button></p>")
    assert 'data-i18n="chars.more"' in page and 'data-i18n="chars.less"' in page


def test_every_font_with_mood_words_is_a_font_that_the_functions_count():
    counted = set(json.loads((ROOT / "worker" / "fonts.json").read_text(encoding="utf-8")))
    folders = set(site.PROJECTS) | {p.name for p in (ROOT / "library").iterdir() if (p / "fonts" / "index.json").is_file()}
    assert counted == folders, "run scripts/build_site.py: it writes worker/fonts.json"
    assert set(json.loads((site.SEARCH / "moods.json").read_text(encoding="utf-8"))) <= counted


def test_one_key_cannot_have_two_english_texts():
    with pytest.raises(SystemExit):
        site.english(['<p data-i18n="k">One</p><p data-i18n="k">Another</p>'])


def test_every_language_of_the_menu_has_a_name_and_a_file_or_is_english():
    codes = [code for code, _, _ in site.LANGS]
    assert codes[0] == "en" and len(set(codes)) == len(codes)
    assert all(name.strip() for _, name, _ in site.LANGS)
    assert all(way in ("", "rtl") for _, _, way in site.LANGS)


@pytest.mark.parametrize("code", CODES)
def test_a_translation_keeps_the_keys_the_tags_and_the_numbers(code):
    words = json.loads((site.I18N / f"{code}.json").read_text(encoding="utf-8"))
    for key, text in words.items():
        assert key in EN, f"{code}: {key} is not a text of the page"
        assert isinstance(text, str) and text.strip(), f"{code}: {key} is empty"
        assert site._tags(text) == site._tags(EN[key]), f"{code}: {key} must keep the tags of the English text"
        assert ("{n}" in text) == ("{n}" in EN[key]), f"{code}: {key} must keep the number"
        if "whateverfont" in EN[key]:
            assert "whateverfont" in text, f"{code}: {key} must keep the name of the command"


#: The set of characters that a font of each East Asian language holds (see whateverfont.charsets).
SETS = {"ja": "japanese", "zh": "chinese", "zh-Hant": "traditional", "ko": "korean"}
FONT_WORDS = ("sample.", "word.", "block.", "demo.", "poster.text")


@pytest.mark.parametrize("code", [c for c in CODES if c in SETS])
def test_the_font_words_of_an_east_asian_translation_stay_in_its_set(code):
    """A word that the page sets in a family's font uses only the characters that its whole font has (kana
    and JIS level 1, GB 2312 level 1, Big5 level 1, KS X 1001 Hangul), and Latin letters, figures and simple
    punctuation, which the family's own font sets."""
    import re
    from whateverfont import charsets
    allowed = charsets.named(SETS[code]) | set(range(0x20, 0x7F)) | charsets.GENERAL
    words = json.loads((site.I18N / f"{code}.json").read_text(encoding="utf-8"))
    wrong = {key: "".join(sorted({c for c in re.sub(r"<[^>]+>", "", text) if ord(c) not in allowed}))
             for key, text in words.items() if key.startswith(FONT_WORDS)}
    assert not {k: v for k, v in wrong.items() if v}, f"{code}: characters outside the {SETS[code]} set"


def test_every_east_asian_language_of_the_menu_has_a_set():
    assert {code for code in CODES if code in site.EAST_ASIAN} <= set(SETS)


def test_a_rule_for_one_language_leaves_out_its_longer_codes():
    """:lang(zh) matches a page in zh-Hant too: the rule of Simplified Chinese must leave it out."""
    assert site.lang_rule("zh") == ":root:lang(zh):not(:lang(zh-Hant))"
    assert site.lang_rule("zh-Hant") == ":root:lang(zh-Hant)"
    assert site.lang_rule("ja") == ":root:lang(ja)"
    codes = [code for code, _, _ in site.LANGS]
    assert codes.index("zh-Hant") == codes.index("zh") + 1
    assert site.SHORT["zh"] != site.SHORT["zh-Hant"]


def test_each_chinese_page_names_only_its_own_fonts():
    """A family with a Simplified, a Traditional and a Japanese font: each page language picks its own."""
    f = {"id": "pen", "name": "Pen", "axes": [], "palettes": [], "codepoints": [0x41]}
    f["parts"] = [{"id": f"pen-{code.lower()}", "language": code, "codepoints": [0x4E00, 0x5B57]}
                  for code in ("zh", "zh-Hant", "ja")]
    css = site.faces_css([{"families": [f]}])
    assert ':root:lang(zh):not(:lang(zh-Hant)) { --p-pen: "ff-pen-zh"; }' in css
    assert ':root:lang(zh-Hant) { --p-pen: "ff-pen-zh-Hant"; }' in css
    assert ':root:lang(ja) { --p-pen: "ff-pen-ja"; }' in css
    assert site.in_script(0x5B57, "zh-Hant") and site.in_script(0x3002, "zh-Hant")
    assert not site.in_script(0x41, "zh-Hant")
