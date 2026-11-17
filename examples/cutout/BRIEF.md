# Cutout

## Brief

Make me a font like Matisse's paper cut-outs. Big bold shapes that look cut with scissors out of painted paper, a bit wobbly, in flat bright colors (that blue, plus coral, yellow, green, black), each letter its own color, maybe with a few leaf or seaweed shapes. Joyful. It's for a children's museum sign and a festival poster.

- **What is it for?** A few large words: the sign of a children's museum and the title, date and time on a
  festival poster. Not running text.
- **What should it feel like?** Joyful, hand-made, bold.
- **What must it not look like?** A torn or rough edge (scissors cut clean), a tidy geometric sans with a
  filter on it, a script, or a tracing of any artwork. The work starts from the description of cut paper: flat
  unshaded color, long straight snips, curves turned in a few facets, shapes that lean.
- **Which styles?** The person did not say, so I chose: one weight, the heaviest that keeps its counters open,
  in two families. `Cutout` has one color, so the person can color it. `Cutout Color` gives each letter its
  own sheet of paper and has three palettes.

## What is delivered

| Family | Files | Characters |
|---|---|---|
| Cutout | `fonts/Cutout/ttf`, `woff2`, `Cutout.css` | The full Latin set of the engine (367 glyphs), with accents. |
| Cutout Color | `fonts/CutoutColor/ttf`, `woff2`, `CutoutColor.css` | Letters, figures and common signs (100 glyphs), no accents. |

Leaves and seaweed are on five keys that a sign does not need:

| Type | Get |
|---|---|
| `*` | a tall frond |
| `{` and `}` | a pair of fronds that lean away from the word between them: `{Children's Museum}` |
| `^` | one leaf |
| `~` | a strand of seaweed on its side |

Palettes of Cutout Color (in CSS, `font-palette` with `base-palette: 0`, `1` or `2`):

| Palette | For | sheet0 | sheet1 | sheet2 | sheet3 | sheet4 |
|---|---|---|---|---|---|---|
| Paper | a light wall | blue `#1F56B0` | coral `#F0604A` | green `#1F9A5B` | yellow `#F4B312` | black `#1B1A1F` |
| Night | a dark wall | `#5B9BFF` | `#FF7C66` | `#4FCB82` | `#FFD23F` | cream `#FBF2DF` |
| Lagoon | the sea | blue `#1F56B0` | teal `#12A39A` | coral `#F0604A` | sky `#2F8FE0` | navy `#0E2A5C` |

## Decisions

Write down each design decision and why you made it, newest last.

1. **Three directions, one picked.** `proofs/directions-round1.png` shows them: A, a chunky grotesk; B, circles
   and triangles (geometric); C, stems that swell toward their ends (flare). I picked C. Its swelling stems
   look like leaves and like the turn of the hand at the end of a cut, and it was the only base that stayed
   clean at this weight: the grotesk grew spikes on `r`, `g`, `a` and `s`, and the geometric `1` collapsed to a
   sliver at weight 190. A and B are no longer in `font.py`.
2. **Not the built-in `rough` effect.** `effects.rough` gives a fine tremble, like torn paper or a worn print.
   Scissors make long straight snips. `cutpaper.py` holds a custom effect (`effects.wrapped`): it closes small
   notches, bends each letter with one slow wave, leans it up to 2.8 degrees and lifts it up to 11 units, and
   then replaces every curve with straight cuts that stay within about 6 units of it. Each glyph gets its own
   random numbers, the same in every build.
3. **Weight 180, single-story `a`, round dots, x-height 515.** Heavy for a sign that is read from far away.
   Friendly forms for children who are learning to read. Round dots, because the diamond dots of the flare
   preset touched the stems of `!` and `?` at this weight.
4. **Pinholes are left out.** At this weight the gap in `6` and `9` nearly closes, and the notch-closing step
   turned it into a tiny hole. The effect drops holes smaller than 2200 square units.
5. **A proportional `1`.** The engine's figures all have one width, which leaves a hole around `1` in "2021"
   or "10:15" on a poster. The project draws its own `1` (a stem and a flag) with its own width. The other
   figures keep one width.
6. **Each letter has its own sheet, chosen so that neighbors differ.** A font gives one letter one drawing,
   so a letter always has the same color. I sorted the letters into five sheets with a search over the letter
   pairs of English (a word list plus running-text frequencies): about 2% of neighboring pairs share a sheet,
   against 20% for a random choice. Capitals follow their small letters. Doubled letters (`ll`, `ee`, `MM`)
   always match.
7. **Line height.** `ascent=1000` and `descent=-260` on both families, because `whateverfont probe` reported that
   accented capitals reached above the default line. Both families share the numbers so one can be set over
   the other.
8. **The color family has the full character set** (`latin()` plus the five leaf keys), so accents, currency signs
   and arrows do not fall back to another font. It is about 76 KB as WOFF2.

## Known weak points

- `Ï` and `ï`: the two dots are wider than the letter. The project makes these two letters as wide as their
  dots, so the dots do not touch the neighbors, but the letters now sit in a gap. On `Ï` a dot touches the stem.
- The acute and grave accents are as thick as they are long, so they look like diamonds.
- `S`, `s`, `K`, `k` and `g` keep small nicks where strokes meet. They read as scissor nicks at poster size.
- `A`, `6` and `9` have very small counters.
- Yellow letters (`e`, `o`, `j`, `q`, `0`, `9`) are the faintest on a white wall. Use the Night palette on a
  dark wall, or the one-color family.
- No hinting, automatic kerning, Latin only, one weight. This is a strong draft made in minutes, not a face
  tuned by a type designer.

## Feedback

Notes from the review board go here, with the date.
