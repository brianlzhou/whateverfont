# Page fonts

The site sets some words in each family's own font: its sample, its word on the wall, its block in the
footer and the poster. When a reader picks Arabic, Hindi, Japanese, Simplified or Traditional Chinese or
Korean, a family shows the translated words only if its font has every letter of them. The site never falls
back to another font.

The fonts in this folder give each family those letters. There is one font for each family and each of
the six languages, and it holds only the letters of that family's own words in that language. A reader
of English never loads them: the site gives each one a `unicode-range` of its script.

Each font is a modified version of an open font of the script:

- Arabic: Playpen Sans Arabic for a handwritten family, Noto Sans Arabic for the others.
- Devanagari: Kalam, or Noto Sans Devanagari.
- Japanese: Klee One, or Noto Sans JP.
- Simplified Chinese (the fonts named "Chinese"): LXGW WenKai GB, or Noto Sans SC.
- Traditional Chinese: LXGW WenKai TC, or Noto Sans TC.
- Korean: Gaegu, or Noto Sans KR.

`scripts/build_page_fonts.py` shapes the words with the source (HarfBuzz) and keeps only the glyphs that
shaping reaches: the joined forms of Arabic letters, the conjuncts and marks of Devanagari. It traces
their centerlines and draws them again with the family's pen and effect, as `whateverfont retrace` does
(see `docs/scripts.md`). Each Chinese font draws the forms and the stops of its own region: LXGW WenKai
GB and Noto Sans SC those of mainland China, LXGW WenKai TC and Noto Sans TC those of Taiwan, with the
stops in the middle of the em.
Pebble Sans is not drawn with a pen: its fonts are Noto Sans with round corners, as Pebble is Inter with
round corners. Where many strokes share one em (Japanese, Chinese, Korean), the pen draws lighter, so
that dense characters stay open. A family that has a whole font of the script in `examples/retrace`
gets no font here.

`index.json` lists every font: its family (`pen`), its language, its source, the words it sets and its
code points. The site reads it (`load_parts` in `scripts/build_site.py`).

## License

Every font here is under the SIL Open Font License 1.1, as its source is. Each one keeps the source's
copyright line and license in its name records. `OFL.txt` has the license and the copyright line of
every source used.

## Rebuilding

Rebuild the fonts after a translation or a family changes. The script needs the trace extra
(`pip install 'whateverfont[trace]'`). The Japanese, Chinese and Korean sources are large, so they are
not in the repository. Download them from their projects, put them in one folder, and give it with
`--east-asian`:

- `KleeOne-Regular.ttf`, `LXGWWenKaiTC-Regular.ttf`, `Gaegu-Regular.ttf` (Google Fonts)
- `LXGWWenKaiGB-Regular.ttf` (the releases of the `lxgw/LxgwWenkaiGB` repository)
- `NotoSansJP-Light.otf`, `NotoSansSC-Light.otf`, `NotoSansTC-Light.otf`, `NotoSansKR-Light.otf`, and the
  Regular of each for Pebble Sans (the `notofonts/noto-cjk` repository, `Sans/SubsetOTF`)

`examples/retrace/sources.json` lists the URL and the SHA-256 of most of them, and
`examples/retrace/build.py` fetches them into `examples/retrace/.cache/sources`.

```sh
python scripts/build_page_fonts.py --east-asian ~/fonts/east-asian
python scripts/build_page_fonts.py --east-asian ~/fonts/east-asian --proof out/page-fonts-proof
```

The script rebuilds only the fonts whose words, source, pen or effect changed. `--all` rebuilds every
font (do this after a change to the tracer), `--only FAMILY` and `--lang CODE` limit the run, and
`--list` shows what it would build. `--proof DIR` writes one HTML sheet for each language with every
family's words in its own fonts: look at it before you commit the fonts. A reader of the script must
review the result.
