# Gilt

## Brief

Make me a font like Klimt's The Kiss. Gold everywhere: letters built from little gold tiles, with some of those black-and-white rectangles and small spirals and colored circles mixed in like on the robes. Rich and decorative, for a wedding invitation heading and a perfume label.

- **What is it for?** One line at a large size: the names on a wedding invitation, the name on a perfume label. Not for running text. (The person said this.)
- **What should it feel like?** Golden, ornate, precious. (The person said "rich and decorative".)
- **What must it not look like?** A plain gold gradient, a pixel font, or a letter that the ornament makes hard to read. (I chose this.)
- **Which styles?** One style in each family, with four palettes: Gold, Gold on Dark, Silver, Rose. A color font has no variable file. (I chose this.)

## Decisions

Write down each design decision and why you made it, newest last.

1. **A color font with a custom effect.** The stock `mosaic` effect gives gold tiles only. The brief also asks for rectangles, spirals and circles, so `klimt.py` holds an effect written with `effects.wrapped`. I worked from the description of the painting. I did not open or trace an image.
2. **Three directions, one for each reading of the painting.**
   - `Gilt`: Roman capitals and a humanist lowercase (the `flare` preset, with the flare set to 0). An even mix of all four motifs. This is `FAMILY`, for the invitation heading.
   - `Gilt Robe`: wide, squared letters (the `geometric` preset with `superness=0.5`). Tall tiles and many black and white rectangles, like the man's robe. For a label in capitals.
   - `Gilt Bloom`: round letters (the `rounded` preset). Small tiles and many colored circles, like the woman's robe.
3. **Weight 144 to 150, not heavier.** A stem must be wide enough for a circle with rings, so the letters are bold. Above weight 165 the engine breaks the `1`, `a`, `9`, `&` and `5`, and at 165 the `s`, `f`, `j` and `t` get kinks. Weight 150 keeps the forms clean and still fits a circle 52 units in radius.
4. **`contrast=0.62` and `flare=0` on Gilt.** Thin horizontals (the arms of `E` and `F`) could not hold a row of tiles, and the flare made arrow-shaped ends on `C`, `a` and `e` at this weight.
5. **`spacing=1.08`.** The dark edge adds 7 units to each side of a letter, and heavy letters need more room.
6. **Layer order: edge, grout, gold tiles, rectangles, round motifs.** The edge is the letter grown by 7 units, and the grout is the whole letter. The silhouette is solid under the ornament, so the word reads first and the ornament second.
7. **Tiles in courses of upright rectangles, in four golds.** Upright rectangles are the mark of the man's robe. A slow wave picks the gold, so the tone drifts in patches like leaf, not like noise.
8. **Rectangles must be whole, with gold on every side.** A white rectangle at the edge of a letter reads as a notch on white paper, and a black one does on a black label. Inside a run the rectangles are narrow, so that two or three fit across a stem.
9. **Circles and spirals sit only where they fit.** The effect shrinks the letter by the radius of the motif and puts centers in what remains. Each new motif goes as far as possible from the ones already placed.
10. **A `Gold on Dark` palette.** The `Gold` palette has a dark edge, which disappears on a black label. `Gold on Dark` has a bright gold edge. I checked it on the review board with the dark background.
11. **Two workarounds for engine problems** (both are in `klimt.py`).
    - `outline.dilate` lost the counter of the Gilt Robe `0` at amount 7, so the counter filled with the edge color. `grow` grows the outside and shrinks the counters separately.
    - The `6` and `9` of Gilt Robe have a hairline crack with a small pocket where the bowl joins the stem. `sealed` closes cracks and fills pockets before the effect runs.
12. **Full character set.** `latin()`: every letter, sign, arrow and fraction of the engine, so no character falls back to
    another font. Each family is about 600 to 770 KB as WOFF2, and the whole project builds in about a minute.
    `sealed` keeps the ink as it is when Skia cannot shrink an outline (it failed on the `Ə` of Gilt). Each family
    sets `ascent` (955 to 970), so the marks of the heavy capitals (`Ż Ố Ǘ`) are not clipped.

## Weak points

- `a` in Gilt has a cramped bowl. `&`, `S`, `s` and `t` have small kinks that the engine makes at this weight.
- `g` has a flat, short tail in all three families. `5` in Gilt Robe has a gap where the bowl meets the stem.
- `+ = < > - *` are too thin to carry ornament. They get tiles only.
- Below about 40 px the spirals and rings turn into dots. This is a font for large sizes.
- The ornament of a letter is the same each time the letter appears: the two `n` in "Anna" are twins.

## Feedback

Notes from the review board go here, with the date.
