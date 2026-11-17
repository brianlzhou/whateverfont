# Retrace: the project's families in Arabic, Devanagari, Japanese, Chinese and Korean

## The request

Show the project's fonts in other scripts on the project site: Arabic, Hindi, Japanese, Chinese and Korean
readers should see the tagline in Last Bell, Last Bell Snow, Neon Glow and Gantry. A second request added
Traditional Chinese, for readers in Taiwan, as fonts of their own.

## The method

WhateverFont has recipes for Latin, Greek and Cyrillic. Drawing Arabic or Devanagari from scratch is weeks of
work for each script, with a reader of it. This project redraws open fonts instead: `whateverfont retrace`
traces the centerline of every glyph of a source font and draws it again with a family's pen and, for the
color families, its effect. The shaping tables of the source stay as they are, so Arabic letters join, marks sit
on their anchors, and Devanagari conjuncts form.

**The letter shapes come from the source fonts.** The pen (weight, contrast, round or flat ends, the dots) and
the effects (snow, glow) are this project's. The skeletons are not.

## The sources, chosen by family

| Family | Arabic from | Devanagari from | Why |
|---|---|---|---|
| Last Bell, Last Bell Snow | Playpen Sans Arabic (TypeTogether) | Kalam (Indian Type Foundry) | Marker letters need handwriting. Traced from Noto Sans they looked like type. |
| Neon Glow, Gantry | Noto Sans Arabic | Noto Sans Devanagari | A tube and a technical sans fit a plain, even sans. |

| Family | Japanese from | Simplified Chinese from | Traditional Chinese from | Korean from |
|---|---|---|---|---|
| Last Bell, Last Bell Snow | Klee One (Fontworks) | LXGW WenKai GB (LXGW) | LXGW WenKai TC (LXGW) | Gaegu (JIKJI SOFT) |
| Neon Glow, Gantry | Noto Sans JP Light | Noto Sans SC Light | Noto Sans TC Light | Noto Sans KR Light |

The rule is: a handwritten family is traced from a handwritten open font, a technical family from
Noto Sans. Each Chinese font is traced from a source made for its region. LXGW WenKai GB draws the forms of
mainland China and sets its commas and stops at the lower left. LXGW WenKai TC draws Taiwan's forms and
centers its stops. The first Simplified fonts were traced from LXGW WenKai TC, with its stops moved; they
had Taiwan's forms, which look odd to a reader in mainland China, so they were traced again from LXGW WenKai
GB. A heavy brush font (Ma Shan Zheng) was tried in a pilot and broke into lumps. Noto Sans CJK is traced
from its Light weight, whose thin strokes leave the most white for a heavier pen.

All the sources are under the SIL Open Font License 1.1. Each folder (`noto/`, `kalam/`, `playpen/`) holds
the Arabic and Devanagari fonts and an `OFL.txt` with their copyright lines. The Japanese, Chinese and Korean
sources are 3 to 26 MB each and are not in the repository: `sources.json` lists their URLs, SHA-256 and
copyright lines, `build.py` fetches a missing one into `.cache/sources/`, and each of their font folders
holds an `OFL.txt` with the source's copyright line. Playpen Sans Arabic is a variable font: it is traced
at its default weight (400). The sources have thin, even strokes, which the tracer follows best; a brush
font breaks into lumps (`retrace` warns about one).

## Decisions

- Each family is drawn with the pen of its default style: Last Bell at its Bold default (weight 132), Neon
  Glow with the Neon tube (62), Gantry at Regular (80).
- Snow on Devanagari lies shallower (`depth=72` instead of 112), so the headline keeps its red under it.
- Names follow the Latin family: "Last Bell Arabic", "Last Bell Snow Devanagari". The Simplified Chinese
  fonts kept their first names ("Last Bell Chinese"); the Traditional ones are "Last Bell Traditional
  Chinese" and so on. The site calls the two scripts Simplified Chinese (`zh`) and Traditional Chinese
  (`zh-Hant`). The names of the sources
  (Noto, Kalam, Playpen, Klee) are not used: the license or a trademark reserves them for the originals.
- Each Arabic and Devanagari font keeps every glyph of its source, so readers can type their own text.
  Kalam and Playpen Sans Arabic also cover Latin, so those fonts have traced Latin letters too; use the Latin
  family for Latin text.
- The Japanese, Chinese and Korean fonts keep the common characters (`--only japanese`, `chinese`,
  `traditional`, `korean`): kana and the 2,965 kanji of JIS X 0208 level 1, the 3,755 characters of GB 2312
  level 1, the 5,401 characters of Big5 level 1, the 2,350 Hangul syllables of KS X 1001, and their
  punctuation. They have no Latin letters or figures.
- Last Bell is much heavier than the white between the strokes of a kanji allows. Each dense character is
  drawn thinner, and the whole font no heavier than its median character allows: Last Bell Japanese draws
  at 58% of its stem, Last Bell Chinese at 74%, Last Bell Traditional Chinese at 69% and Last Bell
  Korean at 89%. In Japanese the chunky look of
  the Latin Last Bell does not survive (Klee One leaves the least white): the alternative was characters
  that fill in.
- Snow lies shallower on these scripts (`depth=44`), and Neon Glow glows half as wide (`size=40`), so that
  the white between strokes stays. Snow has no drips there: a lump under a stroke reads as a dot, and a dot
  can change the character (大, 犬).

## What to check

- A reader of Arabic and a reader of Hindi should read the proofs (`proofs/`, made by `build.py`) and type
  their own words, most of all the marks over joined letters, shadda with a vowel, the lam-alef, the
  conjuncts and the vowel signs with candrabindu.
- A reader of Japanese, Chinese and Korean should read `proofs/japanese-families.png`,
  `chinese-families.png`, `traditionalchinese-families.png` and `korean-families.png` and the proof of
  each font, most of all the densest characters, the dakuten and handakuten, and the small rings of Hangul.
- `build.py` prints every glyph the self-check flags. Most are the large word ligatures (U+FDF2 to U+FDFD) and
  stacked marks, and in the new scripts the characters too dense for Last Bell.

## Build

`python examples/retrace/build.py`, with numpy installed (the `trace` extra, as in CONTRIBUTING.md). Give
script names (`Japanese Chinese Traditional Korean`) to build only those, and `--family "Last Bell"` to build
one family only. Arabic and Devanagari take about a minute and a half on eight cores. On sixteen, Japanese
takes about six and a half minutes, Chinese eight, Traditional Chinese about eighteen and Korean three:
most of it is the snow.

The Japanese, Chinese and Korean fonts are committed as WOFF2 files and CSS only: with their TTF files the
sixteen fonts take over 150 MB. `build.py` writes the TTF files (git ignores them), and `index.json` lists
the characters of each font, so the site builds without them.
