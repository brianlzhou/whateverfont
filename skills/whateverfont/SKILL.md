---
name: whateverfont
description: Design a custom typeface from a plain-language brief and deliver real font files (TTF, WOFF2, variable). Use when someone asks for a custom font, a font "like X but ...", a bolder, rounder or condensed version of a font, an illuminated or themed display font, or a font for a specific project, and when a design needs a typeface that is not one of the default web fonts.
---

# WhateverFont

You design typefaces with the `whateverfont` engine. You write parameters and short recipes. The engine expands
them into outlines, spaces and kerns the letters, and compiles font files. You never write outline
coordinates by hand.

## Set up

Check that the command exists: `whateverfont --version`. If it does not, install it:
`uv tool install whateverfont` (or `pipx install whateverfont`, or `pip install whateverfont` in a virtual
environment).

The reference pages ship with the package. `whateverfont docs` lists them, and `whateverfont docs NAME` prints one.
Read them when you need them:

- `whateverfont docs parameters`: every parameter, with usual ranges. Read it before you change numbers.
- `whateverfont docs recipes`: the drawing vocabulary. Read it before you write or replace a recipe.
- `whateverfont docs effects`: stencil, inline, shadow, glow, paint and other effects, color fonts, picture
  fonts and monospaced fonts. Read it for any request that is not a plain text face.
- `whateverfont docs scripts`: Arabic, Devanagari and other scripts, redrawn from an open font.
- `whateverfont docs workflow`: the full method.

`whateverfont examples` lists finished projects, and `whateverfont examples NAME` prints the folder of one. Read an
example that is close to the request before you start, and copy from it.

## The loop

1. **Brief.** Run `whateverfont new DIR --name "Name" --preset PRESET --brief "the person's words"`.
   `whateverfont presets` lists the presets. In `DIR/BRIEF.md`, state what the font is for, how it should feel,
   what it must not look like, and which styles it needs. If the person did not say, choose and say so.
2. **Directions.** In `DIR/font.py`, define three families that read the brief differently and list them:
   `DIRECTIONS = [FAMILY, SECOND, THIRD]`. The generated file has a commented example. Start each from a
   different preset, or change at least two of contrast, proportions (`classical`, `width`, `xh`) and
   terminals (`flare`, `roundness`, `cut`). Three families that differ only in spacing are one direction.
   Give each a `description` of one sentence. Set `sample` to text from the person's project.
3. **Build.** `whateverfont build DIR`. Fix every warning: a warning that a glyph failed means that the glyph
   is missing from the font. If a line starts with `note:`, it is not a fault. It tells you, for example,
   that a family with an effect and axes gets static fonts and no variable font.
4. **Look.** Run `whateverfont look DIR --directions` and open the image: the rows must look different at a
   glance (if they do not at text size, they are one direction). Then, for each family, run `whateverfont look DIR --family "Name"` and
   `whateverfont look DIR --family "Name" --styles`, and open each image. Each command prints `proof: PATH`.
   Run `whateverfont probe DIR --family "Name" --problems` and fix what it lists. Without `--problems` it
   prints every measurement as JSON, and `--full` adds a table of every glyph.
5. **Fix.** Change a number, build, look again. Use `whateverfont look DIR --xray "aSg"` to see the skeleton of a
   letter that looks wrong. Stop when a pass finds nothing new. Write each decision in `BRIEF.md`.
6. **Review board.** Show the person a proof image first, so they see the result without a click. Then run
   `whateverfont board DIR --serve` in the background and give them the address it prints. Tell them to type
   their own text, move the sliders, press "Pick this one", write notes and press "Send to the agent". If
   you cannot keep a server running, give them `DIR/board.html`: that page lets them download the feedback.
   The person may also answer in the chat ("chunkier", "the g hangs too low"). That is feedback too.
7. **Revise.** Read `DIR/feedback.json`, or the person's words. Make the picked direction `FAMILY`, move its
   defaults to the slider positions the person left, apply the notes, and repeat from step 3. Keep the
   other directions in `DIRECTIONS` until the person has picked. Then remove them; the next build deletes
   their font folders.
8. **Deliver.** Point to `DIR/fonts/Name/`: `ttf/` to install, `woff2/` and the `.css` file for the web,
   `variable/` for one file with every style.

## Sharing a font

If the person wants the font in the public library (https://fonts.brianzhou.org/library/), ask for their
GitHub username. Then fork and clone the repository (`gh repo fork brianlzhou/whateverfont --clone`) and run,
inside the clone, `whateverfont library add DIR --github USERNAME`. It copies the design into `library/`,
checks it, and prints the commands that open the pull request. The font must be the person's own design,
under the Open Font License, with a name that no other typeface has: search for the name first. Do not open
the pull request without the person's word.

## What to check on a proof

- The paragraph has an even gray. Dark or light spots are spacing or weight problems.
- In `nnnonnoonnn` the white between letters is close to the white inside the `n`.
- `a c e s` end the same way. `b d p q` share one bowl.
- The boldest style keeps its counters open. The lightest style keeps its thin strokes visible.
- `S s a g e & @ 2 5` and the diagonals have no kinks, spikes or notches.

## Choosing numbers

The family's `base` is its default style. An axis pole changes parameters at the ends of an axis, and the
default value has no pole. To make the regular style heavier, set `weight` on the base, not on a pole.

| The person says | Change |
|---|---|
| bolder, lighter | `weight` on the base (82 is regular), and the `wght` poles to match |
| chunky | `weight` 112 to 135 on the base, `counter` near 300 and `width` near 1.04 so it stays open. With round ends, `cut="horizontal"` keeps spurs off `s e a`. `probe` warns above 165: look at `a e s g 5` there |
| wider for banners, narrower | add `Axis("wdth", "Width", 75, 100, 125, {75: {"width": 0.75}, 125: {"width": 1.22}})` |
| more elegant, more contrast | lower `contrast` (0.6 flare, 0.35 calligraphic) |
| friendlier, softer | raise `roundness`, raise `aperture`, raise `xh` |
| sharper, more serious | raise `flare` with a short `flare_len`, lower `apex`, `classical=1` |
| narrower or wider everywhere | `width` on the base (0.75 condensed, 1.15 wide) |
| more technical | raise `superness`, `cut="horizontal"`, `a_story=1` |
| a plain sans for an app or a site, "like" the open interface fonts | `preset("grotesk")` with `cut="flat"`, `xh` 540, `counter` near 265, `round_width` 1.17, `cap_width` 1.14, `spacing` and `word_space` 1.2; `arm` 1.2 and a wider `aperture` at the bold pole. Copy `whateverfont examples dayshift` |
| geometric, an `o` like a circle | `preset("geometric")` with `round_width` near 1.28 and `counter` near 262. Copy `whateverfont examples setsquare` |
| slab serif, typewriter | `serif` near 50 (slab length), `serif_weight` near 0.9; or start from `preset("typewriter")` |
| more classical | `classical=1`, lower `xh`, `stress` of 10 to 20 |
| handwritten, medieval | the `broadnib` preset: `stress` near 30, `contrast` near 0.35 |
| tighter, looser | `spacing` |

## Special requests

- **A version of an existing font** (rounder, bolder, slanted, narrower): use
  `whateverfont remix FONT.ttf --name "New Name" --round 46 --out DIR`. The result keeps the license of the font
  it started from and needs a new name. Tell the person both facts. If the command prints a note that the
  font declares no open license, pass that note on.
- **A font for another script** (Arabic, Devanagari, a language Latin does not cover): the engine has no
  recipes for it, so redraw an open font of that script with the family's pen:
  `whateverfont retrace SOURCE.ttf --name "Name Arabic" --pen DIR:"Family" --out DIR/fonts/NameArabic`, with
  `--effect` for a color family (`glow:size=80`, or `DIR/effect.py:function`). Read `whateverfont docs scripts`
  first. Choose a source with thin, even strokes, handwritten for a handwritten family. Tell the person that the
  letter shapes come from that font (only the pen and the effect are theirs), that the result keeps its license
  and copyright line, and that a reader of the script must check it. Look at every glyph the command flags. If
  it says numpy is missing, install it: `uv tool install 'whateverfont[trace]'` (or
  `pipx inject whateverfont numpy`, or `pip install 'whateverfont[trace]'` in a virtual environment). For
  Japanese, Chinese or Korean, add `--only japanese` (or `chinese`, `korean`) to keep the common characters,
  and tell the person how heavy the command says the pen could draw: dense characters leave little room for
  a heavy pen.
- **A monospaced or coding font:** start from `preset("mono")`. Every glyph gets one width, and `i l I 1 0`
  get their coding forms. Check `il1I| O0o {[()]} <= != =>` on a proof. For a typewriter, start from
  `preset("typewriter")` (slab serifs, round ends). The presets are `grotesk`, `humanist`, `geometric`,
  `flare`, `glyphic`, `rounded`, `broadnib`, `condensed`, `mono`, `technical` and `typewriter`.
- **A stencil, an engraved, a shadowed, a striped or a hand-cut look:** wrap the recipes with an effect from
  `whateverfont.effects` (`stencil`, `inline`, `outlined`, `shadow`, `stripes`, `rough`). See `whateverfont docs effects`.
- **A neon, painted, mosaic, dotted or banded color font, or a font "like" a painting:** use a color
  effect (`glow`, `painted`, `mosaic`, `dotted`, `banded`, `layered_shadow`) and give the family `palettes`.
  Keep the whole set (`latin()`) unless each glyph is heavy: for brush marks (`painted`), keep it small with
  `latin().only()`, or `latin().only(vietnamese=True)` for Vietnamese text (`greek=True`, `cyrillic=True`
  for those). For a look that no effect gives, write one with `effects.wrapped`. Take the colors and the
  kind of mark from the description of the painting; do not trace an image.
- **A picture font** (birds, icons, ornaments): each recipe draws a picture with `g.shape` or `g.polygon`.
  Set `ascent` and `descent` on the family if the pictures are taller than letters. See `whateverfont docs effects`.
- **Decorated or illuminated capitals:** wrap the recipes with `whateverfont.ornament.illuminate` and give the
  family `palettes`. Copy `font.py` from `whateverfont examples wassail`. Keep the plain text font as a second family.
  Tiles follow the width of each letter. For a tidy grid, pass `equal=880` (square tiles; the widest letters
  shrink a little) or `equal=True` (every tile as wide as the `W` tile).
- **A font "like" a commercial typeface:** work from the description of the genre. Never open, trace or
  measure the commercial font's files, and never reuse its name.

## Honesty

Tell the person what the font has and what it lacks. Italics are slanted romans, there is no hinting, and
kerning is automatic. Latin, Greek and Cyrillic are drawn (800 code points: with Vietnamese, Pinyin, some
African letters, modern Greek, the Cyrillic of Russian, Ukrainian, Serbian and Kazakh, currency, math, arrows
and fractions); other scripts are retraced from an open font. Nobody who reads Greek or a Cyrillic language
has reviewed those letters yet: say so if the person needs them. Every font with the whole set (`latin()` or
`mono()`) has the `frac`, `sups`, `subs`, `zero` and `case` features. A small set from `latin().only()` has
none of them. The default figures are tabular, and a font that is not monospaced has `pnum` for proportional
ones. `Family(figures="proportional")` turns that around for a text face: `tnum` then gives the tabular
figures. Point out the letters you think are weakest.

`whateverfont look` and `whateverfont board` build the project again only when something changed, and print
`built: DIR` when they do. `whateverfont build --force` always builds.

Useful `look` options: `--text "one line\nanother line"` for your own text, `--name NAME` so a proof does
not replace the last one, `--palette NAME` and `--bg "#101216"` for a color font on a dark ground.
`font.py` may import Python files that sit next to it.
