# Changelog

This file lists what changed in each release, newest first. Version numbers follow
[semantic versioning](https://semver.org); before 1.0 any release may change the API.

## 0.1.1 (2026-11-17)

### Added

- **Text families for everyday use.** Five example families that are plain on purpose: **Dayshift** (a sans for
  the interface of an app), **Setsquare** (a geometric sans), **Softboil** (a rounded sans), **Doorstep** (a
  slab serif for long reading) and **Hedmast** (a condensed sans for headlines). Each has the whole character
  set, five weights or more and a variable font.
- **Six more example families.** **Lowslung** (a wide display sans with a width axis), **Scanstep** (a pixel font
  on one grid, with a color cut), **Etchant** (letters as traces on a circuit board), **Tinsheen** (chrome from
  flat color bands), **Teacloth** (cross-stitch on one grid) and **Knollrise** (letters as hills on a contour
  map). Each has the whole character set.
- **Four numbers for proportions.** `round_width` sets how wide `o c e b d p q s` and the figures are next to
  the `n`, `cap_width` how wide the capitals are next to the lowercase, `arm` how far the arm of `r` and the
  hooks of `f t j` reach, and `word_space` the space between words. Each is 1 by default, so a font that does
  not set them is drawn as before. An interface sans needs a narrow `n` beside a wide `o`, wide capitals and
  loose spacing: `examples/dayshift` shows the numbers.
- **`cut="flat"`**, the stroke endings of a grotesque: `c e s a` end level, the arm of `r` and the hooks of
  `f t j` stop when they are level and end upright, and the tails of `g J 3 5 6 9` are cut square. With
  `cut="horizontal"` those hooks and tails ended in a sharp wedge.
- **The first page of the site** has wide tiles that show a font's own line, a text box that sets your words
  in every font, sliders for the eight numbers of one font under "How it works", and a button that copies the
  commands.

### Changed

- **The tilde is a long, low wave.** The old one was tall, and in a heavy weight it closed into a knot. Every
  font's `ã ñ õ`, the Vietnamese letters with a tilde and the combining mark changed.

### Fixed

- `retrace` on a Latin source with 2048 units to the em (Inter and its relatives) lost the stems of `b d h`,
  lost dots, and left the marks of composite letters without color. The tracer's lengths now follow the em of
  the source.

## 0.1.0 (2026-11-15)

### Added

- **Six more example fonts**, each a color family with a custom effect that an agent wrote from a
  description in words: **Cabochon** (letters cut from polished stone, in six stones), **Ombrelle** (pointillist
  dots with a sunny side and a shadow side), **Panework** (letters divided like the grid paintings of De
  Stijl), **Lacentine** (a valentine on a paper doily), **Drippelgang** (Halloween letters dipped in goo) and
  **Leafpile** (letters heaped from fall leaves). Each has the whole character set and a plain or second cut.
- **Greek and Cyrillic.** `latin()` and `mono()` have modern Greek and Cyrillic, drawn with the family's
  pen like the Latin letters: 195 code points more, 800 in all (960 in `mono()`). Cyrillic covers U+0400 to
  U+045F, `Ґ ґ`, and `Ә Ғ Қ Ң Ө Ұ Ү Һ Җ Ҳ Ҷ Ӣ Ӯ` with their lowercase, for Russian, Ukrainian, Belarusian,
  Bulgarian, Serbian, Macedonian, Kazakh, Uzbek, Tatar, Tajik and Kyrgyz. Greek has the monotonic alphabet,
  the vowels with the tonos and the dialytika, the question mark and the ano teleia. A letter with the shape
  of a Latin one draws that letter (`А Α` are `A`), so a redrawn Latin letter changes its twins too. The
  Cyrillic lowercase are small capitals with lowercase strokes; `б ф Д Л Ж У` and the Greek lowercase have
  recipes of their own. Each letter is kerned within its script and with the punctuation, the combining
  marks attach to it, and the font names the `cyrl` and `grek` scripts. `latin(greek=False,
  cyrillic=False)` leaves them out, and `latin().only(greek=True, cyrillic=True)` keeps them in a small set.
  The Latin glyphs keep their names, outlines, advances and places. A font is about half again as large.
  Proof sheets show a line of each script.
- **A library that you search by mood, with votes and views.** The site's library is one page with every
  font, the examples and the ones that people added. Type a need in plain words ("cozy winter", "a sign for
  my bakery") and the fonts that fit come first, each set in your words, with words to go on from. The search
  runs in the browser on small word vectors (`site/search`, `site/search.js`), so nothing that a reader types
  leaves the page. Every font has a page of its own (`/library/NAME/`) with its styles, sliders, downloads
  and three fonts like it, and the table of all its characters, also for the scripts that it has whole fonts
  of. A reader can vote for a font, and the page of a font counts its views. A small Cloudflare Worker
  (`worker/`) keeps the counts in the SQLite storage of one Durable Object, with no outside database. Until
  it is deployed the buttons and the numbers stay hidden. `node scripts/try_site.js` serves the built site
  with the same code and SQLite in memory.
- **The first page is short.** It keeps the poster, the demo and the wall of words. The samples of all the
  fonts moved to the library. The poster and the wall show every font of the library, and each tile of the
  wall leads to its font's page.
- **Traditional Chinese.** `whateverfont retrace --only traditional` keeps the 5,401 characters of Big5 level
  1, with the same punctuation as `chinese`. `examples/retrace` has four Traditional Chinese fonts: Last Bell
  Traditional Chinese and Last Bell Snow Traditional Chinese, traced from LXGW WenKai TC, and Neon Glow
  Traditional Chinese and Gantry Traditional Chinese, traced from Noto Sans TC Light. The site has a twelfth
  language, 繁體中文 (`zh-Hant`), written as Taiwan writes it, with page fonts for the other families. A
  Traditional page never loads a Simplified font, and the reverse.
- **Last Bell's Simplified Chinese has mainland forms.** Last Bell Chinese, Last Bell Snow Chinese and the
  Simplified page fonts of the handwritten families are traced from LXGW WenKai GB, the release of LXGW
  WenKai with the forms and the stops of mainland China, instead of LXGW WenKai TC, which has Taiwan's.
- **Japanese, Chinese and Korean, by retracing.** `whateverfont retrace --only japanese` (or `chinese`,
  `korean`, or a text file of characters) keeps the common characters of a source: hiragana, katakana and
  the 2,965 kanji of JIS X 0208 level 1, the 3,755 characters of GB 2312 level 1, or the 2,350 Hangul
  syllables of KS X 1001, with their punctuation. The sets come from Python's codecs, with no data file.
  For these scripts nothing joins, corners are rebuilt sharp for a type source and stay round for a
  handwritten one (`--corners`), straight strokes stay straight where others cross them, and a box keeps
  its four corners. A heavy pen is thinned for each dense character by the white between its strokes and
  parts, the whole font no heavier than its median character allows, and a character that still fills in
  is flagged. About 3,400 glyphs trace and draw in a minute on 16 cores. See `whateverfont docs scripts`.
- **`examples/retrace` in Japanese, Chinese and Korean**: Last Bell and Last Bell Snow traced from Klee One,
  LXGW WenKai TC and Gaegu, Neon Glow and Gantry from Noto Sans CJK Light. The sources are not in the
  repository: `examples/retrace/sources.json` lists their URLs and hashes, and `build.py` fetches a missing
  one. Each font folder keeps its source's license and copyright lines.
- **A complete character set.** `latin()` and `mono()` have 605 code points, 143 more, so a font from the
  engine is not the one in which a currency sign, a fraction or an arrow falls back to another font. They are
  what Intern, a popular open font, has and the engine lacked, and a little more: the rest of Latin
  Extended-A (`Ĳ ĸ Ŀ Ŋ Ŧ ſ ƒ`), the Pinyin vowels with a caron and `ü` with each tone, `ə Ə ʻ ʼ ṣ ṅ` for
  Azerbaijani, Hawaiian, Yoruba and Igbo, `ɓ ɗ ƙ Ɓ Ɗ Ƙ` for Hausa, `Ω π`, the Unicode hyphens and dashes,
  the superscript and subscript figures, twelve more fractions, 27 currency signs (`₹ ₽ ₺ ₦ ₩ ₿` and the
  others), the Mac Roman math signs (`∂ ∆ ∏ ∑ √ ∞ ∫ ≈ ≠ ≤ ≥ ◊ №`), ten arrows and twelve marks and shapes
  (`✓ ✗ ★ ☆ ♥ ● ○ ■ □ ▲ ▼ ◆`). Most are drawn from the basic recipes, so they follow the family's pen; a
  currency sign built on a capital is drawn narrower, as wide as a figure. The glyphs that were there keep
  their place and their outlines.
- **Figure and case features.** Every font has `frac` (1/2 becomes a fraction like ½), `numr`, `dnom`, `sups`,
  `subs`, `sinf`, `ordn`, `zero` (a slashed zero), `case` (dashes, brackets and guillemets for capitals) and
  `pnum`, written for the glyphs it has. The default figures stay tabular; `Family(figures="proportional")`
  makes them proportional and adds `tnum`. They work in static and variable fonts, in monospaced families
  (every glyph keeps its cell) and under effects.
- **The effect examples have the whole set.** Gilt, Kanagawa, Cutout Color, Marquee, Turbo, Billboard,
  Pointille and Meridian now use `latin()` instead of `latin().only()`. The heavy ones set `ascent`, so the
  marks of their capitals (`Ż Ố Ǘ`) are not clipped. Starry and Haystack keep the small set: a painted glyph
  is about 10 KB.
- **Other scripts, by retracing.** `whateverfont retrace FONT --name NAME --pen PROJECT[:FAMILY]` traces the
  centerline of every glyph of an open font and draws it again with a family's pen, and with an effect if you
  give one (`--effect glow:size=80`, or a project's own as `snow.py:capped`). The font keeps its shaping
  tables, character map, advances and composite glyphs, so Arabic joins and Devanagari conjuncts work. The
  letter shapes are the source's: the result keeps its license and copyright line, gets a new name (a name
  the source reserves is refused) and drops its trademark record. Strokes next to a small counter or a narrow
  gap get thinner under a heavy pen, marks and dots grow less than letters, and a self-check flags every
  glyph that lost a stroke, closed a counter or merged two parts. It needs numpy:
  `pip install 'whateverfont[trace]'`. See `whateverfont docs scripts`.
- **`examples/retrace`**: Last Bell, Last Bell Snow, Neon Glow and Gantry in Arabic and Devanagari. Last Bell
  is traced from handwriting (Kalam, Playpen Sans Arabic), Gantry and Neon Glow from Noto Sans.
- **Vietnamese.** The full Latin set (`latin()`, `mono()`) has the whole Vietnamese alphabet in both cases:
  the horn of `ơ ư`, the hook above, the dot below and the letters with two marks, the dong sign `₫`, and the
  combining hook above, dot below and horn, with their place in the `mark` feature. That is 98 code points
  more, 462 in all. The marks of a stack are placed by measuring their outlines, so they keep apart at every
  weight and width: with a circumflex the acute, grave and hook sit at its upper right, and on a breve an
  acute, grave or hook sits down in its cup. A stack that would rise above the top of the line gets flatter
  marks, so the line spacing did not change. `latin().only(vietnamese=True)` keeps the alphabet in a small
  set. A reader of Vietnamese has not reviewed the marks yet.
- **Hopstep**, an example where every letter is a person who dances: a color font with four palettes, a solid
  cut and a line cut. One body kit with fixed bone lengths draws all 26 poses.
- **The site speaks twelve languages, and so do the fonts where they can.** A menu in the header changes the
  words of both pages: English, Spanish, French, German, Galician, Breton, Vietnamese, Simplified Chinese,
  Traditional Chinese, Japanese, Korean, Arabic and Hindi. Each language is one file in `site/i18n`, the build checks its keys and tags against the
  English text, and Arabic turns the page right to left. Each font's sample is set in the reader's language
  too, where the font has every letter of the translation: the build checks that against the font's own
  character table, so a sample never falls back to another font. The poster, the words of the wall, the blocks
  of the footer and the snow demo follow the language the same way, and in a language that only some fonts
  can set, the poster shows those fonts only. Briefs, descriptions and code stay in English.
- `python3 scripts/build_site.py --serve PORT` serves the built site on your computer.
- **The library.** `library/` holds fonts that people add by pull request, and the site shows each with the
  GitHub name of the person who added it. `whateverfont library add DIR --github NAME` prepares an entry,
  `library check` runs the checks of a pull request, and `library build` builds the fonts after a merge. A
  pull request holds sources only.
- **A plugin for Claude Code** (`.claude-plugin`), an `npx whateverfont` wrapper (`npm/`), and a release
  workflow that publishes a tag to PyPI.
- **The skill, the reference pages and the example sources ship with the package.** `whateverfont skill install`
  copies the skill to an agent's skills folder and `whateverfont skill show` prints it. `whateverfont docs` and
  `whateverfont examples` list and print the pages and the example projects, so an agent needs no checkout.
- **`whateverfont probe --problems`** prints only the list of problems. `probe` warns when stems pass 165 units,
  and it skips the letter checks for a font that an effect has finished.
- **A proof shows every color.** `whateverfont look` gives a palette that the paper would hide (white snow on
  white) a contrasting ground, and `look --directions` gives such a row its own band.
- A recipe can be called, so a new recipe can start from a stock one: `latin()["r"](g)`.
- **Last Bell**, an example made in four rounds of feedback, with a snow effect of its own.
- **Slab serifs**: the `serif` and `serif_weight` parameters. Free stem ends get slabs, the arms of
  `E F L T Z 2 5 7` get beaks, `a d q g` get spurs, and slabs that meet across a narrow counter are
  shortened. `g.slab`, `g.beak` and `serif0`/`serif1` on `g.stem` let a recipe place its own. Turning serifs
  on is a structure choice: a variable font needs them in every master or in none, and `build` warns if a
  family mixes the two. The slab length may vary along an axis. See [docs/parameters.md](docs/parameters.md#serifs).
- **The `typewriter` preset**: a monospaced slab serif with round ends and low contrast. In a monospaced
  family with serifs, `i j l I 1` take typewriter forms and `m w M W` are drawn lighter and more open.
- **`em` and `double_vee`** in `recipes.upper` and `recipes.lower`: an `M`, `W` and `w` with a raised vertex
  and lighter strokes, for crowded cells.
- **`probe`** reports the slab size, and says when an upright monospaced glyph runs past its cell.
- Three monospaced example projects: **Platen** (a typewriter face and an inked companion), **Pinout** (a
  datasheet mono) and **Greenbar** (dot-matrix print, and Halation, a phosphor-screen color font).
- **Effects** (`whateverfont.effects`): `stencil`, `inline`, `outlined`, `shadow`, `stripes` and `rough` for one
  color; `glow`, `layered_shadow`, `banded`, `mosaic`, `dotted` and `painted` for color fonts; `wrapped`
  and a set of tools (`brush_mark`, `stroke_marks`, `field_marks`, `paint_layers`, `erode`, `extrusion`) for
  writing your own. See [docs/effects.md](docs/effects.md).
- **Monospaced fonts**: the `mono` parameter and preset. Every glyph gets one advance; wide letters are
  drawn with narrower counters and narrow letters wider. The `mono()` recipe set has barred `i l I 1`, a
  dotted zero, signs drawn for code, and the box-drawing and block characters (U+2500 to U+259F).
- **Line height on the family**: `Family(ascent=..., descent=...)` for picture fonts and framed capitals.
- **`Recipes.only(chars)`**: a small character set for display and color fonts.
- **`whateverfont look`**: `--palette` and `--bg` for color fonts, several lines with `--text "a\nb"`, and
  `--name` to keep more than one text proof. Color proofs are drawn layer by layer, so no layer is clipped.
- **`fonts/index.json`**: `whateverfont build` lists what it built (families, styles, axes, palettes, files).
- GF Latin Core coverage: 364 code points, combining marks with `mark`, `mkmk` and `ccmp`, and `locl` forms
  for Romanian, Moldovan and Catalan.
- `whateverfont remix` restyles an existing font (round, embolden, slant, narrow).
- Color fonts (COLR version 0) with palettes, and `ornament.illuminate` for decorated capitals.
- The review board, proofs rendered from the built files, `probe`, presets, and the agent skill.
- Eighteen example projects, and a project site built from them.

### Changed

- **Large WOFF2 files are smaller.** Font data over 4 MB is compressed with a 16 MB Brotli window, the
  largest of standard Brotli, instead of the 4 MB default, so repeated outlines far apart are found. Last
  Bell Snow Traditional Chinese is 7.0 MB instead of 11.7, Neon Glow Traditional Chinese 8.4 instead of
  9.5. A smaller font comes out byte for byte as before. The fonts committed before were not encoded again.
- **A remix keeps the whole font.** `whateverfont remix` used to cut its result down to Latin letters and six
  features. It now keeps every character and every OpenType feature of the source, so Pebble Sans has all
  2,849 characters and 39 features of Inter. `--latin` gives the small file as before.

- **The project is called WhateverFont**: the package and the command are `whateverfont`.
- **American spelling.** The paint effects take `colors=`, and two example fonts are now Aviary Color and
  Cutout Color.
- **Heavy weights hold together to about weight 200.** The figure 1 lost its stem above weight 190, and a
  horizontal cut on a nearly horizontal stroke end (the arm of an `r`) left a spike as long as the stroke
  is thick. A cut now keeps at least 38 degrees to the stroke it cuts.
- **Aviary is redrawn**: 26 birds cut from colored paper, built from circles and straight lines, with one
  shared palette, four palettes in all, and ten figures.
- `whateverfont look --directions` prints the warnings of every family and honors `--name`.
- `whateverfont new` leaves the font's description empty instead of writing the request into it.
- In a monospaced family, a glyph wrapped by an effect is fitted to the cell with its plain drawing, and the
  effect runs once. Before, a slow effect ran up to six times per glyph.
- `effects.redraw` keeps how far slabs reach past the frame, so an effect does not push serifs out of the cell.
- `whateverfont look --text` accepts an empty line.
- **Builds are about three times as fast.** The styles of a family and the masters of its variable font
  are drawn in parallel (set `WHATEVERFONT_JOBS=1` to turn that off), and the stroke expander and the kerning
  do less work. Arroyo (six styles, three axes) went from 8.0 s to 3.0 s on a 16-core laptop.
- **Builds are reproducible.** Font files carry a fixed date (or `SOURCE_DATE_EPOCH`), so the same design
  gives the same bytes.
- **`look` and `board` build only what changed** and print `built: DIR` when they build. `build --force`
  always builds. Editing `BRIEF.md` does not make the fonts stale.
- Accented letters, `æ` and `œ` now use the project's own base letters: a project that redraws `e` gets
  that `e` under every accent. An effect is applied to an accented letter once, as a whole.
- `font.py` may import Python files that sit next to it.
- `æ` always has a two-story `a`, so it cannot be read as `œ`. A heavy, narrow `Æ` keeps its counter.
- The comma has a longer, heavier tail.
- `dilate` grows each contour on its own, so it no longer loses a counter.
- A family that cannot have a variable font (a color family, a stencil) says so in a `note:`, not a warning.
- `build` removes the font folders of families that the project no longer has.
- A failing recipe or effect names the line of your code that failed.
- The brief in a new `font.py` ends at a sentence or a word.

### Fixed

- **A remix takes the new name in every language.** `remix_file` wrote the new name in English only, so a
  font with Japanese, Chinese or Korean name records (Noto Sans CJK has them) kept the source's name there.
  It now drops the old name records in every language. The committed remixes would not change: Inter has
  English names only, and the page fonts of Pebble Sans keep English records only anyway.
- **Only an effect that asks gets its dots uncovered.** After an effect, `retrace` gave a dot back the color
  of the layer it guessed was the letter, the one whose area was closest to the outline. For paint on a
  paper layer it guessed the paper and took the paint off every dot. An effect now names its letter layer
  (`g.letter_layer`, as `snow.py` does), and other effects keep their layers on dots.
  `scripts/build_page_fonts.py` no longer turns the function off; its fonts come out byte for byte the
  same. Built again, the committed retraced fonts would not change: snow's letter layer is the one the
  guess took, and a glow's tube is its top layer.
- **Retraced rings stay on their centerline.** A traced ring with four corners (a box) lost the corner at
  its seam, and the closing curve of a ring could bulge where it met its start. A stroke whose outline
  touches itself is cut in two so that it merges. Built again, the committed Arabic and Devanagari fonts
  would change slightly in 15 to 57 glyphs each, their rings (`o`, `٥`, `०`); they were not built again.
- **A stroke at 45 degrees is no longer lost in tracing.** The thinning that finds centerlines wore a straight
  45 degree stroke away to one pixel, so the slash `／` of Noto Sans CJK was drawn empty. Such a part is
  thinned again with a test that keeps it.
- **A retraced Chinese character keeps its sides straight after a round corner.** A drawn curve after a
  round turn could bow up to ten units off its stroke (the side of a handwritten 月). In dense characters it
  is now split where it strays more than six units.
- **A retraced Chinese character no longer loses a stroke in silence.** Skia could drop a stroke while it
  merged a dense character (the long stroke of a handwritten 水). The merge now checks that every stroke is
  inside it, and merges the strokes one at a time, or as polygons, if not.
- **A proof fills overlapping contours of a static font.** Proofs merged overlaps only for variable fonts, so
  in a static font with overlapping contours (a composite glyph, a font from another tool) the overlap, or a
  whole contour, came out blank. Every glyph is now merged by non-zero winding, as renderers fill it.
- **A variable font no longer clips its boldest instance on Windows.** Its `usWinAscent` and `usWinDescent`
  came from the default master only. Now they hold the tallest and the deepest glyph of every master.
- **A merge of shapes no longer loses a piece in silence.** Where two curves lie exactly on each other, the
  boolean engine can drop part of a glyph. `union` now checks that every contour is in the result, tries
  again with the contours a hair apart, and if that fails it keeps the overlaps and `build` warns with the
  name of the glyph.
- `whateverfont look --bg COLOR` keeps the ground that you chose. It used to paint a band of another ground
  behind a palette whose colors match the one you asked for (chalk figures with black bodies on a black board).
- **The footer of the site can no longer make the page longer.** A block that was thrown hard could pass
  through the floor and fall without end, and the page grew under it.

### Removed

- The `g_story` parameter, which did nothing.
