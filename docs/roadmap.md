# Roadmap

What version 0.1 does not do, in rough order of value.

## Character coverage

The basic set covers GF Latin Core, the set Google Fonts requires of every Latin family, Vietnamese, Pinyin,
and the letters of Azerbaijani, Yoruba, Igbo and Hausa: 605 code points, combining marks with `mark`, `mkmk`
and `ccmp`, and `locl` forms for Romanian, Moldovan and Catalan. It also has the signs of a popular open font
such as [Intern](https://github.com/bvvst/intern) (a rounded version of Inter): the Mac Roman math set, 34
currency signs, arrows, checks and shapes, superscripts, subscripts and fractions, with the `frac`, `numr`,
`dnom`, `sups`, `subs`, `sinf`, `ordn`, `zero`, `case` and `pnum` features. Modern Greek and Cyrillic add
195 code points: 800 in all. In order of value, the next groups are:

| Group | Characters | Why |
|---|---|---|
| Pan-African | the other letters of the set, such as `Ɛ ɛ Ɔ ɔ Ƴ ƴ ʼ` with their accents | 167 languages and 276 M speakers. `Ɓ ɓ Ɗ ɗ Ƙ ƙ Ŋ ŋ ə Ə ṣ ẹ ọ` are done. |
| Old-style figures | `onum` and `lnum`, and old-style figures for a text face | Figures that sit with lowercase. |
| Superscript letters | `ᵃ ⁿ` and the rest, for `ordn` in more languages | `ⁱ ª º` are done. |
| Monospace | Powerline (9), programming ligatures (`->`, `=>`, `!=`) as an optional feature | Box drawing and blocks are done. |

Sources: the [Google Fonts glyph sets](https://github.com/googlefonts/glyphsets), the
[Adobe Latin character sets](https://github.com/adobe-type-tools/adobe-latin-charsets), fontbakery's
[coverage check](https://github.com/fonttools/fontbakery/blob/main/Lib/fontbakery/checks/vendorspecific/googlefonts/glyph_coverage.py),
and a count of 16 popular open fonts.

## Better letters

- Tune `S`, `a`, `g`, `&`, `@`, `2` and `5`, and the bold weights of the condensed designs. The heavy condensed
  `Æ` closes up.
- A two-story `g` and other alternates, chosen by a parameter as `a_story` is now.
- Old-style figures and the `onum` feature. Proportional figures and the `case`, `tnum` and `pnum` features are done.
- Kerning for accented letters, and classes instead of single pairs to make files smaller. Greek and
  Cyrillic took a font from about 4,000 pairs to about 18,000, which is 10 KB of each WOFF2 file.

## Serifs and italics

- Done: slab serifs (`serif`, `serif_weight`). Free stem ends get slabs, arms get beaks, and slabs that meet
  across a narrow counter are shortened. `examples/platen` is a typewriter face built on them.
- Bracketed serifs: a slab that curves into the stem, with the bracket's size as a parameter. Then a `SERF`
  axis that runs from sans through flare to serif. An axis that turns slabs on from nothing needs slabs of
  zero length in the sans master, so that every master has the same strokes.
- Serifs on the signs of code (`{ } [ ] < >`) and on `C G S` (beaks), chosen by a parameter.
- Cursive italic forms for `a e f g k v w y z`, so an italic is more than a slanted roman.

## More scripts

| Script | Plan | Effort |
|---|---|---|
| German, Spanish, French, Galician, Breton and the other languages of GF Latin Core | They work today: every font has their letters. Breton's `ʼ` (U+02BC) is there too. | Done |
| Vietnamese | The full set (`latin()`, `mono()`) has the whole alphabet: 98 code points more, with the horn of `ơ ư`, the hook above, the dot below, letters with two marks, the dong sign `₫`, and the combining hook, dot and horn. The marks of a stack are placed by measuring their outlines, and they fit under the top of the line, so the line spacing did not change. A reader of Vietnamese should still review the marks, most of all the capitals of heavy weights, where the stacks get flat. | Done, waiting for a review |
| Greek | The full set has modern (monotonic) Greek: 71 code points with the tonos, the dialytika, the question mark and the ano teleia. 14 capitals draw their Latin twins; `Γ Π Φ` are the Cyrillic ones; the lowercase have recipes of their own. Next: polytonic Greek (about 200 letters with breathings and the perispomeni), and a reader's review of `α γ ζ ξ ς` and of the tonos on the capitals. | Done, waiting for a review |
| Cyrillic | The full set has U+0400 to U+045F, `Ґ ґ`, and the letters of Kazakh, Uzbek, Tatar, Tajik and Kyrgyz: 124 code points. Shared letters draw their Latin twins, the lowercase are mostly small capitals, and `Д Л` have their feet. Next: the Bulgarian forms and the Serbian and Macedonian ones under `locl`, the other languages of Cyrillic Extended, and a reader's review. | Done, waiting for a review |
| Kana | A first version exists: `whateverfont.kana` expands KanjiVG centerlines with the family's pen (see below). It needs spacing, punctuation, small-kana tuning and a reader's review. | 1 to 2 days |
| Kanji | The 2,136 jouyou kanji from KanjiVG. Most of the work is cleaning stroke joins. Expect 1 to 2 MB per weight. | 2 to 4 weeks |
| CJK by remix | Round, embolden or slant an open CJK font such as Zen Maru Gothic or M PLUS. Faster, but it is a derivative of that font. | 1 week |
| Chinese | The pen model fits: a hanzi is centerline strokes. Open stroke data exists (Make Me a Hanzi has medians for 9,000 characters; its data comes from Arphic fonts, so check that license first). The work is the joins, the stroke ends that give a style its look, and proofing thousands of glyphs. Expect 3 to 6 MB per weight. | 4 to 8 weeks |
| Any script, by retracing | `whateverfont retrace` traces the centerlines of an open font and redraws them with a family's pen and effect, keeping the font's shaping tables (see [scripts](scripts.md)). The letter shapes are the source's. `examples/retrace` has Arabic, Devanagari, Japanese, Simplified Chinese (GB 2312 level 1), Traditional Chinese (Big5 level 1) and Korean in four families, and the site shows them in each language. It needs a reader's review of each script, and fixes for the classes of glyph the self-check flags: tight curls, stacked marks, word ligatures, the densest characters. | Done, waiting for a review |
| Arabic, drawn | Own recipes instead of a traced source. A letter has up to four joined forms, so basic Arabic is about 120 glyphs with new recipes. It needs the joining features (`init`, `medi`, `fina`, `rlig`), cursive attachment, mark placement over joined letters, and spacing that has no gaps. Proofs already shape right-to-left text. | 4 to 6 weeks, with a reader of Arabic |
| Devanagari and the other Indic scripts, drawn | Own recipes instead of a traced source. The shaper reorders the letters, but the font must hold the half forms, a few hundred conjuncts, the vowel signs in several widths and the features that choose them. Each script is its own project. | 4 to 8 weeks for each script, with a reader of it |

### Kana today

```python
from whateverfont import Family, kana, latin

kana.download("data/kanjivg")                 # 177 files from KanjiVG, on request
recipes = latin()
recipes.update(kana.recipes("data/kanjivg"))
FAMILY = Family(name="My Kana", recipes=recipes, license=kana.LICENSE,
                copyright="Copyright 2026 Me. " + kana.CREDIT)
```

KanjiVG is licensed CC BY-SA 3.0. A font that contains these kana must credit KanjiVG and carry the same
license, which is why the example sets `license` and `copyright`. WhateverFont does not ship the data or any
font made from it.

A reviewer who reads the script must check every new script. Non-native designers get `д`, `л`, `ж`, `α`
and `λ` wrong.

## Engine

- An optical size axis that widens spacing and lowers contrast at small sizes.
- Color fonts with axes, and gradients (COLR version 1) with a version 0 fallback.
- Smaller painted fonts: marks as components of a few shared brush shapes, placed with transforms.
- Effects in variable fonts: a stencil whose bridges are part of the skeleton, so every master has them.
- Parallel builds on Windows, where processes cannot be forked.
- A check that runs Google's fontbakery on built files.
- Hinting with ttfautohint as an option for static files.

## Agent loop

- A critic: a second agent that only looks at proofs and names the three things that matter most.
- A scratch space for trying one glyph without rebuilding a family.
- An MCP server that wraps `build`, `look` and `probe`.
