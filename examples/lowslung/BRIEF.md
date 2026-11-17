# Lowslung

## Brief

Make me a wide, flat sans for the name of a studio. Low and stretched, like the lettering on the back of a sports car.

- **What it is for:** the name of a studio, a label or a shop. One to three words at 60 to 160 pixels, in
  capitals or in mixed case, and a short paragraph at 18 pixels under them.
- **How it should feel:** low and stretched. The letters sit wide on the line and their strokes end
  flat.
- **What it must not look like:** a narrow headline face, or a futuristic face with broken letters.
- **Styles:** Light, Regular, Medium, Bold and Extrabold, and one variable font with a weight axis (300
  to 800) and a width axis (70 to 125). No italic: the request did not ask for one.

## Decisions

- I drew three directions first. A `grotesk` drawn wide (`superness` 0.5). A `technical` face drawn
  wide (`superness` 0.8, single-story `a`). An oval one (`width` 1.5, `superness` 0.25, `aperture`
  0.45, `cap` 660). The oval one looked like any wide sans: its rounds lost the flat look. In the
  technical one the single-story `a` read like a `d` without its ascender in "and". I kept the
  `grotesk` start and took the square rounds of the second one. The other two are gone.
- `width` 1.45 makes every counter 45% wider than the engine's normal. `superness` 0.68 squares the
  rounds. More than that made the `o` look like a label on a machine.
- `xh` 560 against a `cap` of 700. The x-height is 80% of the capitals, so mixed case stays large next to
  a word in capitals. `asc` is 760: at 740 the dot of the `i` nearly touched the stem in the bold.
- The regular is at `weight` 90, above the engine's 82. A wide letter has more white around the same stem
  and looks lighter than a narrow one.
- `spacing` 1.22 and `word_space` 1.2. Wide capitals need room between them.
- `aperture` is -0.6, below the usual range. At 0.2 the ends of `c e s a C G S 2 3 5` left the curve at
  about 40 degrees, and the horizontal cut turned them into wedges that grew with the weight. At -0.6
  these letters curl in until their ends point up or down, and the flat cut is square to the stroke.
- The hooks of `r g t f j J ƒ` end traveling sideways. They get a vertical cut, because a horizontal cut
  runs almost along the stroke there and leaves a spike. `f j J ƒ` are drawn with 0.8 more aperture
  than the family and `t` with 2.0 more, so their hooks do not curl back.
- `6` and `9` are redrawn. The stock figure ends on a slope, which was a spike in this width. Here the
  stroke rises from the bowl, turns and runs flat to a vertical cut.
- `ß` is redrawn with a lower round at the top. The stock one was as tall as it was wide, folded, and was
  left out of the variable font.
- The acute, the grave and the double acute end flat. With square ends they were diamonds in the bold.
  The two strokes of the double acute keep a gap of half a stroke. The ring of `Å ů` is thinner, and larger
  when its counter would close. The dot of `i` and `j` is 0.86 of the stock dot.
- Weights: Light 58, Regular 90, Medium 107, Bold 140, Extrabold 156. At 800 `counter` goes to 285, `arm`
  to 1.15 and `aperture` up by 0.35, so the `e` and the `a` stay open. `cap_weight` is 1.05, so the
  capital stems of the Extrabold stay at 164, under the 165 where the engine starts to close counters.
  At weight 160 the `e` closed to a slit and the `&` filled in.
- The width axis runs from 70 (`width` 1.0, a sans of normal width) to 125 (`width` 1.8). The numbers are
  close to the real change in the counters: 1.0 is 69% of 1.45, and 1.8 is 124%. The default is 100, the
  wide design, so a browser that sets the width from a normal `font-stretch` still draws it wide. At 70
  `aperture` goes up by 0.3, because the narrow letters have less room.
- `ascent` is 955. The Vietnamese capitals with two marks reach 944 in the Extrabold.
- Figures are proportional by default, for headings and dates. The `tnum` feature gives tabular ones.

## Weak points

- `S s`: the inner corners where the bowls meet the spine are tight. In Bold and Extrabold there is a notch
  of a few units inside the upper bowl.
- `a`: a small kink inside the bowl at the lower left in the heavy weights.
- `&`: the left side of the upper loop has a corner. `5`: the end of the flag stands out a little from
  the bowl.
- At the wide end (`wdth` 125) the ends of `C S e` are sharper. At the narrow end in Extrabold, `a e &`
  are crowded.
- The closed apertures make `e` and `c` close to `o` in the Light at 13 to 16 pixels. The face is for
  large sizes.
- Greek in Extrabold: the loop of `γ` nearly closes, and the tails of `ζ ξ` have a small notch.
- The tilde of `Ñ ñ` is large.
- There is no hinting, and kerning is automatic. Nobody who reads Greek or a Cyrillic language has checked
  those letters.

## Feedback

Notes from the review board go here, with the date.
