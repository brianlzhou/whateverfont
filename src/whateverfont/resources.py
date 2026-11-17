"""Files that ship with whateverfont: the agent skill, the reference pages and the example sources.

In an installed package they are in ``whateverfont/_data``. In a checkout of the repository they
are where the repository keeps them.
"""

from __future__ import annotations

import shutil
from pathlib import Path

#: Reference pages an agent reads, in the order it needs them.
PAGES = {
    "workflow": "the method, from brief to delivery",
    "parameters": "every parameter, with usual ranges",
    "recipes": "the drawing vocabulary, for a new or replaced letter",
    "effects": "stencil, inline, shadow, glow and paint; color, picture and monospaced fonts",
    "scripts": "Arabic, Devanagari, Japanese, Chinese, Korean: retrace an open font with a family's pen",
    "roadmap": "what whateverfont does not do yet",
}


def root() -> Path:
    here = Path(__file__).resolve().parent
    packed = here / "_data"
    return packed if packed.is_dir() else here.parents[1]


def skill_file() -> Path:
    return root() / "skills" / "whateverfont" / "SKILL.md"


def docs_dir() -> Path:
    return root() / "docs"


def examples_dir() -> Path:
    return root() / "examples"


def page(name: str) -> Path:
    path = docs_dir() / f"{name.removesuffix('.md')}.md"
    if not path.is_file():
        raise ValueError(f"no reference page named {name!r}; choose from {', '.join(PAGES)}")
    return path


def examples() -> list:
    """(name, first line of the module docstring) for each example that has a font.py."""
    out = []
    folder = examples_dir()
    for font in sorted(folder.glob("*/font.py")) if folder.is_dir() else []:
        text = font.read_text()
        first = text.split('"""')[1].strip().splitlines()[0] if text.startswith('"""') else ""
        out.append((font.parent.name, first))
    return out


def install_skill(dest: Path) -> Path:
    """Copy the skill into ``dest`` (a skills folder) and return the file written."""
    folder = Path(dest).expanduser() / "whateverfont"
    target = folder / "SKILL.md"
    for link in (folder, target):
        if link.is_symlink():
            link.unlink()        # a link into a checkout: replace it with a copy
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(skill_file(), target)
    return target
