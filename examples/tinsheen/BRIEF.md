# Tinsheen

## Brief

Make me a chrome font, like the shiny metal logo on an arcade cabinet from the year 2000.

- **What is it for?** One or two words at a large size, from about 80 px up: a logo, a title screen, a poster, a sticker, a high score. It is not for running text. (I chose this.)
- **How should it feel?** Loud, fast and shiny. The letters are polished metal that reflects a pale sky, a sharp horizon and dark ground. (From the request.)
- **What must it not look like?** A soft gradient, a blurry 3D render, or thin and elegant letters. Every tone is a flat band with a crisp edge, and the letters are heavy and leaning. (From the request. A color font in this engine has no gradients.)
- **Which styles and palettes?** Two families with one style each: Tinsheen, solid chrome letters, and Tinsheen Line, the same letters hollow. Four palettes, each drawn for its own ground: Chrome, Gold, Magenta and Lime. (I chose this.)

## Decisions

1. **A color font with an effect of its own.** No stock effect gives a reflection with a horizon, a rim and an outline, so `chrome.py` holds two effects written with `effects.wrapped`: `chrome` for Tinsheen and `chrome_line` for Tinsheen Line. I worked from the words of the request. I did not open, trace or measure any font, logo or picture.
2. **The base letters.** The `grotesk` preset with `weight=170`, `width=1.24`, `counter=330`, `xh=540`, `slant=10`, `contrast=0.9`, `aperture=0.45`, `superness=0.3` and `spacing=1.15`. Low contrast and a wide body give each letter enough metal to show the bands. I tried weights from 140 to 196. At 182 the 5, 6 and 9 close up and the & crumples. At 196 the a and the 8 also get notches. 170 is the heaviest weight that stays clean, with the letters of decision 9 redrawn.
3. **The layers, from bottom to top.** Tinsheen has 12 layers in each glyph:

   | Layer | What it is |
   |---|---|
   | `outline` | The letter grown by 24 units on every side, in a dark color. |
   | `ground0` | Below y 120: the baseline and the descenders. The lightest ground. |
   | `ground1` | 120 to 195. |
   | `ground2` | 195 to 250. |
   | `ground3` | 250 to 290, just under the horizon. The darkest ground. |
   | `sky0` | 290 to 314, just over the horizon. The palest sky. |
   | `sky1` | 314 to 350. |
   | `sky2` | 350 to 400. |
   | `sky3` | 400 to 470. |
   | `sky4` | 470 to 590: the top of the lowercase. |
   | `sky5` | Above 590: the tops of capitals, ascenders and figures. The deepest sky. |
   | `rim` | A band 13 units wide just inside the edge, and 2 units past it, in a bright color. |

4. **The horizon is at 290 units in every glyph.** That is 41% of the cap height (700) and 54% of the x-height (540), so it crosses the middle of capitals and lowercase alike. The band edges are fixed heights in font units, so on a line of mixed case the horizon and every band run straight through all the letters, and a word reads as one piece of metal. Capitals reach two more sky bands than the lowercase.
5. **The bands are thin near the horizon and wide away from it.** In the sky they are 24, 36, 50, 70 and 120 units tall, and in the ground 40, 55 and 75. The light changes fast at the horizon and slowly at the top and the bottom, as in a curved mirror. The edge of `sky5` (590) lies above the x-height and its overshoot (551), so no lowercase letter gets a sliver of it.
6. **No slivers and no seams.** A piece of a band less than 20 units tall (the tip of a round that just crosses an edge) joins the band next to it. Each band reaches 6 units up under the band above it. Where two layers only meet along an edge, a browser lets the layer under them show through as a hairline.
7. **Marks get bands of their own.** An accent or the dot of an i floats above the letter, wholly in the deepest sky, and as one flat color it looked dull. So each mark above a letter gets three bands of its own, from bottom to top `sky1`, `sky3` and `sky5`, or two for a mark less than 90 units tall. A mark below a letter (a dot below, a comma below) gets `ground0`, `ground1` and `ground2`.
8. **The letter is cleaned before it is banded.** The rim traces every flaw of the outline, so the effect first fills counters smaller than 1500 square units (a closed hook leaves a pinhole), drops pieces of ink smaller than 400, and removes segments shorter than 0.05 units (one in the Greek ξ made Skia fill the whole rim). Then it grows the letter by 9 units and shrinks it back, and shrinks and grows it, which smooths small spurs. A glyph keeps its own outline when this would open or close a counter or change its area by more than 5%. Holes in the outline smaller than 900 square units and in the rim smaller than 400 are filled.
9. **Ten letters are redrawn in `font.py`.** Each one is the stock recipe with a few numbers changed, and the accented and Cyrillic letters drawn from them follow.
   - `Å Ů`: the stock ring closes into a dot at this weight, so the ring has a lighter stroke (0.5) and is 18% of the cap height tall.
   - `&`: the upper loop is wider (17% to 64% of the width), and its whole stroke has one width (0.8). The stock loop swells at its sides and gets small steps inside.
   - `a`: the bowl is a little lighter (0.9) where it turns at the left, and the handle there is longer.
   - `S s $`: the bowls are lighter where they turn into the spine (0.86, and 0.76 in `s`). Without this the inside of each bowl gets a spur.
   - `3`: a short bar joins the two bowls, so their ends do not stick out of each other.
   - `6 9`: the bowl is smaller (29% of the cap height, stock 31.5%), so the slot under the hook stays open.
10. **Four palettes, each drawn for its own ground.** Chrome is the main palette.

    | Palette | Ground | Sky, horizon to top | Ground, bottom to horizon | Rim | Outline |
    |---|---|---|---|---|---|
    | Chrome | deep blue `#0A1A4F` | `#F8FCFF` to `#3E7EDF` | `#A3AACB` to `#14142A` | `#FFFFFF` | `#02040C` |
    | Gold | dark wine `#2A0710` | `#FFFADF` to `#9E5A08` | `#E2A04E` to `#341703` | `#FFF4C6` | `#160800` |
    | Magenta | black `#000000` | `#FFEAF8` (pink) to `#7F27C2` (purple) | `#E54FB6` to `#25062F` | `#FFF0FA` | `#0C0012` |
    | Lime | black teal `#03181C` | `#F7FFDA` (lime) to `#0F7F88` (teal) | `#2BB5AA` to `#04252A` | `#F8FFE8` | `#001012` |

    The engine fills `grounds` in `fonts/index.json` only for a palette that white paper would hide. These palettes all show on white, so that field is empty. The site must take the grounds from this table, or from `chrome.GROUNDS`.
11. **Tinsheen Line is the same letters, hollow.** A chrome tube 46 units wide runs inside the edge of each letter, with the same bands at the same heights. A dark band holds it: 24 units outside the edge and 10 units inside the tube. A rim 9 units wide runs along the outer edge. The middle of the letter is empty, so the ground shows through. Where the hollow would be smaller than 3000 square units (a thin mark, a small figure in a fraction) the tube fills it.
12. **The outline is the first layer.** The engine kerns a color glyph by its first layer, so neighbors keep clear of each other's outlines. `spacing=1.15` leaves a gap of dark ground between the outlines.
13. **`ascent=975`.** With the outline, the marks of capitals (`Ä Ǘ`) reach 958 units, above the default top of the line (940).
14. **Full character set.** `latin()`: 800 code points and 847 glyphs in each family, with every OpenType feature of the engine. Tinsheen is 343 KB as WOFF2 and Tinsheen Line is 445 KB. The project builds in about 40 seconds.
15. **The name.** I searched for "Tinsheen", with "font", with "typeface", and with "game", "company", "product" and "app". I found no typeface, game, product or company with that name. I rejected Brightwork, Skyplate, Mirrorsky, Glintway, Skysheen, Sheenrise and Gleamrise, because a company, a product or a game already uses each of them.

## Weak points

- The `j` (and `ĵ ȷ ј`) has a long tail that runs under the letter before it: the advance is 352 units and the drawing 639. With the outline, the tail comes close to a round letter on its left.
- Small bumps remain inside some bowls where the heavy stroke turns fast: the right side of the bowls of `3` and `R`, and the joins of `S s`. The smoothing makes them soft, but the rim shows them above about 250 px.
- The grave and the acute are short and heavy at this weight, so above a capital they look like small diamonds.
- The slot under the hook of `6` and `9` is narrow. The outline fills it with dark.
- The bands are steps, not a gradient. At 80 px the four thin bands next to the horizon start to merge. Below about 40 px the bands blur and the outlines crowd. This is a display face.
- The dark outline almost disappears on the black grounds of Magenta and Lime. There the rim alone holds the letters apart.
- The bands are fixed heights for every glyph, so a superscript is all sky and a subscript is all ground.
- The figures are tabular by default, so `1` sits in a wide cell. The `pnum` feature gives proportional figures.
- In Tinsheen Line, thin parts (marks, the bars of small figures, the ring of `Å`) are solid tubes with no hollow.
- Nobody who reads Greek or a Cyrillic language has reviewed those letters.

## Feedback

Notes from the review board go here, with the date.
