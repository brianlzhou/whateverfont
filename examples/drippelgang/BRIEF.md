# Drippelgang

## Brief

Make me a font for a Halloween party. Dip every letter in slime and let it drip. Spooky and fun, no gore.

- **What is it for?** One or two lines at a large size: a party invitation, a poster for a school event, a sign on the door. Not for running text. (I chose this.)
- **What should it feel like?** Spooky, gooey, fun. It must say Halloween at a glance and still read as letters. (I chose this.)
- **What must it not look like?** Blood or gore, a distressed horror font that is hard to read, or a plain font with a Halloween picture beside it. (I chose this.)
- **Which styles?** One style in each family. Drippelgang is a color font with four palettes. Drippelgang Ink is the same letters in one color. A color font has no variable file. (I chose this.)

## Decisions

Write down each design decision and why you made it, newest last.

1. **One idea: every letter is dipped head first in goo.** The top of each letter is coated down to a wavy line. Drips run down the strokes from that line, and some hang off as drops. I weighed slime, a carved pumpkin with a glow, and bony letters with cobwebs. Goo works on every letter, accent and sign in the same way, as snow does in Last Bell Snow. A carved face or a cobweb only fits a few letters.
2. **The effect is my own.** `goo.py` holds `dipped`, written with `effects.wrapped`. No stock effect coats the top of a letter or hangs drops. I worked from my own description of dripping goo. I did not open, trace or sample an image.
3. **Round, heavy letters.** The base is the `rounded` preset at weight 138, with `xh=530`, `counter=300` and `spacing=1.08`. Round ends match the round drops. A heavy stem has room for a drip inside it. The extra spacing keeps the swollen goo of two letters apart.
4. **Four layers: shade, letter, goo, shine.** `shade` is the whole silhouette. It shows as a thin shadow under the edge of the goo, so the goo sits on the letter and does not look painted on. `shine` is a short gloss streak on each coat and a spot on each drop. All four are flat colors, as COLR version 0 requires.
5. **The bottom layer is the whole silhouette.** The engine kerns a color glyph by its bottom layer. With the drops in that layer, a drop under the arm of a T keeps its distance from the next letter.
6. **Small parts are coated whole.** A dot, an accent, a period or a dash is too small to coat in part. Each one is all goo, so the dot of an i and the marks of `é ü ǘ` are goo color.
7. **The coat follows the x-height in tall lowercase letters.** The bowl of `b`, the arch of `h` and the bowl of `d` get the same coat as the `n` and `o` beside them. Without this, a word had coats at two heights.
8. **A drip that runs down to the foot covers the whole stem.** A narrow green stream in the middle of a purple stem split the stem in two at text sizes: `i` and `d` read as two thin strokes. The goo now covers the full width of the stem, and its drop hangs from the foot.
9. **No drip runs to the foot of a lone stem, and drops below the baseline are short.** An `i` with a drop under it read as a `j` at 30 px. The `i l I 1` get short drips only. A drop below the baseline is at most 45 units plus its round end. A drop under an arm or a bar (`T F r 7`) may hang 120 units.
10. **Drips only where they read as goo.** A drip must sit on the coat and on the stroke over its whole width. A drip at the edge of a stroke read as an outline. A drip stops above a round edge, such as the bottom of an `o`. A drop into a counter keeps three quarters of the counter open.
11. **Four palettes, each with its own ground.**
    - `Slime`: violet letters, lime goo. Show it on dark purple `#1C0E2B`. It also reads on white.
    - `Pumpkin`: orange letters, candle-yellow goo. Show it on near black `#120A05`. On white the yellow goo is pale.
    - `Black Cat`: near-black letters, orange goo. Show it on white `#FFFFFF`. This is the palette for an invitation printed at home.
    - `Ghost`: off-white letters, mint goo. Show it on midnight blue `#0F1A2C`. It does not work on white, by design.
12. **Drippelgang Ink, the one-color cut.** It is the letter and the goo as one shape. A thin white line runs under each lower edge of the goo, so the coat and the drips still show in one color. This is also the outline that programs without color fonts show for Drippelgang.
13. **Full character set.** `latin()`: 605 characters and the engine's OpenType features (`frac`, `sups`, `case`, `zero` and the others). Drippelgang is 314 KB as WOFF2, and Drippelgang Ink is 180 KB. `ascent=955` keeps the goo on the marks of `Ẫ Ǘ` inside the line. The drops stay above -250, so the family needs no `descent`.
14. **Three workarounds for Skia** (all in `goo.py`).
    - Skia could not subtract the closed outline of the `c` from the outline. The fillet where a drop leaves a stroke now tries three sizes and skips the fillet if all three fail.
    - The white line of the one-color cut has no width where the goo has a vertical edge. Skia left hairlines there. The line is shrunk and grown by 3 units to drop them.
    - Shrinking an outline can fail. `closed` and `_thin` keep the shape as it was when it does.

## Weak points

- The goo of a letter is the same each time the letter appears. The two `T` in "Trick or Treat" and the two `H` in "HAUNTED HAYRIDE" are twins.
- The drips are random within rules, so some letters get a drenched stem and others do not. `H`, `T`, `B`, `E`, `d` and `k` have one. A neighbor such as `N` has none.
- Below about 30 px the gloss and the shadow become specks. Drippelgang Ink looks distressed at text sizes because its white lines turn into noise.
- `Pumpkin` on white and `Ghost` on white are weak. Use them on their dark grounds.
- Accents, dots and periods are all goo color. A line of punctuation is mostly goo.
- The letterforms are the engine's rounded sans. The `G`, `g` and `&` are plain, and the Halloween feel comes from the goo, not from the letters.

## Feedback

Notes from the review board go here, with the date.
