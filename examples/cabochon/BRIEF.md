# Cabochon

## Brief

Make me a font that looks cut from polished gemstones. Start with jade on a dark red cloth: mottled green stone, a glossy bevel, and one small spot of light on each letter.

The person showed a picture. I worked from a description of it, not from the image: one lowercase serif `a`, cut from polished jade, on a dark red ground (about `#7A1418`). The stone is a mottled mid green with paler, cloudy patches, like light inside the stone. The letter has a raised, glossy bevel: a thin bright line runs along the upper left edges of each stroke, the lower right edges are darker, and one small bright spot sits on a stroke like the reflection of a lamp. The letter is a high-contrast book serif.

- **What is it for?** A word or a short line at a large size: a jeweler's sign, a book cover, a menu heading, a label. Not for running text. (I chose this.)
- **What should it feel like?** Precious, polished, elegant. (I chose this, from the picture.)
- **What must it not look like?** Chunky toy letters, candy, a plastic button, or ornament that hides the letter. (The request said the letters must stay elegant.)
- **Which styles?** One style in each family, with six palettes, one for each stone: Jade, Ruby, Sapphire, Amethyst, Amber, Onyx. A color font has no variable file. (I chose this.)

## Decisions

1. **A color font with an effect of its own.** No stock effect gives a lit bevel, so `gem.py` holds two effects written with `effects.wrapped`: `polished` and `faceted`. I worked from the description of the picture. I did not open, trace or sample an image.
2. **Two families, one for each cut of a stone.**
   - `Cabochon`: a bracketed book serif with a raised, glossy bevel, like the jade `a` in the picture. This is `FAMILY`.
   - `Cabochon Rose`: incised letters (the `glyphic` preset) whose strokes are cut into facets that meet in a ridge down the middle, like a carved or faceted stone.
   I did not make a third direction, a round cabochon on the `rounded` preset. I expect round, heavy letters with a dome to read as candy, and the request said not to make toy letters. I did not build it to check.
3. **The base of Cabochon.** The `flare` preset with thin slab serifs (`serif=30`, `serif_weight=0.95`), `classical=1`, `xh=480` and `stress=8`. The flare widens each stem into its serif, so the serifs look bracketed, as in a book face. `weight=120` gives a stem wide enough for a bevel on each side. `contrast=0.45` is as high as the bevel allows: a hairline must stay more than twice as thick as the bevel is deep.
4. **Flat layers only.** The engine's color fonts are COLR version 0, which has no gradients. Each tone is its own flat layer, bottom layer first: the stone, a cast shadow, dark patches, pale clouds, paler cores, the lit bevel, the shaded bevel, the bright line, the lamp spot.
5. **The letter is the bottom layer.** The engine spaces and kerns a color glyph by its first layer. The shadow comes second and does not overlap the letter, so it does not push letters apart.
6. **The bevel is the letter minus a shifted copy of itself.** One lamp sits at the upper left. The lit rim is the part of the letter that a copy moved down and to the right does not cover. The dark rim is the same thing the other way. Each rim is widest on an edge that faces the light squarely and thins to nothing where the light grazes the edge, as a real bevel does. Each side has two steps (a wide one and a narrow, stronger one), so the edge rounds over like a polished dome.
7. **The bevel is 25% of the stem, and never more than 46% of the hairline.** So a thin stroke keeps a lit half and a dark half and does not turn into a single pale or dark line.
8. **The bright line sits just inside the lit rim** (from 12% to 34% of the bevel). At the edge itself it read as an outline. A little inside, it reads as light that runs along the crest of the bevel.
9. **Cloudy patches are soft blobs, not circles.** Each patch is a closed curve whose radius wanders. All patches lean along one grain, 24 degrees, so the stone has a direction. A first version used clusters of ellipses and looked like camouflage and fish scales. The clouds cover about a third of the letter, so the mid green body still shows, as in the picture.
10. **One lamp spot on each letter.** It sits at the point nearest to the upper left of the letter where the stroke has room for it, so on a line of text all the spots agree on one lamp. It is a small pale oval with a white core.
11. **A cast shadow in translucent black (`#00000052`).** It falls 13 units down and to the right. It darkens any ground, so the stones look set down on the cloth, and it gives a pale stone an edge on white paper.
12. **The facets of Cabochon Rose are translucent white and black over the same cloudy stone.** A face turned up gets white at 46%, a face turned left gets white at 22%, a face turned right gets black at 25%, a face turned down gets black at 46% (Onyx has its own values, because white shows more on black stone). Where two faces overlap on a diagonal, their light adds up. The stone shows through every facet. Four-pointed glints sit on about 40% of the letters. On every letter they looked like clip art.
13. **Six stones, each on its own cloth.** The ground is part of the look, so each palette has one. `gem.GROUNDS` lists them:

   | Palette | Ground | Ink for plain text beside it |
   |---|---|---|
   | Jade | dark red cloth `#7A1418` | `#F3E9D8` |
   | Ruby | ivory satin `#F2EADB` | `#3D0410` |
   | Sapphire | old gold cloth `#B08636` | `#1B1407` |
   | Amethyst | pale sage silk `#D2D8C6` | `#2D1342` |
   | Amber | midnight velvet `#15233A` | `#F8E7C4` |
   | Onyx | camel suede `#C6A77B` | `#1E1A15` |

   The engine fills `grounds` in `fonts/index.json` only for a palette that white would hide. These palettes all show on white, so that field is empty. The site must take the grounds from this table.
14. **Full character set.** `latin()`: 605 characters, 652 glyphs and every OpenType feature of the engine, so no character falls back to another font. Cabochon is 795 KB as WOFF2, and Cabochon Rose is 547 KB. The project builds in about 45 seconds.
15. **The name.** I searched for "Cabochon" with "font" and "typeface". I found no typeface with that name, only craft products. "Hardstone" was close to an existing family, Hard Stones, and "Nephrite" is a typeface from Nine Font, so I did not use them.

## Weak points

- The serifs are slabs with a flare, not true brackets, and the contrast (0.45) is lower than in the picture. More contrast would leave no room for a bevel on the hairlines.
- Where a serif meets a stem, the bevel makes small steps, because the rims follow the outline exactly. They show above about 200 px.
- In Cabochon Rose the round letters (`O C G Q o e`) are less crisp than the straight ones. The facets of a curve are curved bands, and where they overlap the stone looks muddy. `&` in the `glyphic` preset has an odd shape.
- Thin signs (`+ = < > ~ ^`, the marks of `ố Ǘ`) are almost all bevel. They read as pale strokes, not as stone.
- The stone of a letter is the same each time the letter appears: the two `a` in "agate" are twins.
- Below about 20 px the bevel and the clouds blur into one green. This is a display face.

## Feedback

Notes from the review board go here, with the date.
