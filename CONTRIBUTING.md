# Contributing

Thank you for looking. WhateverFont is young, and the most useful contributions right now are better letters.

## Set up

```sh
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,trace]"
.venv/bin/python -m pytest -q
```

The `trace` extra installs numpy, which `whateverfont retrace` and its tests need. The whole suite takes a few
minutes. The tests of the site's search and of the vote counts run with Node (22.5 or newer for the counts),
and pytest skips them when Node is missing.

## Ways to help

- **Add your font to the library.** `whateverfont library add DIR --github YOUR_USERNAME` prepares the entry,
  and [library/README.md](library/README.md) has the rules. This is the easiest contribution, and your name
  goes on the library page.
- **Improve a recipe.** Recipes live in `src/whateverfont/recipes`. Draw the letter at several settings before
  and after your change and attach both pictures to the pull request:
  `whateverfont look examples/arroyo --xray "S"` and `whateverfont look examples/arroyo --styles`.
- **Add or review a script.** [docs/roadmap.md](docs/roadmap.md) lists what each script still needs: a
  review of the Vietnamese, Greek and Cyrillic letters by people who read them, polytonic Greek, the
  Bulgarian and Serbian forms of Cyrillic, spacing and punctuation for the kana, and Arabic and Devanagari
  drawn with recipes of their own.
- **Add a preset or an example project.** A good example has a real brief and records its decisions.
- **Add an effect.** Effects live in `src/whateverfont/effects.py`; [docs/effects.md](docs/effects.md) explains
  how they work. An effect needs a row in that page, a line in `tests/test_build.py`, and a picture in the
  pull request.
- **Make a font and say what tripped you up.** Several fixes in the engine came from the notes of agents
  that made one font each. A list of what was confusing is a welcome issue.
- **Report a bad shape.** Open an issue with the output of `whateverfont look ... --text "the word"` and the
  project's `font.py`.

## Rules for recipes

1. Take every measurement from the builder (`g.sw`, `g.xh`, `g.cw`). A number that does not scale with the
   parameters will break at some weight.
2. A recipe must draw at weight 44 and at weight 150, in every preset. `tests/test_family.py` checks this.
3. A recipe must have the same structure in every master: the same strokes, the same nodes, the same
   segment kinds. Do not add or drop a node depending on a parameter. The tests check this too.
4. Keep the radius of a curve larger than half the stroke width, or the inside of the curve folds.

## Fonts and licenses

Do not add outlines traced or copied from a font you do not have the right to modify. Remix examples must
start from a font under an open license, keep its notices, and use a new name.

## Built files

The example folders hold built fonts and review boards so that a visitor can look without installing
anything. They are binary and large. Rebuild them (`python scripts/build_examples.py`) only in a commit that
is about the examples or that changes how letters are drawn, and keep that commit separate from the code.
Builds are reproducible, so a rebuild that changes no drawing changes no file. Proof sheets are not kept in
git: `whateverfont look` makes them.

## Commits

Write the subject as a short imperative sentence ("Add the Greek capitals"). Say why in the body if the
reason is not obvious. Keep one change per commit.

## Releasing

1. Set the new version in `pyproject.toml`, `src/whateverfont/__init__.py`, `npm/package.json` and
   `.claude-plugin/plugin.json`.
2. Add an entry for the version at the top of `CHANGELOG.md`.
3. Commit, and push a tag `vX.Y.Z`. The `release` workflow (`.github/workflows/release.yml`) builds the
   package and publishes it to PyPI. It stops if the tag does not match the version in `pyproject.toml`.
4. After PyPI has the new version, run `npm publish` in `npm/`. The npm package runs the PyPI version with
   its own version number, so it fails until PyPI has that version.
