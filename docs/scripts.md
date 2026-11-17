# Other scripts: retracing an open font

WhateverFont has recipes for Latin, Greek and Cyrillic. For another script, such as Arabic, Devanagari,
Japanese, Chinese or Korean, it can redraw an existing open font with a family's pen: `whateverfont retrace`
traces the centerline of every glyph of the source font, then draws each centerline again with the pen of
your family and, if you ask, an effect.

**The letter shapes come from the source font.** The skeleton of each letter, its proportions and its curves
are the source designer's work. The pen (weight, contrast, the shape of the ends, the dots) and the effect
(snow, a glow) are this project's. The result is a modified version of the source font, not a new design.

Retracing needs numpy. Add it to the environment that you installed the command in:

```sh
uv tool install 'whateverfont[trace]'      # if you installed with uv
pipx inject whateverfont numpy             # if you installed with pipx
pip install 'whateverfont[trace]'          # in a virtual environment
```

```sh
whateverfont retrace NotoSansArabic-Regular.ttf --name "Last Bell Arabic" --pen examples/lastbell \
    --out fonts/LastBellArabic

whateverfont retrace Kalam-Regular.ttf --name "Last Bell Snow Devanagari" \
    --pen "examples/lastbell:Last Bell Snow" --effect "examples/lastbell/snow.py:capped:depth=72" \
    --out fonts/LastBellSnowDevanagari

whateverfont retrace NotoSansDevanagari-Regular.ttf --name "Neon Glow Devanagari" \
    --pen "examples/neon:Neon Glow" --effect glow:size=80 --out fonts/NeonGlowDevanagari
```

| Option | What it does |
|---|---|
| `--name` | The new family name. It must not contain the source's family name, a Reserved Font Name of the source, or a name in its trademark notice: `Noto` is refused for a Noto source. |
| `--pen PROJECT[:FAMILY]` | The family whose pen draws the letters, at its default style. The first family of the project if you name none. |
| `--effect` | An effect from `whateverfont.effects` with its options (`glow:size=80`), or a project's own as `FILE.py:FUNCTION[:option=value,...]`. |
| `--palettes PROJECT[:FAMILY]` | For a color effect: whose palettes to use. By default the pen's family's. |
| `--out DIR` | Where to write `ttf/`, `woff2/` and a CSS file. |
| `--headline auto\|on\|off` | Trace the line that Devanagari letters hang from as one straight stroke. `auto` decides from the font. |
| `--at wght=500` | The instance of a variable source. By default its default. |
| `--only SET\|FILE` | Keep only some characters: a named set (`japanese`, `chinese`, `traditional`, `korean`) or a UTF-8 text file of characters. Give it more than once, or as `japanese,extra.txt`, to add them together. See [Japanese, Chinese and Korean](#japanese-chinese-and-korean). |
| `--corners auto\|sharp\|soft` | Rebuild the corners of the centerline as sharp points (for type) or keep them round (for handwriting). `auto` decides from the source for Japanese, Chinese and Korean, and is sharp for other scripts. |

The command prints the glyphs it traced, a warning for every glyph the self-check flags (see below), and
a note if the source declares no open license. It retraces a font under any license and does not refuse: it
is your job to check that the license lets you modify and share the font.

## What the new font keeps

- The shaping: `GSUB`, `GPOS` and `GDEF` stay as they are, so Arabic letters join, marks sit on their anchors,
  and Devanagari conjuncts and vowel signs still form.
- The character map, every advance width, and the glyph order.
- Composite glyphs stay composites: a letter with dots still points at the dot glyph. In a color font a
  composite gets color layers made of its parts' layers.
- Every glyph. Readers type their own text, so nothing is cut down to a sample. For Chinese characters,
  `--only` keeps a standard set of common characters instead of tens of thousands.

It drops the hinting (`fpgm`, `prep`, `cvt`, `gasp` and the instructions of every glyph), as whateverfont's
own fonts have none. A source with PostScript outlines (`.otf`) gets TrueType outlines, and a variable source
is cut to one instance. A source with another em than 1000 units (Inter and Roboto have 2048) is scaled to
1000 first: its outlines, advances, kerning and anchors together.

It works for Latin too: `whateverfont retrace Inter.ttf --name "Snowed In" --pen "examples/lastbell:Last Bell Snow"
--effect examples/lastbell/snow.py:capped` gives Inter's letters with snow on them. The accents are glyphs
of their own in such a font, and each gets the effect.

## Names and the license

The source's license applies to the result. For a font under the SIL Open Font License that means:

- the new font is under the OFL too, and the license records say so;
- the copyright record keeps the source's copyright line and adds yours (the family's `copyright`);
- the new font has a new name. `retrace` refuses a name that contains the source's family name, a Reserved
  Font Name, or a name from the trademark record;
- the trademark record of the source is not kept: the new font does not carry it.

The description record says which font the letters come from and which pen and effect drew them. Keep the
source's license text next to the fonts you share (the example keeps `OFL.txt` in each source folder).

## Choosing a source

The tracer follows strokes of even width. A source with thin, even strokes gives the cleanest skeleton; a
brush or high-contrast face breaks into lumps at its joins, and `retrace` warns when the wide strokes of a
source are more than 1.55 times its narrow ones.

Choose the source by the family. A geometric or technical family (Gantry, Neon) suits a plain sans such as
Noto Sans. A handwritten or marker family (Last Bell) suits a handwritten source: tracing a sans makes hand
letters look like type. `examples/retrace` draws Last Bell over Kalam (Devanagari) and Playpen Sans Arabic,
and Gantry and Neon Glow over Noto Sans.

## How the pen fits a script it was not made for

- Strokes take the pen's stem weight. Where that is heavier than the source, the strokes next to a small
  counter or a narrow gap get thinner, so that about half of the white stays: the eye of `ف` or `ق` and
  the counters of `ठ` stay open.
- Marks (the mark glyphs of `GDEF`) and dots grow less than the letters: a mark takes 40% of the extra
  weight, a dot 60%. A dot near a letter takes the white between them alone, so the letter keeps its weight.
- Ends that reach the left or the right side of a glyph are cut straight, so joined Arabic letters meet with
  no seam, all at one height.
- A Devanagari headline is cut out and drawn as one straight stroke, and the stems and stubs under it run up
  to its center.
- A stroke that crosses itself (a loop like `∞`, a handwritten loop) is drawn as pieces that do not, and
  each stroke is merged on its own before the glyph is: a heavy pen on a tight curve folds the inner edge
  back, and the fold must not cut into the stroke it overlaps.
- After an effect that asks for it, a dot or a short mark that the upper layers would cover (snow on a
  dot) gets its own color back. An effect asks by naming the key of its letter layer in `g.letter_layer`
  (`examples/lastbell/snow.py` does). Other effects (paint, tiles, dots, bands, a glow) keep their layers
  on a dot as on every other stroke.

## Japanese, Chinese and Korean

A font of Chinese characters has tens of thousands of glyphs. `--only` keeps the characters that everyday
text uses, and the shaping tables keep what they reach from them (vertical forms, local forms):

```sh
whateverfont retrace KleeOne-Regular.ttf --name "Last Bell Japanese" --pen examples/lastbell \
    --only japanese --out fonts/LastBellJapanese

whateverfont retrace NotoSansSC-Light.otf --name "Gantry Chinese" --pen "examples/caliper:Gantry" \
    --only chinese --out fonts/GantryChinese

whateverfont retrace NotoSansTC-Light.otf --name "Gantry Traditional Chinese" --pen "examples/caliper:Gantry" \
    --only traditional --out fonts/GantryTraditionalChinese

whateverfont retrace NotoSansKR-Light.otf --name "Neon Glow Korean" --pen "examples/neon:Neon Glow" \
    --effect glow:size=40 --only korean --out fonts/NeonGlowKorean
```

| Set | Characters |
|---|---|
| `japanese` | Hiragana, katakana and the 2,965 kanji of JIS X 0208 level 1 |
| `chinese` | The 3,755 characters of GB 2312 level 1 (Simplified Chinese) |
| `traditional` | The 5,401 characters of Big5 level 1 (Traditional Chinese, as Taiwan and Hong Kong write it) |
| `korean` | The 2,350 Hangul syllables of KS X 1001 |

Each set also has the space, the punctuation of East Asia (U+3000 to U+303F), the fullwidth forms, and the
quotes, dashes and ellipsis of General Punctuation, where the source has them. Korean also has the ASCII
punctuation, because Korean text uses it. Latin letters and figures are not in the sets: the Latin family
sets them. The sets come from Python's own codecs (`euc_jp`, `gb2312`, `big5`, `euc_kr`), so there is no data file.
`traditional` keeps the ideographs of rows A4 to C6 of Big5 only: the last of them goes on with kana.
Only 2,434 characters are in both Chinese sets. A Simplified font does not set Traditional text, and the
reverse: build one font for each.
A text file adds characters a set lacks, for example a level 2 kanji that your text needs.

Tracing is fast enough for these sets: on 16 processor cores, about 3,400 Japanese glyphs trace in half a
minute and draw in another half minute. A color effect takes longer: about a minute and a quarter for a glow,
three to four minutes for snow.

### Choosing a source

- A handwritten family needs a handwritten source with thin, even strokes. `examples/retrace` traces Last
  Bell from Klee One (Japanese), LXGW WenKai GB (Simplified Chinese), LXGW WenKai TC (Traditional
  Chinese) and Gaegu (Korean). A heavy brush face (Ma Shan Zheng) breaks into lumps.
- A technical family needs a plain sans. The Light weight of Noto Sans CJK (JP, SC, TC, KR) works best: its
  strokes are thin and leave the most white for a heavier pen.
- `--corners auto` gives sharp, rebuilt corners for a source whose outlines have corners at most of their
  points (type), and round ones for a handwritten source.
- A font made for one region draws the characters and the stops as that region does. LXGW WenKai TC has
  every Simplified character, but in Taiwan's forms, with its commas and stops in the middle of the square.
  Trace each region from a source made for it: `examples/retrace` takes LXGW WenKai GB and Noto Sans SC for
  Simplified Chinese, LXGW WenKai TC and Noto Sans TC for Traditional Chinese. Noto Sans TC follows Taiwan's
  standard forms; Hong Kong's differ in some characters.

### How the pen fits

- Nothing joins: each character sits alone in its square, so ends are not cut for joining and there is no
  headline.
- **A heavy pen is thinned for a dense character.** The tracer measures the white between strokes that run
  side by side, and between separate parts. The pen draws each character no heavier than leaves a quarter
  of its narrow white open, but never below 40% of its stem, nor thinner than the source.
- The whole font is drawn no heavier than its median character allows, so that a kana is not twice as dark
  as the kanji next to it. `retrace` prints how heavy that is (Last Bell over Klee One: 58% of its stem).
- A character that would still fill in at 40% of the stem (90% of its narrow white gone) is flagged as too
  dense for the pen.
- The strokes of type are straight: a nearly straight piece between corners becomes a straight line, so a
  stroke does not wobble where others meet it. A stroke runs straight through a crossing only if it bends
  less than 22 degrees there.
- A box keeps all four corners, and the closing curve of a ring meets its start with no bulge (the small
  notch at the seam of a Hangul ㅇ). A drawn curve that strays more than six units from the traced
  centerline is split, so a side does not bow out after a round corner.
- The boolean engine can drop a stroke while it merges a character with many strokes. Each merge is
  checked: the middle of every stroke must be inside it. If not, the strokes are merged one at a time, and
  a stroke that still fails is merged as a polygon.

### What breaks

- The densest characters (竃 and 聾 under Last Bell) are drawn at 40% of the pen's stem and still lose some
  white. The self-check flags them.
- Strokes that almost touch in the source (common in handwriting) may touch. The self-check counts parts
  closer than 0.6 of the stroke width as one, so it does not flag them.
- Snow lies on every horizontal stroke. Its depth must be smaller than the strokes, or it hides the letter:
  `examples/retrace` uses `depth=44`, and no drips (`drips=0`): a lump of snow under a stroke reads as a
  dot, and a dot is a stroke of its own (大 and 犬 differ by one).
- A wide glow fills the white between strokes in the same way. `examples/retrace` uses `glow:size=40`, half
  the glow of its Arabic and Devanagari fonts.
- A reader of each language must review the result: the engine cannot tell a correct stroke from a wrong
  one, or see that two radicals now read as one.

## The self-check

Every redrawn glyph is compared with its source. A glyph is flagged when:

- the new ink misses more than 8% of the source's centerline (a lost stroke or a stub),
- it has fewer counters than the source (a counter closed),
- it has fewer parts (two dots, or a mark and its letter, merged), or more (a stroke broke in two),
- it is too dense for the pen: a Chinese character, kana or Hangul syllable whose white fills in even at
  40% of the pen's stem.

`retrace` prints each flagged glyph as a warning and the count at the end; `--no-check` skips it. A flag is
a place to look, not always a fault: a heavy pen on a calligraphic word ligature fills some of its white on
purpose. Look at the flagged glyphs on a proof before you share the font.

## Limits

- The curves are the source's. A pen's `superness`, `width`, `xh` and other proportions do not apply: only
  the stroke (weight, contrast, angle, ends, roundness) and the dot shape do.
- A traced font is static: no axes and no variable font.
- Ball and teardrop terminals become round dots; a flared or pointed end of the source becomes the pen's end.
- Tight curls, stacked marks (shadda with tanwin, candrabindu) and the large word ligatures (`ﷺ`, `ﷻ`) are
  the weakest glyphs. The self-check flags most of them.
- An effect that fails on a glyph (a boolean operation of skia-pathops) is tried once more with the outline
  grown by 0.6 units. If it fails again, that glyph has the letter's color only, and the command says so.
- A reader of the script must review the result. The engine cannot tell a correct conjunct from a wrong one.

## From Python

```python
from whateverfont import trace

traced = trace.trace_font("NotoSansArabic-Regular.ttf")          # once, for any number of pens
family = trace.load_family("examples/neon:Neon Glow")
effect, label = trace.load_effect("glow:size=80")
result = trace.redraw(traced, "fonts/NeonGlowArabic", "Neon Glow Arabic", family, effect, effect_label=label)
print(result.ttf, len(result.flagged), "flagged")
```

`trace.trace_glyph(contours)` traces one shape, and `trace.check(source, drawn)` compares two outlines.
`trace.trace_font(path, only=charsets.named("japanese"))` keeps a named set (see `whateverfont.charsets`).
`examples/retrace/build.py` builds twenty-four families this way.
