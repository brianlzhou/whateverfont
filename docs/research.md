# What exists, and why WhateverFont is built this way

Notes from a survey of the field in November 2026.

## Agents and language models that make fonts

- **[NetsuFont](https://github.com/NetsumaInfo/NetsuFont)** (MIT; its KanjiVG data is CC BY-SA) is the closest
  project found. An agent draws glyphs through MCP operations from primitives (rectangles, rings, arcs,
  strokes) and watches a preview. It exports OTF only and is at an early stage.
- **[draw-your-font](https://github.com/danilo-znamerovszkij/draw-your-font)**, the
  [ImageAI font wizard](https://github.com/lelandg/ImageAI) and several blog posts turn a photo or a generated
  image of an alphabet into a font by tracing. The model labels characters. It does not draw them.
- **[fontlab-mcp-server](https://github.com/dithilli/fontlab-mcp-server)** scripts a running copy of FontLab.
- **[VecGlypher](https://xk-huang.github.io/VecGlypher/)** (CVPR 2026) trains a model to emit SVG path tokens.
  Its paper reports that general-purpose language models are poor at writing glyph paths directly. That
  result is the main reason WhateverFont keeps the model at the level of parameters and recipes.
- **Rounded Inter.** [Open Runde](https://github.com/lauridskern/open-runde) is a rounded Inter made with
  scripted corner rounding in Glyphs. `whateverfont remix` does the same kind of edit from the command line.
- Nothing found lets a model write a stroke-and-pen recipe that compiles to a variable font.

Simon Cozens' [survey of AI font generation](https://simoncozens.github.io/state-of-ai-font-generation/)
concludes that neural methods give drawings without spacing or kerning, and that results for Latin are weak.
DeepVecFont, DualVector and FontDiffuser are research code and are not practical here.

## Parametric type design

- **Metafont** (Knuth) is the origin of the skeleton-and-pen model. WhateverFont borrows the model, not the code.
- **[Metapolator](https://github.com/metapolator/metapolator)** applied skeleton parameters to existing
  fonts. It is no longer maintained.
- **[Prototypo](https://github.com/byte-foundry/prototypo)** offered parametric sliders in a browser. It
  closed on July 1, 2020, as [its website](https://www.prototypo.io) says. Its code is on GitHub under the
  Mozilla Public License 2.0.
- **[Fontra](https://github.com/fontra)** is an active browser font editor. A person could use it to
  finish a font that WhateverFont started.
- **fontTools, fontmake, ufo2ft** are the standard open build chain. WhateverFont uses fontTools directly:
  `fontBuilder` for tables, `cu2qu` for curves that stay compatible across masters, `varLib` for the
  variable font.

## Build choices and their pitfalls

- **Overlaps.** Static fonts have overlaps removed with skia-pathops. Variable masters keep them, because
  removing them would break point compatibility. Each variable glyph sets the `OVERLAP_SIMPLE` flag, without
  which some Apple renderers fill overlaps wrongly.
- **Proofs** are shaped with HarfBuzz and drawn with FreeType through Pillow. A browser screenshot of the
  review board is the final check.
- **Vertical metrics** follow the Google Fonts guide: typo and hhea values match, the line gap is 0, and
  `USE_TYPO_METRICS` is set.
- **Hinting** is left out. Removing overlaps drops it anyway, and web text does not need it.

## Spacing and kerning

- [HT Letterspacer](https://github.com/huertatipografica/HTLetterspacer) sets sidebearings from the white
  area beside a glyph, measured to a limited depth. Walter Tracy's method sets `n`, `o`, `H` and `O` first
  and derives the rest.
- WhateverFont combines the two ideas. A recipe declares what each side of a letter is, as Tracy's groups do.
  Kerning measures the depth-limited white between two glyphs, as HT Letterspacer does, and moves the pair
  toward the white between two straight stems.
- Overshoot: round letters pass the baseline and the cap height or x-height by about 1 to 3% of that height
  ([Wikipedia](https://en.wikipedia.org/wiki/Overshoot_(typography))). The default `overshoot` of 11 units
  is 1.6% of the default cap height and 2.2% of the default x-height.
- Three other defaults of `Params` are estimates: horizontal strokes at 86% of vertical ones (`contrast`),
  round strokes 4% heavier than straight stems (`round_weight`), and capital stems 10% heavier than
  lowercase stems (`cap_weight`).

## Color fonts

- **COLR version 0** (flat layers) draws in Chrome, Firefox, Safari and CoreText. Safari dropped it in 17.0
  and restored it in 17.2, so test on a real device. [caniuse](https://caniuse.com/colr)
- **COLR version 1** (gradients) draws in Chrome and Firefox. Safari does not support it.
  [caniuse](https://caniuse.com/colr-v1)
- `font-palette` and `@font-palette-values` switch palettes in all three browsers.
  [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-palette-values)
- The base glyph of a color glyph must have a bounding box that covers every layer, or some renderers clip
  the layers. WhateverFont makes the base glyph a solid tile with the letter cut out, which also reads well
  where color is not supported.
- No open font of illuminated initials in color was found. Nabla and Kalnia Glaze are the open color
  fonts to study.

## The flare genre, and what "inspired by" means

Optima, Albertus, Pascal, ABC Arizona Flare and Faculty Glyphic share one idea: strokes that widen toward
their ends without a separate serif. Dinamo describes ABC Arizona as a family that runs from sans to serif in
one file, with Flare as the "nearly-but-not sans" step. WhateverFont's `FLAR` axis is a small version of that
idea, made from its own skeletons.

No published source gives numbers for the genre. The defaults in the `flare` preset are our estimates:
terminals 20 to 40% wider than the stem, a contrast of about 0.6, near-vertical stress, Roman capital widths.

In the United States a typeface design cannot be registered for copyright, while font software can
(37 CFR 202.1(e); *Adobe v. Southern Software*, 1998). Names can be trademarks. So: draw your own outlines,
never copy font data, and do not use another foundry's name. This is a summary and not legal advice.

## Open fonts to remix

All of these are under the SIL Open Font License 1.1: Inter, Geist, Figtree, Instrument Sans, Recursive,
Roboto Flex, Source Sans 3, IBM Plex Sans, Atkinson Hyperlegible Next, Source Serif 4, Fraunces, Newsreader,
Literata, EB Garamond, Crimson Pro, Instrument Serif, Faculty Glyphic, Cinzel, Marcellus, Grenze Gotisch,
Texturina.

What the license asks of a modified version ([OFL FAQ](https://openfontlicense.org/ofl-faq/)):

- It stays under the OFL. It cannot be relicensed.
- It keeps the copyright notices.
- It must not use a Reserved Font Name that the original declares. Source Sans 3, IBM Plex Sans, Marcellus,
  Forum and Tenor Sans declare one. A new name is good practice in every case.
- It cannot be sold by itself.

Fonts can be fetched from `https://raw.githubusercontent.com/google/fonts/main/ofl/<name>/<file>`.

## Other scripts

See [roadmap.md](roadmap.md) for the plan. The short version: Greek and Cyrillic are drawn. Letters that
have the shape of a Latin letter draw that letter, and the others have recipes of their own
(`recipes/greek.py`, `recipes/cyrillic.py`). Still open are polytonic Greek, the Bulgarian, Serbian and
Macedonian forms of Cyrillic letters, and a review by people who read those scripts. For Japanese,
[KanjiVG](https://github.com/KanjiVG/kanjivg) holds hand-traced centerlines for about 6,000 kanji and the
kana, which a pen model can expand directly. `whateverfont.kana` does this for the kana. KanjiVG's license is
CC BY-SA 3.0, so a font made from it must carry that license. Other scripts are redrawn from open fonts with
`whateverfont retrace` (see [scripts.md](scripts.md)).
