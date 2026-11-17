# Neon

## Brief

I want a neon-sign font for a bar menu — letters that look like one bent glass tube, rounded ends, and if possible a colored glow in pink or blue. A weight slider would be nice.

- **What it is for:** headings and item names on a bar menu, printed or on a screen, usually on a dark wall. (I chose this. The person did not say.)
- **How it should feel:** glowing, playful, a little retro.
- **What it must not look like:** a stencil, a script, or an ordinary bold sans. The strokes must not change thickness, because a glass tube cannot.
- **Styles:** a weight slider (wght 200 to 700), named Light, Regular and Bold, and a slanted Italic. A color version with a glow in pink or blue.

## Decisions

- Every direction uses a monoline "tube": `contrast=1`, `round_weight=1`, `join=1`, `cap_weight=1`, `flare=0`, `roundness=1`, round dots. A glass tube has one thickness and round ends.
- Three shape directions: **Neon** (geometric preset, round bowls, single-story a), **Neon Diner** (condensed preset, tall and narrow, `superness=0.5`), **Neon Rod** (technical preset, wide and low, `superness=0.92`, squared bends). Rod first used `width=1.15, superness=0.8`, and its row looked like Neon at a glance. I pushed it to `width=1.28, xh=450`.
- Base tube `weight=62`, lighter than a text regular (82), because a neon tube is thin relative to the letter. The wght axis runs from 0.55x (200) to 1.9x (700) of that.
- Spacing 1.18 to 1.22. Neon letters are separate tubes that do not touch, and the glow needs room.
- **Neon Glow** is a COLR v0 color font built on the Neon shape. Each letter has five layers: two translucent glow rings (80 and 52 units out), a third ring (30 units), a saturated halo (13 units) and the tube. Several translucent rings stack into a soft gradient, because COLR v0 has no blur or gradients.
- Four palettes: **Pink** and **Blue** have a white-hot tube for dark walls. **Pink Day** and **Blue Day** color the tube itself, because a pale tube on a light wall reads as an outline letter.
- Neon Glow has no weight axis: the color format cannot vary along an axis. The weight slider lives on the plain families.
- The glow is `effects.glow` (see docs/effects.md). The first version of this project wrote its own wrapper; the effect came out of it.
- Rod's `desc` is -222. At -215 the `¿` reached 1 unit below the line and the probe reported it.

## Weak points

- `S` and `5` have a slight hook where the curved end meets its round cap. The `5` has a small spur where its stem meets the bowl. Neither shows at menu sizes.
- The glow reaches about 80 units below the descender, past the line descent (-260). Programs that clip to the line may cut the glow under g, p and y.
- `whateverfont look` proofs clip the glow at the top and bottom of each letter. Browsers do not. Judge the glow on the review board.
- The glow version is for display sizes, about 40 px and up. Below that the rings fill the counters.

## Feedback

Notes from the review board go here, with the date.
