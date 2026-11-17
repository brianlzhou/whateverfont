# Security

## Report a problem

Report a security problem in private, through GitHub: open the
[Security tab](https://github.com/brianlzhou/whateverfont/security) of this repository and press
"Report a vulnerability". Do not open a public issue for it.

## What to know before you run it

- **A font project is code.** `whateverfont build DIR` runs `DIR/font.py` with Python. Build a project only if
  you trust the person who wrote it, as you would with any script. The public library takes sources only, and a
  maintainer reads each `font.py` before the fonts are built.
- **`remix` and `retrace` read font files.** They parse the file you give them with fontTools. A broken or
  hostile font file can make the command fail. Report a file that does worse than that.
- **The site's vote counter** (`worker/`) has no accounts. It marks a visitor by a hash of the address the
  request came from, with a secret that the Worker makes once, and it never keeps the address itself. A
  vote keeps that mark until it is taken back. A view keeps it for one day.

## Supported versions

Fixes go into the newest release on PyPI and npm.
