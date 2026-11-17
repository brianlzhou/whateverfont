# The site

This folder holds the source of [fonts.brianzhou.org](https://fonts.brianzhou.org): the pages that set the
example fonts live, and the library page. `scripts/build_site.py` fills the templates here with the fonts of
`examples/` and `library/` and writes the site to `out/site`.

## Build and serve

```sh
python3 scripts/build_site.py                  # build into out/site
python3 scripts/build_site.py --serve 8787     # build, then serve it at http://127.0.0.1:8787/
python3 scripts/build_site.py --serve 8787 --no-build   # serve the last build as it is
```

The build uses only the Python standard library, so a host can run it without installing whateverfont. It
copies the built fonts, so rebuild the examples first (`python scripts/build_examples.py`) when a font
changes. Vercel runs the same command (see `vercel.json`) and serves `out/site`. It rebuilds the site on
every push to `main`. `.vercelignore` keeps the upload to the folders that the build reads.

While `INDEX` in `scripts/build_site.py` is `False`, every page asks search engines not to index it.

| File | What it is |
|---|---|
| `index.html` | The first page. The build replaces each `@NAME@` in it. |
| `catalog.html`, `catalog.js`, `catalog.css` | The library page: the shelf, the search by mood, votes and views. |
| `font.html` | The page of one font of the library. |
| `app.js`, `style.css` | The script and the styles of the pages: the shared sample text and size, the axis sliders, the palettes and the character table. |
| `search.js`, `search/` | The search by mood. It runs in the reader's browser on the word vectors in `search/` (see [search/README.md](search/README.md)). |
| `i18n/` | The translations. |
| `page-fonts/` | Small fonts for the words that each family sets in other scripts, and the slices of large fonts. |
| `vendor/` | Matter.js, for the footer (see [vendor/README.md](vendor/README.md)). |
| `card.png` | The picture of a link preview. `python scripts/build_card.py` draws it again. |
| `skeleton.svg`, `favicon.svg` | Pictures that the first page uses. |

## Translations

The language menu has 13 languages: English and 12 translations. They are Spanish, French, German, Galician,
Breton, Vietnamese, Simplified Chinese (`zh`), Traditional Chinese as Taiwan writes it (`zh-Hant`), Japanese,
Korean, Arabic and Hindi. `LANGS` in `scripts/build_site.py` lists them. English is in the pages, and every
other language is one file, `i18n/CODE.json`. A language is in the menu only when its file exists.

The build writes [`i18n/en.json`](i18n/en.json) from the English pages. To add or correct a translation:

1. Copy the keys of `i18n/en.json` into `i18n/CODE.json`.
2. Translate each text. Keep its tags and its `{n}` exactly.
3. Add the language to `LANGS` in `scripts/build_site.py`.
4. Build the site. The build stops on a key that the pages do not have, an empty text, or a text that lost a
   tag or its `{n}`.

A text with no translation stays in English, and the build lists those texts.

Some keys are words that the page sets in a family's own font: `sample.` (the sample of each font), `word.`
(the wall), `block.` (the footer), `demo.` and `poster.text`. A family shows such a text only if its font has
every letter of the translation, and the page never sets such a text in another font. So write these texts
with letters that the fonts have. In Japanese, Chinese and Korean, they must keep to the character sets of the whole fonts in
`examples/retrace`: kana and JIS X 0208 level 1, GB 2312 level 1, Big5 level 1, and the Hangul of KS X 1001.
`tests/test_site.py` checks this.

A language code can have a subtag, such as `zh-Hant`. The CSS selector `:lang(zh)` matches `zh-Hant` too, so
the build writes the rules of `zh` to leave out the longer codes. A Traditional Chinese page never names or
loads a Simplified Chinese font, and the reverse.

## Fonts of the pages

The pages themselves are set in Arroyo, Arroyo Text, Gantry and Tally Mono (`PAGE_FACES` in
`scripts/build_site.py`).

A family that has no letters of a script cannot set its words in that language. `scripts/build_page_fonts.py`
draws a small font for each family and each of Arabic, Hindi, Japanese, Simplified Chinese, Traditional
Chinese and Korean, with only the letters of that family's words. It needs the `trace` extra and the Japanese,
Chinese and Korean source fonts, which are not in the repository. [page-fonts/README.md](page-fonts/README.md)
explains how to run it.

A large font loads in two files: a slice with the letters of the page's own words, and the whole font for a
reader who types other words. This applies to the fonts of other scripts in `examples/retrace` and to every
Latin family whose web font is larger than 250 KB, such as Arroyo, Gilt and Kanagawa.
`python scripts/build_page_slices.py` cuts the slices into `page-fonts/slices/` and lists them in
`page-fonts/slices.json`. Run it again after a translation changes or a font is rebuilt. It needs fontTools,
so run it in the virtual environment of [CONTRIBUTING.md](../CONTRIBUTING.md).

## Votes and views

A Cloudflare Worker in [`worker/`](../worker/README.md) counts the votes and views of the library. It keeps
the counts in the SQLite storage of one Durable Object. It stores a salted hash of a visitor's address, and
it does not store the address itself.

`COUNTS` in `scripts/build_site.py` is the address that the pages ask. With an empty `COUNTS`, or with
`WHATEVERFONT_COUNTS` set to an empty value when you build, the pages show no vote buttons and no numbers.

To try votes and views on your computer, build the site and serve it with the Worker's code and SQLite in
memory (Node 22.5 or newer):

```sh
python3 scripts/build_site.py && node scripts/try_site.js --seed
```

`--seed` starts with some votes and views. The site is then at http://localhost:8788/.
