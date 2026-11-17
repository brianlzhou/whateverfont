# Kanagawa

## Brief

Make me a font like Hokusai's Great Wave off Kanagawa. Deep Prussian blue letters with white foam, those little claw-like curls coming off the tops of the letters, on a cream paper feel. It's for the title of a poster, so mostly capitals, but give me lowercase and numbers too.

- **What is it for?** The title of a poster: a few words, set large. Capitals first, with lowercase and figures.
- **What should it feel like?** Woodblock, stormy, hand-cut.
- **What must it not look like?** Snow or icing on the letters, a comic "splash" font, or a traced copy of the print.
- **Which styles?** The person did not say. I chose one style, Regular, in each direction. A color font cannot be a variable font, and a poster title needs one weight.

## Decisions

- **A custom effect, `breaker` (in `breaker.py`).** No shipped effect gives a foam crest. Each part of a letter is a wave: a dark key line, Prussian blue water, two or three pale streaks that run parallel to the outline (the stripes of the wave), a white foam cap at the top whose lower edge runs down in curved fangs, hooked claws that stand on the crest and curl to the right (the way the wave breaks in the print), a few dots of spray, and a cream sheet behind everything.
- **Colors from the description of the print, nothing traced.** Key line `#081B33`, water `#113A66`, streaks `#6C9BBE`, foam `#FCF8EC`, paper `#EADBB4`. The foam is a little whiter than the paper so that it reads as white on cream.
- **Three palettes.** `Print` (the blues on a cream sheet), `Night` (a dark sky and moonlit foam), `Bare` (the print's colors with a transparent sheet, for a poster that is already cream).
- **The cream sheet is a halo, not a rectangle.** A rectangle behind each letter would cover the neighbor in kerned pairs such as `AV` and `Ty`. The halo is 34 units wide, less than the closest distance the kerning allows, and it fills the counters.
- **Three directions.** `Kanagawa` (heavy flare serif with Roman capitals, like a cut block), `Kanagawa Brush` (broad pen, slanted 8 degrees, thick and thin), `Kanagawa Swell` (fat, round, even strokes). I recommend `Kanagawa`: its flared stems give the claws a wide crest to stand on and its capitals are the calmest.
- **Weight 165 and `counter=300`** for `Kanagawa`, so that the stems hold a key line, two streaks and the foam, and the counters stay open.
- **Round dots (`dot="round"`).** A diamond dot under a foam cap looked like a gem.
- **Small signs get foam and no claws** (comma, period, quotes, dashes, asterisk). With claws they looked like small animals.
- **Full character set** (`latin()`): every letter, sign, arrow and fraction of the engine, so no character falls back to
  another font. Each family is about 520 to 610 KB as WOFF2, and the whole project builds in about a minute.
  Each family sets `ascent` and `descent` (1005 to 1025, -270 to -300): the foam and the halo carry the marks
  of the capitals (`Ż Ǘ`) and the case forms of the brackets past the default line.
- **Engine workarounds, all in `breaker.py`:**
  - The bottom color layer is the bare letter with its claws, hidden under the sheet, because the engine kerns a color glyph by its bottom layer.
  - The plain glyph gets four specks of four units at the outermost points of the sheet, so that its box covers every color layer. `whateverfont look` draws layers outside that box, but some renderers clip them to it.
  - Skia could not shrink the grown sheet of the `^` of Kanagawa Swell. The sheet is then grown by the paper width only.
- **`breaker.py` sits next to `font.py`.** `font.py` imports it as `from breaker import ...`: WhateverFont puts the project's folder on the import path when it loads `font.py`.

## Known weak points

- Below about 30 px the claws and streaks close up. This is a title face.
- `Kanagawa Brush`: `whateverfont probe` reports that `j` and `/` are wider than their advance (the slant), and `f)` and `(j)` sit very close.
- `Kanagawa Swell`: the counters of `a e 5 6` are small.
- The spray dots are white on cream and are faint in the `Print` palette. They show well in `Night`.
- `whateverfont look` shows only the first palette. I checked `Night` on the review board in a browser.

## Feedback

Notes from the review board go here, with the date.
