# Examples

Each folder is a complete WhateverFont project: `BRIEF.md` (the brief and the decisions), `font.py` (the design),
`fonts/` (the built files) and `board.html` (the review board; open it in a browser).

| Folder | Start here |
|---|---|
| `arroyo` | A flare serif in three directions. Shows axes, named styles and a custom `FLAR` axis. |
| `caliper` | A condensed display face and a technical sans. Shows a width axis and a roundness axis. |
| `tally` | A monospaced face for code. Shows `preset("mono")`. |
| `dayshift` | A plain interface sans. Shows `round_width`, `cap_width`, `word_space`, and `arm` on the bold pole. |
| `setsquare` | A geometric sans. Shows `preset("geometric")` with a round `o` next to a narrow `n`. |
| `softboil` | A rounded sans. Shows `preset("rounded")` with interface proportions. |
| `doorstep` | A slab serif text family. Shows `serif` on a proportional face, with shorter, heavier slabs at the bold pole. |
| `hedmast` | A condensed headline sans. Shows `cut="flat"`, a weight and a width axis, and a few letters redrawn for heavy weights. |
| `lowslung` | A wide display sans. Shows a width axis with three stops, and hooks and accents redrawn for wide, heavy letters. |
| `scanstep` | A pixel font. Shows an effect that draws every character from a chart of pixels on one grid. |
| `etchant` | A custom effect written by an agent: it turns the strokes of each letter into traces, pads and vias. |
| `tinsheen` | A custom effect written by an agent: chrome from stacked flat bands, a rim and an outline. |
| `teacloth` | A custom effect written by an agent: one X stitch for each square of a letter, in two thread tones. |
| `knollrise` | A custom effect written by an agent: rings from the outline shrunk step by step, with index contours. |
| `platen` | A typewriter face. Shows `preset("typewriter")`, slab serifs on a weight axis, ball terminals added to recipes, and an inked effect of its own. |
| `pinout` | A datasheet mono. Shows redrawn `g y l 0` and the `em` and `double_vee` helpers for a narrow cell. |
| `greenbar` | Dot-matrix print. Shows an effect that places every glyph on a fixed grid from a character ROM, and a color font of the same characters. |
| `lastbell` | A display face revised in four rounds, recorded in its brief. Shows a color effect written in the project: snow that settles where a letter faces the sky. |
| `wassail` | A book hand and a color font of decorated capitals. Shows `illuminate` and palettes. |
| `aviary` | A picture font of birds. Shows a kit of shapes, layers that leave a gap of paper, and one palette shared by 26 drawings. |
| `neon` | A tube letter in three shapes, and `effects.glow`. |
| `crate` | A stencil with hand-placed bridges. Shows `g.cutouts` and a wrapper of your own. |
| `effects` | Five faces with one effect each: `inline`, `stripes`, `layered_shadow`, `dotted`, `banded`. |
| `starry` | `effects.painted`, and a scene behind each capital built with `field_marks`. |
| `haystack` | The same tools as `starry`, and four palettes that change the hour. |
| `gilt` | A custom effect written by an agent: tiles, spirals and ringed circles. |
| `kanagawa` | A custom effect written by an agent: foam and claws on a wave. |
| `cutout` | A custom effect written by an agent: straight scissor cuts, and one color per letter. |
| `cabochon` | A custom effect written by an agent: a bevel, a bright line and cloudy patches from flat color layers. |
| `ombrelle` | A custom effect written by an agent: dots that are never cut, a lit side and a shadow side, a border of dots. |
| `panework` | A custom effect written by an agent: a frame, a grid of lines, and whole rectangles of color. |
| `lacentine` | A custom effect written by an agent: a doily under each letter, and side bearings set from the doily. |
| `drippelgang` | A custom effect written by an agent: goo that runs down each stroke, with a gloss and a shadow. |
| `leafpile` | A custom effect written by an agent: leaf shapes with veins that follow the strokes, in four palettes. |
| `pebble` | A remix of Inter. Shows `whateverfont remix`. |
| `retrace` | Last Bell, Last Bell Snow, Neon Glow and Gantry in Arabic, Devanagari, Japanese, Simplified and Traditional Chinese, and Korean. Shows `whateverfont retrace` with a pen and an effect, and `--only` for the large scripts. It has a `build.py` instead of a `font.py`. |

Rebuild everything with `python scripts/build_examples.py` from the repository root. To see proof sheets,
run `whateverfont look examples/arroyo`; the pictures go to `examples/arroyo/proofs/`, which git ignores.

Every font here except Pebble Sans and the fonts in `retrace/` was drawn with WhateverFont and is under the
SIL Open Font License 1.1, see [OFL.txt](OFL.txt). Pebble Sans keeps Inter's license, see
[pebble/OFL.txt](pebble/OFL.txt). The fonts in `retrace/` are redrawn from Kalam, Playpen Sans Arabic, Noto
Sans, Noto Sans CJK, Klee One, LXGW WenKai and Gaegu, and keep the licenses of those fonts. See
[retrace/OFL.txt](retrace/OFL.txt), and the `OFL.txt` in the folder of each Japanese, Chinese and Korean font
in `retrace/fonts/`. The source fonts in `retrace/kalam/`, `retrace/noto/` and `retrace/playpen/` each have
their `OFL.txt` next to them.

## Use a font on a web page

Every family folder has a stylesheet. For the variable font:

```html
<link rel="stylesheet" href="fonts/Arroyo/Arroyo.css">
<style>
  h1 { font-family: "Arroyo"; font-weight: 300; font-variation-settings: "FLAR" 80; }
  p  { font-family: "Arroyo"; font-weight: 400; }
</style>
```

For the color font, pick a palette with CSS:

```css
@font-palette-values --frost { font-family: "Wassail Initials"; base-palette: 2; }
.initial { font-family: "Wassail Initials"; font-palette: --frost; }
```
