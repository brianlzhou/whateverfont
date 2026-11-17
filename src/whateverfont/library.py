"""The library: fonts that people add to the whateverfont repository by pull request.

An entry is a folder ``library/NAME`` with the design and a credit::

    library/snowday/
        entry.json     {"github": "octocat", "prompt": "the request, in the person's words"}
                       (and, if the person likes: "agent", "word" for the tile, "moods" for the search)
        font.py        the design (and the Python files it imports)
        BRIEF.md       the brief and the decisions

A pull request holds sources only. The repository builds the font files from them after the
merge, so every font on the library page is one that the engine drew from code a person read.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ENTRY = "entry.json"
#: A GitHub username: letters, figures and single hyphens, at most 39 characters.
USERNAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$")
#: What a pull request may put into an entry.
SOURCES = {".py", ".md", ".json"}
#: The design of a font is small. A large file in an entry is something else.
MAX_SOURCE_BYTES = 200_000
#: The web fonts of one entry, together.
MAX_FONT_BYTES = 4_000_000
LICENSE = "OFL-1.1"


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def find_repo(start: str | Path = ".") -> Path:
    """The checkout of the whateverfont repository at or above ``start``."""
    here = Path(start).resolve()
    for folder in (here, *here.parents):
        if (folder / "library" / "README.md").is_file() and (folder / "pyproject.toml").is_file():
            return folder
    raise ValueError(
        f"{here} is not inside a checkout of the whateverfont repository. Fork and clone it first "
        "(`gh repo fork brianlzhou/whateverfont --clone`), then pass --repo PATH or run the command in it.")


def entries(repo: Path) -> list:
    folder = Path(repo) / "library"
    return sorted(p for p in folder.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def read_entry(folder: Path) -> dict:
    try:
        data = json.loads((Path(folder) / ENTRY).read_text())
    except FileNotFoundError:
        raise ValueError(f"{folder.name}: no {ENTRY}") from None
    except ValueError as exc:
        raise ValueError(f"{folder.name}: {ENTRY} is not valid JSON ({exc})") from None
    if not isinstance(data, dict):
        raise ValueError(f"{folder.name}: {ENTRY} must hold one object")
    return data


def names_in_use(repo: Path, skip: Path | None = None) -> dict:
    """Family names that the examples and the other entries use: lower-case name -> where."""
    from . import project
    taken = {}
    folders = [p for p in sorted((Path(repo) / "examples").iterdir()) if (p / "font.py").is_file()]
    folders += [p for p in entries(repo) if (p / "font.py").is_file()]
    for folder in folders:
        if skip is not None and folder.resolve() == Path(skip).resolve():
            continue
        index = folder / "fonts" / "index.json"
        try:
            if index.is_file():
                names = [f["name"] for f in json.loads(index.read_text())["families"]]
            else:
                names = [f.name for f in project.load(folder).families]
        except Exception:
            continue        # a broken neighbor is reported where it is checked itself
        for name in names:
            taken[name.lower()] = f"{folder.parent.name}/{folder.name}"
    return taken


def problems(folder: Path, repo: Path, author: str | None = None, sources_only: bool = False,
             build: bool = True) -> list:
    """What is wrong with one entry, in plain words. An empty list means it can be merged."""
    from . import project
    folder = Path(folder)
    out = []
    if not SLUG.match(folder.name):
        out.append(f"the folder name {folder.name!r} must be 3 to 40 lower-case letters, figures and hyphens")
    try:
        entry = read_entry(folder)
    except ValueError as exc:
        return out + [str(exc).split(": ", 1)[-1]]
    user = entry.get("github")
    if not isinstance(user, str) or not USERNAME.match(user):
        out.append(f'{ENTRY}: "github" must be a GitHub username, for example "octocat"')
    elif author and user.lower() != author.lower():
        out.append(f'{ENTRY}: "github" is {user!r}, but the pull request is from {author!r}. '
                   "Credit goes to the account that opens the pull request")
    prompt = entry.get("prompt")
    if not isinstance(prompt, str) or not 8 <= len(prompt.strip()) <= 400:
        out.append(f'{ENTRY}: "prompt" must be the request that made the font, 8 to 400 characters')
    for key in entry:
        if key not in ("github", "prompt", "agent", "word", "moods"):
            out.append(f"{ENTRY}: unknown key {key!r} (the keys are github, prompt, agent, word and moods)")
    if "agent" in entry and not (isinstance(entry["agent"], str) and len(entry["agent"]) <= 60):
        out.append(f'{ENTRY}: "agent" must be a short name, for example "Claude Code"')
    # what the library page shows on the font's tile, and the words that its search finds the font by
    if "word" in entry and not (isinstance(entry["word"], str) and 1 <= len(entry["word"].strip()) <= 16):
        out.append(f'{ENTRY}: "word" must be one short word for the font\'s tile, 16 characters at most')
    if "moods" in entry and not (isinstance(entry["moods"], str) and 3 <= len(entry["moods"].strip()) <= 300):
        out.append(f'{ENTRY}: "moods" must be a few words for the search, 300 characters at most')

    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if rel.parts[0] in ("fonts", "proofs", "__pycache__") or rel.name in ("board.html", "feedback.json", ".build.json"):
            continue
        if path.is_symlink():
            out.append(f"{rel}: links are not allowed")
        elif path.is_dir():
            out.append(f"{rel}/: an entry has no folders of its own")
        elif path.suffix not in SOURCES:
            out.append(f"{rel}: an entry holds only .py, .md and .json files")
        elif path.stat().st_size > MAX_SOURCE_BYTES:
            out.append(f"{rel}: {path.stat().st_size // 1000} kB is too large for a design file")
    if sources_only and (folder / "fonts").exists():
        out.append("fonts/: leave the built fonts out. The repository builds them from your source after the merge")
    for name in ("font.py", "BRIEF.md"):
        if not (folder / name).is_file():
            out.append(f"{name} is missing")
    if out or not (folder / "font.py").is_file():
        return out

    try:
        proj = project.load(folder)
    except Exception as exc:
        return out + [f"font.py does not load: {type(exc).__name__}: {exc}"]
    taken = names_in_use(repo, skip=folder)
    for fam in proj.families:
        if fam.license != LICENSE:
            out.append(f"{fam.name}: the license must be {LICENSE} (it is {fam.license!r}), so others may use the font")
        if fam.name.lower() in taken:
            out.append(f"{fam.name}: {taken[fam.name.lower()]} already has a family of this name")
        if not fam.copyright:
            out.append(f'{fam.name}: give the family a copyright line, for example copyright="Copyright 2026 Your Name"')
    if build and not out:
        scratch = _scratch(folder)
        try:
            results = project.build(project.load(scratch), variable=True, force=True)
            for name, res in results.items():
                out += [f"{name}: {w}" for w in res.warnings]
            size = sum(p.stat().st_size for p in scratch.rglob("*.woff2"))
            if size > MAX_FONT_BYTES:
                out.append(f"the web fonts are {size / 1e6:.1f} MB together; the limit is {MAX_FONT_BYTES / 1e6:.0f} MB. "
                           "Keep the character set small with latin().only()")
        except Exception as exc:
            out.append(f"the build failed: {type(exc).__name__}: {exc}")
        finally:
            shutil.rmtree(scratch.parent, ignore_errors=True)
    return out


def _scratch(folder: Path) -> Path:
    """A copy of an entry's sources in a temporary folder, to build without touching the entry."""
    import tempfile
    target = Path(tempfile.mkdtemp(prefix="whateverfont-library-")) / folder.name
    target.mkdir()
    for path in folder.iterdir():
        if path.is_file() and path.suffix in SOURCES:
            shutil.copyfile(path, target / path.name)
    return target


def add(project_dir: str | Path, repo: str | Path, github: str, prompt: str | None = None, agent: str | None = None,
        name: str | None = None, update: bool = False) -> Path:
    """Copy a project's sources into ``repo/library`` with a credit. Returns the new entry's folder."""
    from . import project
    if not USERNAME.match(github or ""):
        raise ValueError(f"{github!r} is not a GitHub username")
    src = Path(project_dir)
    proj = project.load(src)
    repo = Path(repo)
    target = repo / "library" / (name or slug(proj.family.name))
    if not SLUG.match(target.name):
        raise ValueError(f"{target.name!r} cannot be a folder name; pass --name with 3 to 40 lower-case letters")
    if target.exists():
        if not update:
            raise FileExistsError(f"{target} exists. Pass --update to replace your own entry, or --name for another folder")
        owner = read_entry(target).get("github", "")
        if owner.lower() != github.lower():
            raise ValueError(f"{target.name} belongs to {owner}; choose another name with --name")
        shutil.rmtree(target)
    if not prompt:
        prompt = _first_brief_line(src / "BRIEF.md")
    if not prompt:
        raise ValueError('pass --prompt "the request that made the font"')
    target.mkdir(parents=True)
    for path in sorted(src.iterdir()):
        if path.is_file() and path.suffix == ".py" or path.name == "BRIEF.md":
            shutil.copyfile(path, target / path.name)
    entry = {"github": github, "prompt": " ".join(prompt.split())}
    if agent:
        entry["agent"] = agent
    (target / ENTRY).write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
    return target


def _first_brief_line(path: Path) -> str:
    """The first paragraph under '## Brief' in BRIEF.md: the request in the person's words."""
    try:
        text = path.read_text()
    except OSError:
        return ""
    m = re.search(r"^## Brief\s*\n+(.+?)(?:\n\s*\n|\Z)", text, re.S | re.M)
    return " ".join(m.group(1).split()).strip('"“”')[:400] if m else ""


def check(repo: str | Path, only: list | None = None, author: str | None = None, sources_only: bool = False,
          build: bool = True) -> dict:
    """Problems of every entry (or of the named ones): folder name -> list."""
    repo = Path(repo)
    found = {}
    for folder in entries(repo):
        if only and folder.name not in only:
            continue
        found[folder.name] = problems(folder, repo, author=author, sources_only=sources_only, build=build)
    for name in only or []:
        if name not in found:
            found[name] = [f"library/{name} does not exist"]
    return found


def build(repo: str | Path, only: list | None = None) -> dict:
    """Build the fonts of the entries into their folders: folder name -> BuildResult by family."""
    from . import project
    done = {}
    for folder in entries(Path(repo)):
        if only and folder.name not in only:
            continue
        done[folder.name] = project.build(project.load(folder), variable=True, force=False)
    return done


def changed(repo: str | Path, since: str) -> list:
    """The entries that differ from the git revision ``since`` (for example origin/main): folder names.

    A name that cannot be an entry's folder is left out and reported by ``check``, so the result is
    safe to pass to a shell.
    """
    import subprocess
    out = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", f"{since}...HEAD", "--", "library"],
                         capture_output=True, text=True, check=True).stdout
    names = {line.split("/")[1] for line in out.splitlines() if line.count("/") >= 2}
    return sorted(n for n in names if SLUG.match(n))
