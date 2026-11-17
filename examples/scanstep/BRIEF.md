# Scanstep

## Brief

Make me a pixel font like the text in an 8-bit video game.

- **What it is for:** the text of a game, or of a page that looks like one: a title screen, "PRESS START", a
  score line, a menu, a dialog box. Also two or three lines of plain text at 16 or 24 pixels. (I chose this.)
- **How it should feel:** chunky, crisp and exact, like text on an old television set. Every pixel is a square
  of the same size on one grid.
- **What it must not look like:** a smooth font with a pixel texture on top, soft or half pixels, stems of
  uneven width, or letters that work one at a time but not in a line.
- **Styles and palettes:** Scanstep, in one color, and Scanstep Color, with the same pixels, a hard shadow
  and a darker foot, in four palettes: Title, Dungeon, Handheld and Manual. One style in each family. A color
  font has no variable file.

## Decisions

1. **Eight pixels to the em.** One pixel is 125 units square. At 8, 16, 24, 32 and 48 px a font pixel covers
   a whole number of screen pixels (two at 16 px, three at 24 px, six at 48 px), so the edges stay sharp.
   Every point and every advance in both fonts is a multiple of 125. I checked this with a script over every
   glyph and every color layer. Only `.notdef`, which the engine draws, is off the grid.
2. **The rows.** The baseline is row 0. The x-height is 5 rows (625 units), capitals and ascenders are 7 rows
   (875), descenders 2 rows. A mark over a lowercase letter sits on rows 6 and 7, over a capital or an
   ascender on rows 8 and 9, with one empty row between mark and letter. The comma below Ș, Ț, Ķ and Ņ takes
   a third row below the baseline. The line is 1250 units above the baseline and 375 below: 13 rows.
3. **Stems two pixels wide, horizontal strokes one pixel tall.** On an old television a line one pixel wide
   smeared sideways, and a line one scanline tall stayed sharp. Seven rows have room for the three bars of an
   E only if a bar is one pixel tall. The stems make the font heavy: a stem is 2/7 of the cap height.
4. **Widths.** Capitals are mostly 7 pixels wide, so a counter is 3 pixels. The lowercase is mostly 6 wide,
   with counters of 2. `m`, `Ш` and `ш` are 8 wide with counters of 1, and `w` is 8 wide too. Figures are
   7 wide and tabular.
   Every glyph has one pixel of white after it, and the word space is 4 pixels. Kerning is off
   (`kerning=0`): a kern of a part of a pixel would leave the grid.
5. **Every character has a drawing.** I first wrote the sampler that the request describes
   (`pixels.sample`): the engine's outline, drawn with stems of 125 units, is laid on a grid of cells half a
   stem wide and one stroke tall, so a stem covers two cells. The grid is tried at 8 sideways shifts, the
   shift with the fewest half-covered cells wins, and a cell more than half inside the outline becomes a
   pixel. Straight letters came out right (`b d h l n o p q u`). At 7 rows the diagonals and curves did not:
   `k s v w x y z` had ragged rows, `A M N V W` lost their points, `& @ %` could not be read, and even `+ ■ ●`
   came out uneven. So I drew each character in `pixels.py`, as a game kept its letters: 356 drawings, 11
   small figures and 17 marks. The sampler stays in the effect for any glyph that has no drawing. In this
   build no glyph uses it.
6. **Accented letters are built by rule** from the drawing of the base letter and the drawing of each mark,
   from the Unicode decomposition (323 glyphs). A mark has a version for a base an even number of pixels
   wide and one for an odd width, so it sits exactly in the middle. `i` and `j` lose their dot under a mark.
   `ď ľ ť Ľ` take an apostrophe beside the ascender. `ķ ļ ņ ŗ` take a comma below and `ģ` a turned comma
   above. A Greek capital takes its tonos at the upper left. A Vietnamese tone mark goes up and to the right
   of a circumflex (the grave to the left). The horn of `ơ ư` fills the corner of the bowl and rises one row.
   Greek and Cyrillic letters that look like Latin ones use the Latin drawings (47). Fractions, `Ĳ` and `₨`
   are drawings set side by side with one column of white.
7. **Letters that must not be confused.** `0` has a dot in the middle, `O` has none, and `Ø ø` have a slash
   that pokes out at two corners. The `zero` feature gives a zero with a slash. `1` has a flag and a foot,
   `l` is a plain stem, `I` has bars. `5` has a flat top, `S` is round. `8` is round on the left, `B` flat.
   `rn` keeps a pixel of white between the letters, and `m` has counters of one pixel.
8. **Ł, ł, ø and Ø.** With two-pixel stems a slash of the same weight read as a crossbar: `Ł` looked like a
   `t`. Their slashes are one pixel wide and cross the stem on a diagonal.
9. **Scanstep Color has three flat layers:** `face` (every pixel), `lower` (the pixels on row 2 and below, in
   a darker color) and `shadow` (the pixels one column right and one row down that the letter does not cover).
   Each glyph has two pixels of white after it and the space is 5 pixels, so the shadow does not touch the
   next letter. The split at row 2 puts the darker color on the lower three rows of a capital and the lower
   three of five rows of a lowercase letter, the same band across a whole line.
10. **The palettes and their grounds.** The engine names a ground only for a palette that white would hide,
    so `GROUNDS` in `font.py` holds them all:

    | Palette | Face | Lower | Shadow | Ground | Ink beside it |
    |---|---|---|---|---|---|
    | Title | `#FFE45C` | `#FF8A1E` | `#B3123C` | night blue `#141A4A` | `#FFE45C` |
    | Dungeon | `#E9E1CC` | `#9E937D` | `#4B2D63` | black `#121014` | `#E9E1CC` |
    | Handheld | `#3B6634` | `#16361A` | `#86A43C` | pale green `#B6C65A` | `#16361A` |
    | Manual | `#DE3A2C` | `#981D1A` | `#CDB287` | cream `#F4EAD2` | `#2A2422` |

    Title is the one to show first. On the light grounds the shadow is a shade darker than the ground: a black
    shadow on cream was heavier than the red letters and filled their counters.
11. **The full set.** `latin()`: 800 code points and 847 glyphs in each family, with the `frac`, `sups`,
    `subs`, `zero`, `case` and `pnum` features. The WOFF2 files are 16 KB (Scanstep) and 52 KB (Scanstep
    Color), because a glyph is a few rectangles. A build of both families takes about 3 seconds.
12. **The name.** A scanline and the steps of a pixel diagonal. I searched for "Scanstep font", "Scanstep
    typeface" and "Scanstep game or company" and found no typeface, game or company with that name. My first
    choices were already the names of games, shops or fonts.

## Weak points

- Vietnamese capitals with two marks (`Ấ Ắ Ễ Ỗ` and the others), the Pinyin capitals `Ǖ Ǘ Ǚ Ǜ`, and the
  lowercase `ẫ ắ ằ ẳ ẵ ễ ỗ` rise one to three rows above the line: 27 glyphs. With tight line spacing they
  can touch the line above.
- A few small things use strokes one pixel wide: the ring of `Ů`, the slashes of `Ł ł Ø ø`, `™`, `☆`, `∞`
  and `≈`. Everything else is built from two-pixel stems.
- The small figures of superscripts and fractions have counters one pixel wide, and fractions are wide
  (15 or 16 pixels).
- The engine places a combining mark typed after a letter (the `mark` feature), the second of two stacked
  combining marks, and the slash of the `frac` feature by amounts that can be half a pixel off the grid.
  Precomposed letters are exact.
- With a large x-height and eight pixels to the em, text at 16 px looks as large as most fonts at about
  20 px.
- In Scanstep Color the lowercase is mostly the darker color, since three of its five rows are below the
  split.
- There is no kerning, so `AV`, `To` and `LT` keep the same one pixel of white as every other pair.
- Nobody who reads Greek, Cyrillic or Vietnamese has reviewed these letters yet.

## Feedback

Notes from the review board go here, with the date.
