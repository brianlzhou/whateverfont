# Leafpile

## Brief

Make me a font for fall. Pile every letter up from maple, oak, birch and ginkgo leaves in the colors of October.

- **What is it for?** A heading at a large size: a harvest fair poster, the title of a fall menu, the letters on a school bulletin board. Not for running text. (I chose this.)
- **What should it feel like?** Warm, crisp, a little playful. Like a heap of leaves that a child jumps into. (I chose this.)
- **What must it not look like?** A camouflage pattern, a gradient, a font that you must squint at to read, or leaves that look like blobs. (I chose this.)
- **Which styles?** One style in each family. `Leafpile` is a color font with four palettes: Maple, Ginkgo, Oak, Late October. `Leafpile Plain` is the same letters in one color. A color font has no variable file. (I chose this.)

## Decisions

Write down each design decision and why you made it, newest last.

1. **One idea: every letter is a heap of fallen leaves.** I weighed four ideas: letters covered with leaves, letters built from a row of leaves, plain letters with a few leaves that landed on them, and a pressed-leaf print. A cover of leaves says "fall" at once and keeps the shape of the letter. The leaves that landed on top come back in decision 6.
2. **Four kinds of leaf, drawn in code from a description.** A maple has three big pointed lobes and two small ones at the foot. An oak has four round lobes on each side and one at the top. A birch is an oval with a long point and a toothed edge. A ginkgo is a fan on a long stalk, with a notch in its top edge. Each has ribs. I did not open, trace or sample any image. Maples are the most common (40 percent), because they say "fall" most clearly. My first birch was upside down and my first ginkgo was a heart; I fixed both before I drew a letter.
3. **Heavy, round letters.** The `rounded` preset at weight 155, with `counter=310` and `width=1.06`, so that the counters stay open under the leaves. A leaf is about 1.45 stems long, so a stem holds one or two leaves across. Smaller leaves turn into noise. Bigger leaves hide the strokes.
4. **The leaves follow the strokes.** Each leaf points along the stroke under it, either way, turned by up to 40 degrees. A long oak or birch leaf then lies inside the stroke and does not cover a counter.
5. **The leaves are cut to the letter.** The bottom layer, `under`, is the letter grown by 12 percent of a stem, in a dark color. The leaves lie on it, cut to the same outline, so the letter keeps a clean outline and reads first. A gap of 7 units between two leaves shows the dark layer, as wet leaves show under dry ones. This gap is what makes each leaf read as a leaf.
6. **A few leaves on top stick out.** Of the top 30 percent of the heap, a leaf that lies at least 55 percent on the letter is not cut at the edge. It may reach out by 38 percent of a stem. These leaves make the outline look like leaves that fell, and not like a pattern seen through a window. The dark layer reaches under each of them too: without that, the gap between two such leaves showed the paper and looked like a crack.
7. **Where a leaf may not stick out** (`_room` in `leaves.py`). Not into a counter. Not into an opening or an inside corner (the mouth of the `e`, the crotch of the `V`). Not toward another part of the letter. Not on a dot, an accent or a thin sign (`~ - =`): on those a leaf hid the shape, and the two dots of `Ä` came out different sizes. If two leaves still meet across an opening and close it, that glyph is stacked again with no leaf sticking out. A check over all 652 glyphs found no glyph with more or fewer parts or counters than the plain letter.
8. **The letter grows less where it must.** The dot of the `i` sits less than 40 units above the stem, so a margin of 19 units on each side joined them. The margin shrinks for a glyph until it keeps all its parts and counters.
9. **Colors come from a shuffled bag.** My first version chose each leaf's color at random. Some letters came out darker than their neighbors, and the word looked spotty. Now every letter gets the same mix of five colors (one dark, three middle, one light).
10. **A vein layer with transparency.** The ribs are one layer, a dark color at about 40 percent opacity. Over each leaf color it gives a darker rib of the same hue. That needs one layer and not five.
11. **Four palettes, each for its own ground.**
    - Maple: reds, oranges and gold, on a warm cream (`#F4E9D4`).
    - Ginkgo: five yellows, on a dark green (`#23302C`), like ginkgo leaves on a wet path. On white its small sizes are pale, so I do not show it on white.
    - Oak: browns, rust and tan, on a pale sage (`#E4E2C8`). My first Oak browns were too close to each other, and the word looked muddy. I spread them from dark brown to tan.
    - Late October: the Maple colors, brighter, on a near-black ground (`#17120E`). First its dark layer was the color of the ground, so the leaves glowed, but at small sizes the `9` blurred into a `0`. A dark brown layer (`#4A2A1A`) now gives each letter a faint body.
12. **Proportional figures.** A poster sets "2026" and "4 pm" in a line, so the default figures are proportional. The `tnum` feature gives tabular ones.
13. **`ascent=960`.** The dots of heavy capitals (`Ä`, `Ż`) reach 946, above the default top of the line (940).
14. **Full character set.** `latin()`: 605 characters, every letter, sign, arrow and fraction of the engine. The color font is about 1.1 MB as WOFF2 (2.4 MB as TTF). The plain cut is 40 KB. The project builds in about 90 seconds.
15. **Workarounds for three engine problems** (all in `leaves.py`).
    - Skia failed to cut the ribs of a leaf to the thin bar of U+2015 ("operation did not succeed"), and the build left the glyph out. `_ribs_on` cuts each rib on its own when that happens.
    - Skia's intersection sometimes returns a piece outside both shapes: a gray dash of rib to the left of the `Ż`. `_ribs_on` drops a piece that leaves the box of its leaf.
    - The engine warns about every merge that gives up while a glyph is drawn, also inside an effect. The rough zone of `_room` gave 151 such warnings (from slivers along the outline), although nothing of it goes into the font. The effect drops slivers and then those warnings, as the engine's own `trace.py` does.

## Weak points

- The leaves of a letter are the same each time the letter appears: the two `l` in "Fall" are twins.
- Below about 30 px the leaves turn into a mottled texture. The word still reads, but the leaf shapes do not.
- Thin signs (`- = + ~ |`) hold only a few leaves, cut short.
- A leaf that sticks out can change an end a little: the `4` has a leaf under its bar, and the foot of the `S` has a ginkgo.
- The top of the `t` in the `rounded` preset is a lumpy trefoil at this weight, in both families.

## Feedback

Notes from the review board go here, with the date.
