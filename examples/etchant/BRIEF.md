# Etchant

## Brief

Make me a font like the traces on a circuit board.

I read this as a color font in which each letter is drawn as copper traces on a printed circuit board. The strokes are thin traces of one even width. They run straight and turn in 45 degree bends. Each free end stops in a round solder pad with a drilled hole, and a via (a small ring with a hole) sits at some of the joints. The copper lies on a dark board under a lighter halo of solder mask.

- **What is it for?** A word or a short line at a large size: a poster, a label, a sticker, a hardware project, a maker event, a slide. It still reads at 28 px. (I chose this.)
- **What should it feel like?** Engineered, tidy, a little playful. It should look like a real board when you zoom in. (I chose this.)
- **What must it not look like?** Round neon tubes, a pixel font, or a schematic drawing with symbols. The letters must not turn into a maze in which the word is lost. (I chose this.)
- **Which styles?** One style in each family. `Etchant` is the color font, with four palettes: Green, Black, Blue and Paper. `Etchant Plain` is the same traces in one color. A color font has no variable file. (I chose this.)

## Decisions

1. **The traces come from the strokes.** The engine draws every letter from centerline strokes, and a trace is a centerline, so the effect starts from the centerlines. `traces.py` holds two effects written with `effects.wrapped`: `traces` for the color family and `plain` for the one-color family. Both read `g.strokes` and `g.shapes`, build the copper, and redraw the glyph.
2. **The skeleton is monoline.** The base is the `technical` preset with `weight` 44, `contrast` 1, `cap_weight` 1, `round_weight` 1, `join` 1 and `flare` 0. So the stem is as wide as a trace and every centerline sits where a 44-unit trace needs it. `superness` is 0.4: rounds are a little square, so an `o` becomes a wide octagon.
3. **One trace width: 44 units.** Every stroke of every glyph is stroked with a round pen 44 units wide, also the accents and the small figures. A round pen gives each bend a round outer corner, as a plotted trace has.
4. **How bends are snapped.** A curve is sampled every 2.5 units. A sample whose direction lies within 15 degrees of a diagonal runs at 45 degrees; any other runs level or upright. Each stretch of samples with one direction becomes one straight run, and neighboring runs meet where their lines cross. So the flat sides of the octagon touch the old curve, and the letter keeps its height. I first used an even split (22.5 degrees). The spine of `s` then ran as one long diagonal and the letter read as a mirrored `z`. With the narrower window the spine lies flat.
5. **Straight strokes at other angles become two or three runs.** A stroke at 60 degrees becomes an upright run and a 45 degree run. A free end gets the upright or level run, so a pad sits on a straight run like a pin. A joint or a corner gets the diagonal. So `V` and `A` have upright legs and a point of two 45 degree runs, and the arm of `K` leaves the stem at 45 degrees. A stroke free at both ends (a slash) is bent where it keeps farther from the other strokes. A jog shorter than a quarter of a trace is dropped, and the free end moves those few units instead. A check over all glyphs finds no run more than 1 degree off 0, 45 or 90.
6. **Square corners get a chamfer.** Every 90 degree turn between a level and an upright run gets a 45 degree cut with legs of 64 units (less where a run is short). A smaller chamfer from a curve is widened to the same size. A 90 degree turn between two diagonals keeps its point, because the point of `V`, `A` and `W` tells the letters apart.
7. **Joints.** An end buried in another stroke slides along its run until it meets that trace, so there is no stub past the joint. Two ends that meet at an L (`E`, `L`) become one trace with a chamfered corner. Two parallel runs a few units apart (the stems of `a` and `e` in `æ`) are moved onto one line, so they do not print as one fat trace.
8. **Pads: radius 46 (92 across), with a hole of radius 16 (32 across).** A pad sits on every free end. It moves back along the trace until it passes the line the stroke ended on by no more than 8 units. So pads on the baseline and on the x-height stand like overshoots.
9. **Where an end stays plain.** A pad that would crowd a letter is left out, and the trace ends with its round end:
   - the stem below the dot of `i`, `j`, `ï`, `!` and `?` (the dot is that stroke's pad);
   - the short bars of `t` and `f`, and the strokes of `ł` and `đ` (a bar shorter than 300 units that crosses a stem);
   - pads that would touch another pad (the arms of `*`, the two acutes of `ő`);
   - the lower end of a straight quote, which keeps one pad on top like a curly quote;
   - accents that bend (circumflex, caron, breve, tilde, cedilla, ogonek). With pads they were wider than an `i` and ran into the next letter. A straight acute or grave keeps one pad, at its upper end.
10. **Dots are pads.** The dots of `i j ! ? : ;`, the period and the dieresis are pads of the same size. A pad on the baseline rises to stand on it. Two pads closer than 106 units move apart. A pad that would lie on a trace it does not belong to (the caron of `ď ľ Ľ`) moves away from it, with its tail.
11. **Vias: a ring of radius 36 (72 across), with a hole of radius 14 (28 across).** A glyph gets at most one via. It sits at a T joint, where a trace ends on the middle of another, at least 100 units from any pad, and the joint nearest the middle of the glyph wins. So `A E F H K N R T Y k 3 6 9` get one and a word gets a few.
12. **Filled shapes are copper pours.** The curves of `¶`, `●` and `♥` are redrawn as runs at 0, 45 and 90 degrees. `■ ◆ ▲ ▼ ★` keep their straight edges.
13. **The layers, bottom first:**
    1. `mask`: the solder mask, a halo 18 units wider than the copper on each side, a little lighter than the board.
    2. `gap`: a ring 7 units wide around each pad, where the mask stops short and the bare board shows.
    3. `trace`: the copper.
    4. `shine`: a line 12 units wide down the middle of each trace, a little lighter, where the copper catches the light.
    5. `via`: the via rings.
    6. `pad`: the pads and pours.
    7. `hole`: the drilled holes.

    The engine spaces and kerns a color glyph by its first layer, so the mask sets the spacing. It reaches 18 units past a trace and 42 units past the edge of a stem where a pad sits.
14. **Recipes I redrew in `font.py`.** The effect needs a skeleton that works as a trace. I redrew twelve glyphs:
    - `( )` as a 45 degree run, an upright run and a 45 degree run back. The stock curve was nearly straight and turned into a bracket.
    - `[ ]` and `{ }` with arms of 170 units, so a pad and a chamfer fit on each.
    - `"` with its ticks 114 units apart, so each gets a pad.
    - `I` with bars top and bottom. A plain `I` was the same as `l`.
    - `!` with a plain stem. With a pad on top it read as an `i` turned over.
    - `y` as a `u` whose right stem runs into the descender and turns left, like `g` and `j`. The stock diagonals bent into a fork that read as a small `Y`.
    - `N` as a stem that turns down into one 45 degree run, which ends on a full right stem. The stock diagonal needed a step in the middle.
    - `M` with upright legs and a V of two 45 degree runs that meets at 57% of the cap height.

    Greek and Cyrillic letters drawn from these follow them (`Ι І Ν И Й у`).
15. **Spacing.** `spacing` and `word_space` are 1.2, because the pads reach past the stems. A side that a recipe calls diagonal (`V A X K k v x`) or thin gets 0.62 of a straight side instead of 0.16 or 0.3. As traces those sides end in upright runs with pads, and with the stock values the pads of `R` and `x` touched in `Rx`. Kerning may pull letters together by up to 110 units but push them apart by only 25, so the sides start wide and kerning closes what the shapes allow.
16. **Line height.** `ascent` is 960 in both families, so the stacked marks of Vietnamese capitals (`Ẫ`) and their mask are not clipped.
17. **Four palettes, each for its own ground.** The engine fills `grounds` in `fonts/index.json` only for a palette that white would hide, so the site must take the grounds from this table (it is `traces.GROUNDS` too):

    | Palette | Ground | Mask | Trace | Pad | Hole |
    |---|---|---|---|---|---|
    | Green | `#0F3D24` | `#247442` | `#D19A3A` | `#F3D47C` | `#0B2416` |
    | Black | `#141517` | `#2E3236` | `#A9AFB6` | `#E8EBEE` | `#08090A` |
    | Blue | `#0C2D63` | `#2259A6` | `#DCA845` | `#F7DC8F` | `#07183A` |
    | Paper | `#FFFFFF` | `#DCEADF` | `#B5651D` | `#8E4A12` | `#FFFFFF` |

    Green is the showpiece: gold on a green board. Black has silver traces. On Paper the holes are white, so they look drilled through the page.
18. **The second family, `Etchant Plain`.** The same copper in one color, with every pad and via hole cut through. It reads as a light monoline sans with dots at the ends, and it needs no ground.
19. **Full character set.** `latin()`: 800 code points and 847 glyphs in each family, with every OpenType feature of the engine. `Etchant` is 177 KB as WOFF2 and `Etchant Plain` 61 KB. The project builds in about 13 seconds.
20. **The name.** An etchant is the acid that eats away the copper around the traces. I searched for "Etchant font", "Etchant typeface" and "Etchant font download" and found no typeface with that name, only dictionary entries and two fonts with other names. Two other names I considered belong to a product or are a term of board design software, so I did not use them.

## Weak points

- `W` and `w` keep upright outer strokes and read a little like two `v`s side by side.
- The small figures of fractions (`½ ⅓ ⅛`), superscripts and `ª º` get full-size pads and traces, so they are crowded. In a fraction the slash runs close to the figures.
- `ð` is crowded at the top. The circumflex of `ĵ` sits left of the stem, over the hook.
- `4` closes its diagonal at the top of the stem, so its upper part reads as a narrow triangle.
- `t` and `f` have plain ends on their bars, and accents that bend have no pads. That breaks the rule of a pad at every end, on purpose, so the letters stay clear.
- `★ ▲ ▼` keep their angles: as copper pours they are not on the 45 degree grid.
- Below about 20 px the pads become dots and the shine and the mask disappear. This is a display face.
- Nobody who reads Greek or a Cyrillic language has reviewed those letters.

## Feedback

Notes from the review board go here, with the date.
