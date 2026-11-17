# whateverfont

**WhateverFont You Want.** Describe a typeface in plain words. An AI agent draws it, checks its own proofs, and
gives you real font files.

WhateverFont is a Python tool. This package runs it through [uv](https://docs.astral.sh/uv/) (or pipx), so
that it works from Node without a setup step.

```sh
npx whateverfont setup        # installs the command, and gives Claude Code the skill
```

Then say, in Claude Code or any coding agent: "Use whateverfont. Make me a font that ..."

`npx whateverfont ARGS` runs any command of the tool, for example `npx whateverfont presets`.

The project, the docs and the fonts: https://github.com/brianlzhou/whateverfont and
https://fonts.brianzhou.org
