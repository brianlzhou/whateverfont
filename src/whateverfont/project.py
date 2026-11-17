"""A font project: a folder with ``font.py`` and ``BRIEF.md``.

``font.py`` defines ``FAMILY`` (the design), and may define ``DIRECTIONS``
(a list of alternative families to compare on the review board).
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .compile import BuildResult, build_family, slug
from .family import Family

FONT_TEMPLATE = '''"""{name}: {summary}"""

from whateverfont import Axis, Family
from whateverfont.presets import preset

# The base is the default style: what the reader gets with no settings.
# Start from a preset and change any parameter (see docs/parameters.md).
BASE = preset("{preset}")

# An axis maps a value the reader picks to parameters. The arguments are the tag,
# the name, the minimum, the default and the maximum, then the poles: the
# parameters at the ends. The default has no pole, because it is BASE.
AXES = [
    Axis("wght", "Weight", 300, 400, 800, {{300: {{"weight": 50}}, 800: {{"weight": 150}}}}),
    Axis("slnt", "Slant", -11, 0, 0, {{-11: {{"slant": 11}}}}),
    # A width axis, from condensed to wide:
    # Axis("wdth", "Width", 75, 100, 125, {{75: {{"width": 0.75}}, 125: {{"width": 1.22}}}}),
]

# Named styles are points on the axes. Each one is also built as its own file.
STYLES = {{
    "Regular": {{}},
    "Italic": {{"slnt": -11}},
    "Bold": {{"wght": 700}},
    "Bold Italic": {{"wght": 700, "slnt": -11}},
}}

FAMILY = Family(
    name="{name}",
    description="",        # one sentence about the design, for the font file and the review board
    base=BASE,
    axes=AXES,
    styles=STYLES,
    sample="{sample}",
)

# To compare several directions on the review board, define more families and
# list them. Make them differ in kind (contrast, proportions, terminals), not
# only in spacing, and give each a one-sentence description.
#
#     SHARP = Family(name="{name} Sharp", description="Higher contrast, pointed.",
#                    base=preset("glyphic"), axes=AXES, styles=STYLES, sample=FAMILY.sample)
#     DIRECTIONS = [FAMILY, SHARP]

# To redraw a letter, replace its recipe (see docs/recipes.md):
#
#     @FAMILY.recipes.add("l", "l")
#     def l(g):
#         g.stem(g.L, 0, g.asc)
#         g.frame(g.sw)
'''

BRIEF_TEMPLATE = """# {name}

## Brief

{brief}

## Decisions

Write down each design decision and why you made it, newest last.

## Feedback

Notes from the review board go here, with the date.
"""


@dataclass
class Project:
    path: Path
    family: Family
    directions: list = field(default_factory=list)
    brief: str = ""
    #: Files outside the project folder that ``font.py`` imported. A build depends on them too.
    sources: list = field(default_factory=list)

    @property
    def families(self) -> list:
        """Every family in the project: the directions, or just the one family."""
        return self.directions or [self.family]

    def out_dir(self, family: Family) -> Path:
        return self.path / "fonts" / slug(family.name)

    def proofs_dir(self) -> Path:
        return self.path / "proofs"

    def feedback(self) -> dict | None:
        f = self.path / "feedback.json"
        return json.loads(f.read_text()) if f.exists() else None


def load(path: str | Path) -> Project:
    path = Path(path)
    if path.is_file():
        path = path.parent
    source = path / "font.py"
    if not source.exists():
        raise FileNotFoundError(f"{source} not found. Run `whateverfont new {path}` to start a project.")
    before = set(sys.modules)
    # font.py may import modules that sit next to it. They are loaded fresh each time, so two
    # projects may both have a helper called paint.py.
    here = str(path.resolve())
    sys.path.insert(0, here)
    try:
        ns = runpy.run_path(str(source))
    finally:
        if here in sys.path:
            sys.path.remove(here)
        for name in set(sys.modules) - before:
            f = getattr(sys.modules[name], "__file__", None)
            if f and Path(f).resolve().parent == path.resolve():
                del sys.modules[name]
    directions = list(ns.get("DIRECTIONS") or [])
    family = ns.get("FAMILY") or (directions[0] if directions else None)
    if family is None:
        raise ValueError(f"{source} must define FAMILY (a whateverfont.Family) or DIRECTIONS (a list of them)")
    brief = (path / "BRIEF.md").read_text() if (path / "BRIEF.md").exists() else ""
    return Project(path, family, directions, brief, _imported(before, path))


def _imported(before: set, project_dir: Path) -> list:
    """Source files that loading font.py pulled in from outside the project and outside installed packages."""
    here = Path(__file__).resolve().parent
    root = project_dir.resolve()
    out = []
    for name in set(sys.modules) - before:
        f = getattr(sys.modules.get(name), "__file__", None)
        if not f or not f.endswith(".py"):
            continue
        f = Path(f).resolve()
        if "site-packages" in f.parts or here in f.parents or root in f.parents:
            continue
        if str(f).startswith((str(Path(sys.base_prefix).resolve()), str(Path(sys.prefix).resolve()), sys.base_prefix, sys.prefix)):
            continue
        out.append(f)
    return sorted(out)


def _summary(brief: str, limit: int = 110) -> str:
    """The first sentence of the brief, shortened at a word if it is long."""
    line = " ".join((brief.strip().splitlines() or ["A custom typeface."])[0].split())
    line = line.replace('"', "'").replace("\\", "/") or "A custom typeface."
    for stop in (". ", "! ", "? "):
        cut = line.find(stop)
        if 0 < cut < limit:
            return line[:cut + 1]
    if len(line) <= limit:
        return line
    return line[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def create(path: str | Path, name: str, preset_name: str = "humanist", brief: str = "", sample: str = "") -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    source = path / "font.py"
    if source.exists():
        raise FileExistsError(f"{source} already exists")
    summary = _summary(brief)
    source.write_text(FONT_TEMPLATE.format(name=name, summary=summary, preset=preset_name,
                                           sample=(sample or "Sphinx of black quartz, judge my vow.").replace('"', "'")))
    (path / "BRIEF.md").write_text(BRIEF_TEMPLATE.format(name=name, brief=brief or "Describe the typeface you want."))
    return path


def build(project: Project, variable: bool = True, only: str | None = None, force: bool = True,
          on_build=None) -> dict:
    """Build every family of the project. Returns family name -> BuildResult.

    With ``force=False`` a family whose inputs have not changed since its last
    build is not built again: the result comes from the record of that build.
    ``on_build(family, reused)`` is called for each family.
    """
    results = {}
    for fam in project.families:
        if only and fam.name != only:
            continue
        out = project.out_dir(fam)
        mark = fingerprint(project, fam)
        res = None if force else _recorded(out, mark, variable, fam)
        reused = res is not None
        if res is None:
            res = build_family(fam, out, variable=variable)
            write_css(fam, res, out)
            _record(out, mark, variable, res)
        results[fam.name] = res
        if on_build is not None:
            on_build(fam, reused)
    if not only:
        _remove_stale(project)
    write_index(project, results)
    return results


def grounds(family) -> dict:
    """For each palette that white paper would hide (white snow, a white-hot tube): a ground that shows it."""
    from . import proof
    from .color import _rgba
    out = {}
    for name, palette in family.palettes.items():
        colors = [tuple(round(v * 255) for v in c[:3]) for c in map(_rgba, palette.values()) if c[3] > 0.38]
        ground = proof.ground_for(colors)
        if ground != proof.PAPER:
            out[name] = ground
    return out


def write_index(project: Project, results: dict) -> Path:
    """``fonts/index.json``: what the project holds, for a web page or a script that wants to use it.

    One entry per family: its name, description, sample, styles, axes, palettes and files. ``grounds``
    names a background for each palette that would not show on white.
    """
    path = project.path / "fonts" / "index.json"
    try:
        known = {f["name"]: f for f in json.loads(path.read_text())["families"]}
    except (OSError, ValueError, KeyError):
        known = {}
    rel = lambda q: str(Path(q).relative_to(project.path))
    families = []
    for fam in project.families:
        res = results.get(fam.name)
        if res is None:
            if fam.name in known:
                families.append(known[fam.name])
            continue
        out = project.out_dir(fam)
        families.append({
            "name": fam.name, "description": fam.description, "sample": fam.sample,
            "styles": list(res.statics), "palettes": list(fam.palettes), "grounds": grounds(fam),
            "axes": [{"tag": a.tag, "name": a.name, "min": a.minimum, "default": a.default, "max": a.maximum}
                     for a in fam.axes] if res.variable else [],
            "glyphs": len(fam.recipes), "license": fam.license,
            "css": rel(out / f"{slug(fam.name)}.css"),
            "ttf": {style: rel(f) for style, f in res.statics.items()},
            "woff2": {style: rel(out / "woff2" / (f.stem + ".woff2")) for style, f in res.statics.items()
                      if (out / "woff2" / (f.stem + ".woff2")).exists()},
            "variable": rel(res.variable) if res.variable else None,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"families": families}, indent=1, ensure_ascii=False) + "\n")
    return path


def _remove_stale(project: Project):
    """Delete the font folders of families that the project no longer has.

    Only folders that a build made (they hold a build record) are removed.
    """
    import shutil
    fonts = project.path / "fonts"
    keep = {slug(f.name) for f in project.families}
    if fonts.is_dir():
        for d in fonts.iterdir():
            if d.is_dir() and d.name not in keep and (d / RECORD).exists():
                shutil.rmtree(d)


# --------------------------------------------------------------------------
# Knowing when a build is up to date
# --------------------------------------------------------------------------

RECORD = ".build.json"
#: Files in a project that a build does not read: what it writes, and the notes for people.
_OUTPUTS = {"fonts", "proofs", "board.html", "feedback.json", "__pycache__", "BRIEF.md", "README.md"}
_engine_mark: str | None = None


def _hash_file(h, path: Path, label: str):
    h.update(label.encode())
    st = path.stat()
    if st.st_size > 2_000_000:
        h.update(f"{st.st_size}:{st.st_mtime_ns}".encode())     # large data: trust the size and the date
    else:
        h.update(path.read_bytes())


def _engine() -> str:
    """A mark for this copy of whateverfont: a build is out of date when the engine changes."""
    global _engine_mark
    if _engine_mark is None:
        import fontTools
        h = hashlib.sha256(f"{fontTools.version}:{sys.version_info[:2]}".encode())
        root = Path(__file__).resolve().parent
        for f in sorted(root.rglob("*.py")):
            _hash_file(h, f, str(f.relative_to(root)))
        _engine_mark = h.hexdigest()
    return _engine_mark


def fingerprint(project: Project, family: Family) -> str:
    """A hash of everything a family's build depends on."""
    h = hashlib.sha256(_engine().encode())
    h.update(f"{family.name}:{os.environ.get('SOURCE_DATE_EPOCH', '')}".encode())
    root = project.path
    for f in sorted(root.rglob("*")):
        rel = f.relative_to(root)
        if rel.parts[0] in _OUTPUTS or any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if f.is_file():
            _hash_file(h, f, str(rel))
    for f in project.sources:
        if f.exists():
            _hash_file(h, f, str(f))
    return h.hexdigest()


def _record(out: Path, mark: str, variable: bool, res: BuildResult):
    rel = lambda q: str(Path(q).relative_to(out))
    data = {"fingerprint": mark, "variable_wanted": variable, "files": [rel(f) for f in res.files],
            "statics": {k: rel(v) for k, v in res.statics.items()},
            "variable": rel(res.variable) if res.variable else None,
            "warnings": res.warnings, "notes": res.notes, "kerning_pairs": res.kerning_pairs}
    (out / RECORD).write_text(json.dumps(data, indent=1) + "\n")


def _recorded(out: Path, mark: str, variable: bool, family: Family) -> BuildResult | None:
    """The result of the last build, if it used the same inputs and its files are still there."""
    try:
        data = json.loads((out / RECORD).read_text())
    except (OSError, ValueError):
        return None
    if data.get("fingerprint") != mark or (variable and not data.get("variable_wanted")):
        return None
    files = [out / f for f in data["files"]]
    if not all(f.exists() for f in files) or not (out / f"{slug(family.name)}.css").exists():
        return None
    res = BuildResult(family.name, files, list(data["warnings"]),
                      {k: out / v for k, v in data["statics"].items()},
                      out / data["variable"] if data.get("variable") else None, data["kerning_pairs"],
                      list(data.get("notes", [])))
    if not variable:
        res.variable = None
    return res


def write_css(family: Family, result: BuildResult, out_dir: Path) -> Path:
    """A stylesheet with @font-face rules for the built files."""
    rules = []
    name = family.name
    if result.variable is not None:
        wght = next((a for a in family.axes if a.tag == "wght"), None)
        weight = f"\n  font-weight: {int(wght.minimum)} {int(wght.maximum)};" if wght else ""
        rules.append(f'@font-face {{\n  font-family: "{name}";\n  src: url("variable/{result.variable.stem}.woff2") '
                     f'format("woff2");{weight}\n  font-display: swap;\n}}')
    else:
        for style, path in result.statics.items():
            loc = family.styles.get(style, {})
            italic = "italic" if "slnt" in loc or "Italic" in style else "normal"
            rules.append(f'@font-face {{\n  font-family: "{name}";\n  src: url("woff2/{path.stem}.woff2") format("woff2");'
                         f'\n  font-weight: {int(loc.get("wght", 400))};\n  font-style: {italic};\n  font-display: swap;\n}}')
    css = out_dir / f"{slug(name)}.css"
    css.write_text("\n\n".join(rules) + "\n")
    return css
