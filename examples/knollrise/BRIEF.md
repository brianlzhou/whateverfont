# Knollrise

## Brief

Make me a font like the contour lines on a hiking map.

- **What is it for?** A word or two at poster size: a trail sign, a park poster, a race bib, a map cover, the title of a hiking guide. It works from about 100 px up. It is not for running text. (I chose this.)
- **How should it feel?** Like a printed trail map: calm, exact, outdoors. From far away it reads as a heavy round word on a soft tint. Up close each letter is a small hill, with its rings and a summit mark. (I chose this, from the request.)
- **What must it not look like?** A neon sign, a striped retro face with even stripes, a fingerprint, or a pattern that hides the letter. (I chose this.)
- **Which styles?** One style in each of two families. Knollrise is the color family, with four palettes: Trail, Sea Chart, Night and Desert. Knollrise Lines is the same rings in one color. A color font has no variable file. (I chose this.)

## Decisions

1. **A color font with an effect of its own.** No stock effect draws contour lines, so `topo.py` holds one, `contour_map`, written with `effects.wrapped`. I worked from the description in the request. I did not open, trace or measure a map or another font.
2. **Two families.** `Knollrise` is the color family and `FAMILY`. `Knollrise Lines` draws the same lines and summit marks in one color, with the paper between them, for one-color printing and for text that takes the color of the page.
3. **The base letter.** The `rounded` preset, so that every free end is round and a ring turns round it smoothly. `weight=176`, `width=1.14`, `counter=340`, `xh=530`, `aperture=0.6`, `join=0.9`, `spacing=1.06`, and the one-story `a` (`a_story=1`), which is a plain bowl and a stem like `d` and `q`. The two-story `a` had a spur at its foot, and every ring repeated it.
4. **Weight 176 is the heaviest that stays clean.** I built 176, 184, 190 and 204 with wider counters for the heavier ones. At 184 the `s` gets a notch where its spine meets the lower curve. At 190 the eye of the `e` is small. At 204 a sixth line runs down every stem but not along the bars. At 176 the counters of `a e s g & 5 6 9 @` stay open. `probe` still warns about stems above 165; I looked at those letters at 240 and 400 px.
5. **Nearly one thickness everywhere.** `cap_weight=1.0` and `round_weight=1.0` give capitals, lowercase and round letters the same 176-unit stem. At this weight the engine draws horizontals at 0.78 of the stem; `contrast=1.15` brings them to 0.91 (160 units). So every stem in a line has the same lines, and the bars have the same lines too, with a narrower ridge.
6. **The lines, from the edge in.** Each line is given by where its outer side lies and how wide it is, in font units:

   | Line | From the edge | Width | Kind |
   |---|---|---|---|
   | 1 | 0 | 9 | index (the edge of the letter) |
   | 2 | 15 | 5 | thin |
   | 3 | 27 | 5 | thin |
   | 4 | 41 | 5 | thin |
   | 5 | 57 | 5 | thin |
   | 6 | 84 | 9 | index |
   | 7 to 10 | 104, 124, 144, 164 | 5 | thin |
   | 11 | 184 | 9 | index |

   The gaps grow from 6 to 7, 9 and 11 units, like the contours of a ridge with steep sides and a round top. A stem (176) holds lines 1 to 5 on each side and a ridge of 52 units of plain tint in the middle; a bar (160) holds the same five lines and a ridge of 36. Lines 6 and up appear only where strokes meet and the letter is deeper than a stem, as small closed rings around a knoll. Every fifth line is an index contour, so the first index is the edge, which keeps the silhouette sharp from far away.
7. **A line is a stroke of even width.** Each line is the outline shrunk to the middle of the line, stroked 5 (or 9) units wide. A stroke keeps one width everywhere, and it needs one shrink for each line instead of two. Only the edge line is the letter minus the letter shrunk by 9, so that it follows the edge exactly.
8. **Smooth rings, no specks.** Where a ring pinches off, the shrunk outline has sharp points. Each shrunk outline is shrunk 12 units more and grown back by 12, which rounds every point to a radius of 12 and drops every part narrower than 24. A piece smaller than 2500 square units gets no ring, so no ring is smaller than about 60 units across. With 260 and then 700, the small top rings at junctions and in the dots of `: ü` read as dark specks at 120 px.
9. **Small dents and points of the letter are smoothed first.** The round end of a stem rises a little past a bar or a bowl that joins it (B D E F P R g 4 Д Л), which leaves a nub and a shallow dent, and the cut end of a diagonal leaves a sharp point on `N`. Every ring repeated them. The letter is grown and shrunk by 200 units, and only the thin fills are kept (no disc of radius 10 fits in them, and they must not close a counter or an aperture). Then it is shrunk and grown by 14, and only cuts in which no disc of radius 4.5 fits are kept.
10. **One summit mark on each letter.** A triangle whose corners are 18 units from its center, at the deepest point inside the letter, found by halving the shrink distance down to 2 units. Where strokes meet, that point is the junction, as on a real ridge. The mark is drawn only where the letter is at least 86 units deep (the last stem line ends at 62, plus the mark and 6 units of white), so it never touches the lines of a stem. A small top ring that it would touch is dropped, and the triangle takes its place. Thin signs (dashes, slashes, brackets, superscripts and fractions) have no summit: 94 glyphs.
11. **The two strokes of a double acute are cut apart.** At this weight the engine draws the two strokes of `ő ű Ő Ű` so close that they touch, and the rings ran round both as one blob. A cut 30 units wide, parallel to the strokes, keeps them two. The cut corners are rounded by 10 units.
12. **Layers, from the bottom:** `land` (the letter, a flat tint), `line` (the thin contour lines), `index` (the index contours), `summit` (the triangle). The engine spaces and kerns a color glyph by its first layer, so the land, which is the whole letter, sets the spacing.
13. **Four palettes, each with its own paper.** The ground is part of the map, so each palette has one. `topo.GROUNDS` lists them:

   | Palette | Ground | Land | Thin lines | Index lines | Summit |
   |---|---|---|---|---|---|
   | Trail (the showpiece) | cream paper `#F4EEDC` | pale green `#C6DA9E` | brown `#9A6436` | dark brown `#6B3E1C` | red `#C2392A` |
   | Sea Chart | pale blue `#E6F0F2` | blue tint `#B5D5E6` | blue `#3C78A8` | deep blue `#1F4F7C` | navy `#1B3F63` |
   | Night | dark slate `#1A222B` | slate `#34475A` | pale sage `#AFC0B0` | pale sand `#E6DEC2` | amber `#F0B860` |
   | Desert | sand paper `#F7EBDA` | tan `#E8BE8E` | rust `#A4532E` | dark rust `#7A351A` | dark brown `#4A3324` |

   The engine fills `grounds` in `fonts/index.json` only for a palette that white would hide. A page that shows these fonts should take the grounds from this table.
14. **Engine problems worked around in `topo.py`.** `effects.erode` does not always return nothing when the distance is wider than the stroke: a dot shrunk by 300 units left a piece the size of a stem. So every shrunk piece is checked: each sampled point must lie inside the letter and at least the distance from its edge. Skia also leaves empty holes and spurs on some shrunk outlines (the Cyrillic `Л` lost all its lines), and now and then cannot merge the band it shrinks with (the build named `ѓ`). The shrink is merged again, and tried a fraction of a unit deeper when either happens.
15. **Full character set.** `latin()`: all 800 code points (847 glyphs) and every OpenType feature of the engine, in both families. Combining marks keep their plain outline, as in every color family of the engine. Knollrise is 472 KB as WOFF2 and Knollrise Lines 427 KB. The project builds in about 2 minutes.
16. **The name.** A knoll is a small round hill, and the rings rise to it. I searched for "Knollrise" alone and with "font" and "typeface", and found no typeface, product or company with that name. Drumlin (a font listing exists), Fellmark (a font for sale), Isofell (a bitmap font) and Ringrise (a boxing brand and an answering service) were taken, so I did not use them.

## Weak points

- Below about 120 px the thin lines (5 units, 0.6 px at 120 px) and the gaps near the edge merge into a darker rim. The word still reads, but the rings show from about 150 px. The summit mark is a red speck below 120 px.
- The small rings where strokes meet come from the shape of each junction, and some letters look busy: `4` has three, `e` two, `k` and `&` have one shaped like a bone, and the flag of `1` has one.
- The rings repeat every small kink of the base letter. In `n` and `m` the round top of the stem rises past the start of the arch, which leaves a shallow dip about 30 units deep; it is too wide for the smoothing. The middle crotch of `m` has a small notch. The top of `g` and the joins of `Д Љ` keep a slight shoulder.
- 94 thin glyphs have no summit mark: dashes, slashes, brackets, `@ % °`, superscripts, fractions and `Ξ`. Their strokes are not deep enough for the mark to clear the lines.
- The two strokes of the double acute are cut apart by the effect, so their inner sides are straight cuts.
- On Night the land tint is close to the ground. The letter reads by its pale edge line more than by its tint.
- Combining marks keep their plain outline and take the color of the text, as in every color family of the engine.
- `probe` warns about stems above 165 units. I checked the letters it names on proofs, but the warning stays.
- Nobody who reads Greek or a Cyrillic language has reviewed those letters.

## Feedback

Notes from the review board go here, with the date.
