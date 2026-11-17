# The library

Fonts that people made with WhateverFont and gave to everyone. Each one is on the
[library page](https://fonts.brianzhou.org/library/) with the name of the person who added it.

## Add your font

You need a font project that builds (a folder with `font.py` and `BRIEF.md`), a GitHub account, and the
[GitHub CLI](https://cli.github.com).

```sh
gh repo fork brianlzhou/whateverfont --clone && cd whateverfont
whateverfont library add PATH/TO/YOUR/FONT --github YOUR_USERNAME
```

The command copies the design into `library/NAME`, writes the credit, builds the font once to check it, and
prints the three commands that open the pull request. An agent can run all of it: say "add this font to the
WhateverFont library under my GitHub name".

## What an entry holds

```
library/snowday/
  entry.json    {"github": "octocat", "prompt": "the request, in your words", "agent": "Claude Code"}
  font.py       the design, and the Python files it imports
  BRIEF.md      the brief and the decisions
```

`github` is the account that gets the credit, and it must be the account that opens the pull request.
`prompt` is the request that made the font. `agent` is optional.

Two more keys are optional. `word` is the one word that the font's tile shows on the site, such as
`"word": "Snow"`. Without it the tile shows the start of your sample text. `moods` is a few words for the
library's search, such as `"moods": "calm office report plain"`. Without it the search reads the font's name,
your prompt and the descriptions of its families.

Leave the built fonts out. After the merge, the `library` workflow builds the fonts from your source and
commits them, so every font file in the library is built from source that is in the repository.

## The rules

- **It is your design.** Do not trace, copy or rename an existing typeface, and do not add a remix.
- **It is open.** The license of every family is the SIL Open Font License 1.1 (`license="OFL-1.1"`, the
  default), and each family has your copyright line.
- **The name is new.** The check refuses a family name that an example or another entry of the library
  already uses. It does not look outside this repository, so search the web for the name yourself first.
- **It builds clean.** `whateverfont build` gives no warning, and the web fonts are 4 MB or less together.
- **Sources only.** `.py`, `.md` and `.json` files, 200 kB each at most, and no folders.

`whateverfont library check` runs the same checks that the pull request runs.

## For maintainers

`font.py` is code, and a build runs it. Read every Python file of an entry before you build it on your own
computer. The check on a pull request runs without secrets.

After a merge, a maintainer starts the `library` workflow, which builds the fonts and commits them. To do it by hand:

```sh
whateverfont library build && git add library && git commit -m "Build the library fonts"
```
