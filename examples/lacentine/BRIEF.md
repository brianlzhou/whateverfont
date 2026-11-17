# Lacentine

## Brief

Make me a font for Valentine's Day, like a card glued on a paper doily. Lace edges and small punched hearts, and letters that still read.

- **What is it for?** A heading or a few words at a large size: a card, a bakery window, a school valentine, a sign for a February sale. Not for running text. (I chose this.)
- **What should it feel like?** Warm, sweet, homemade. It should say Valentine's Day at a glance. (I chose this.)
- **What must it not look like?** Kitsch that hides the letters, a font of heart pictures, or a script. The letters must read first and the ornament second. (I chose this.)
- **Which styles?** One style in each of two families. `Lacentine` is a color font with four palettes. `Lacentine Card` is the same letters in one color. A color font has no variable file. (I chose this.)

## Decisions

Write down each design decision and why you made it, newest last.

1. **One idea: a valentine made from card and a paper doily.** Each letter is cut from colored card and glued on a paper doily cut to its shape. The doily has a scalloped edge, a small eyelet in each scallop and a row of punched hearts. I chose this over four other ideas:
   - Hearts as counters and dots touch only the letters that have a counter or a dot.
   - A candy heart behind each letter makes a row of hearts of different widths, and it fights the width of `m` and `i`.
   - A box of chocolates says "chocolate" before it says "Valentine".
   - A ribbon through the strokes is hard to keep readable.

   The doily goes on every glyph, including the figures, the signs and the accented letters. It never changes the letter itself. I worked from my own description of a paper doily. I did not open or trace an image.
2. **Layers, bottom first: backing, doily, letter.** The letter is the top layer, whole and in one strong color, so the word reads first. The effect is `doily` in `lace.py`, written with `effects.wrapped`.
3. **Soft, round, heavy letters.** The `rounded` preset with `weight=142`, `counter=305`, `width=1.04` and `xh=520`. Round ends feel warm and homemade. The letter must be heavy enough to hold its own inside a doily that reaches about 119 units past it.
4. **The size of the doily.** The band is 100 units, with scallops of radius 27, eyelets of radius 6, and hearts 40 units wide, 55 units out from the letter. My first draft had a 74-unit band and 31-unit hearts close to the letter. At 75 px the holes took half of the band, and the doily washed out to a pale pink haze. Now the paper next to the letter is solid, so every letter keeps a clear white outline at small sizes. The hearts are far apart and show above about 100 px.
5. **Clean counters.** A counter that the doily nearly closes leaves a ragged scrap of ground (the lower bowl of `B`, the bowl of `g`), so the effect fills any counter narrower than about 70 units. An eyelet is cut only where its scallop is on an edge of the paper. Without this rule, filled counters showed a stray ring of dots.
6. **The doily sets the spacing.** The effect gives each glyph sidebearings measured from its doily: 44 units of ground between two doilies before kerning. Neighbors never overlap, because the doily of one letter would cover the punched hearts of the other. Kerning measures the bottom layer (the backing), and the `spacing=0.45` in the base only sets its target. After kerning, the doilies of `nn`, `HH` and `oo` stand about 60 units apart. `To`, `AV` and `LT` get a negative kern, so one doily tucks under the arm or the slope of the other. The figures are proportional by default (`figures="proportional"`), so "Feb 14" has no gap after the tabular `1`. The `tnum` feature gives tabular figures, widened by the doily.
7. **A backing in the color of the ground.** The doily is white, and white paper hid it. On white, the Valentine and Pink lines looked like widely letterspaced letters. Under the doily there is now its silhouette, 8 units larger, in the color of the palette's ground. On that ground it does not show. On white or any other paper, it rims the doily and fills the punched hearts, so the doily still shows.
8. **Four palettes, each for its own ground.** Show each palette on this ground (also in `GROUNDS` in `lace.py`):

   | Palette | Letter | Doily | Backing | Ground | Ink for labels on that ground |
   |---|---|---|---|---|---|
   | Valentine | red `#C3142D` | white | `#F4BFCB` | pink `#F4BFCB` | `#1B1A17` |
   | Candy | red `#D3203E` | pastel pink, butter, mint, lilac | white | cream `#FFF8EE` | `#1B1A17` |
   | Pink | pink `#E8467C` | white | `#B3122E` | deep red `#B3122E` | `#F1EEE7` |
   | Chocolate | dark chocolate `#4A2216` | gold `#E2BC6E` | `#2B150E` | cocoa `#2B150E` | `#F1EEE7` |

   The engine names a ground in `fonts/index.json` only when white paper would hide a palette. It gives Valentine and Pink a dark slate (`#262A31`), and nothing for Candy and Chocolate. The table above lists the grounds the palettes were made for.
9. **Candy: a different pastel for each letter.** The doily has four keys (`lace0` to `lace3`), and each glyph takes one by its name. In Candy they are four pastels, so a word looks like a row of candy hearts with red print. In the other palettes the four keys have one color.
10. **Combining marks take the letter's color.** The marks (U+0300 and on) get no doily. Without layers they took the text color, so `G` + U+0301 (for `Ǵ`, which is not in the set) showed a black acute above a red letter. They now have one `letter` layer.
11. **A taller line.** `ascent=1000` and `descent=-330`, because the doily reaches about 119 units past the letter. A few doilies reach farther: the one of `Ǖ` reaches 1054, and the one of `Ģ` reaches -350. The font's Windows metrics (1054 and 350) hold both, so nothing is clipped.
12. **`Lacentine Card`: the same letters without the doily.** It is one color, for the rest of the card, and for any place where the color font is too much.
13. **The whole set.** Both families use `latin()`: 605 characters and the engine's OpenType features. `Lacentine` is 455 KB as WOFF2 (3.1 MB as TTF), and `Lacentine Card` is 39 KB. The project builds in about 40 seconds.
14. **The name.** "Lacentine" joins lace and Valentine. A web search found no typeface, brand or product of that name. I rejected "Doily" (a font of that name exists), "Mash Note" (a font of that name exists) and "Heartlace" (shops use it as the name of a ring, a necklace and a lingerie set).

## Weak points

- The punched hearts read as hearts only above about 100 px. At 30 to 60 px they are a dotted band, and below about 20 px the doily is a pale halo around the letters. The letters stay clear at every size.
- The doily makes a line about 1.28 times as wide as the same line in `Lacentine Card`. It also needs a line height of about 1.33. With a CSS `line-height` under about 1.2, the doilies of two lines overlap.
- On white, the Valentine palette is quiet: the doily shows only as a pink rim and pink hearts. It is made for its pink ground.
- In Candy, each letter always gets the same pastel: every `e` is butter yellow, every `s` lilac. A doubled letter (`ee`, `ss`) has two doilies of one color side by side.
- Letters from the engine's stock recipes at this weight: the grave on capitals (`À È`) is a short, heavy stub, `ß` has a notch where its two bowls meet, and `&` has a small notch at its lower join.
- The kerning works on the doilies, not on the letters. `To` and `LT` tuck in less than they would in a plain font, and the white under the arm of `T` stays large.

## Feedback

Notes from the review board go here, with the date.
