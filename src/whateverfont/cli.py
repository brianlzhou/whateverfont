"""The ``whateverfont`` command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def _location(text: str | None) -> dict:
    """Parse ``wght=700,slnt=-10`` into a dict."""
    out = {}
    for part in (text or "").split(","):
        if part.strip():
            tag, _, value = part.partition("=")
            out[tag.strip()] = float(value)
    return out


def _family(project, name: str | None):
    if not name:
        return project.family
    for fam in project.families:
        if fam.name.lower() == name.lower():
            return fam
    raise SystemExit(f"no family named {name!r}; this project has: {', '.join(f.name for f in project.families)}")


def _report(results: dict, reused: set = frozenset()) -> int:
    code = 0
    for name, res in results.items():
        print(f"{name}: {len(res.statics)} static styles"
              + (", 1 variable font" if res.variable else "")
              + f", {res.kerning_pairs} kerning pairs"
              + (" (up to date, not built again)" if name in reused else ""))
        for f in res.files:
            print(f"  {f}")
        for w in res.warnings:
            print(f"  warning: {w}")
        for n in res.notes:
            print(f"  note: {n}")
    return code


def cmd_new(args) -> int:
    from . import project
    path = project.create(args.path, args.name or Path(args.path).name.replace("-", " ").title(), args.preset,
                          args.brief or "", args.sample or "")
    print(f"Created {path / 'font.py'} and {path / 'BRIEF.md'}")
    print(f"Next: edit font.py, then run `whateverfont build {path}` and `whateverfont look {path}`.")
    return 0


def cmd_presets(args) -> int:
    from . import presets
    print(presets.describe())
    return 0


def cmd_build(args) -> int:
    from . import board, project
    proj = project.load(args.path)
    reused = set()
    results = project.build(proj, variable=not args.no_variable, only=args.family, force=args.force,
                            on_build=lambda fam, was: reused.add(fam.name) if was else None)
    code = _report(results, reused)
    if not args.no_board:
        print(f"board: {board.build_board(proj, results)}")
    return code


def _said(proj):
    """A callback for project.build that reports each family it had to build again."""
    def on_build(fam, reused):
        if not reused:
            print(f"built: {proj.out_dir(fam)}")
    return on_build


def cmd_look(args) -> int:
    from . import project, proof
    from .family import style_location
    proj = project.load(args.path)
    fam = _family(proj, args.family)
    out = Path(args.out) if args.out else proj.proofs_dir()
    out.mkdir(parents=True, exist_ok=True)
    stem = fam.name.replace(" ", "")
    look = {"palette": args.palette, "paper": args.bg or proof.PAPER}
    # a ground that the person chose stays as it is: chalk figures on a black board keep their black bodies
    bands = {"bands": not args.bg}
    if args.palette and not args.directions:
        names = list(fam.palettes)
        if args.palette.lower() not in [n.lower() for n in names]:
            raise ValueError(f"no palette named {args.palette!r}; {fam.name} has: {', '.join(names) or 'no palettes'}")
    if args.directions:
        # every family of the project in one picture, to check that they differ
        results = project.build(proj, variable=False, force=False, on_build=_said(proj))
        for f in proj.families:
            for w in results[f.name].warnings:
                print(f"warning ({f.name}): {w}")
        rows = [(next(iter(results[f.name].statics.values())), {},
                 _short(f"{f.name}: {f.description}" if f.description else f.name)) for f in proj.families]
        # each family in its own sample, unless one text is asked for
        texts = [args.text or f.sample or proj.family.sample or proof.PANGRAM for f in proj.families]
        print("proof:", proof.compare(rows, out / f"{args.name or 'directions'}.png", texts, args.size,
                                      per_row_text=True, **look, **bands))
        return 0
    if args.xray:
        loc = style_location(fam, args.style) if args.style else fam.default_location()
        loc.update(_location(args.at))
        print("proof:", proof.xray(fam, args.xray, out / f"{stem}-xray.png", loc))
        return 0
    results = project.build(proj, variable=True, only=fam.name, force=False, on_build=_said(proj))
    res = results[fam.name]
    for w in res.warnings:
        print(f"warning: {w}")
    style = args.style or next(iter(fam.styles))
    if args.at and res.variable is None:
        raise SystemExit("--at needs a variable font, and this family has no axes")
    if args.at:
        font, variations, label = res.variable, _location(args.at), args.at
    else:
        font, variations, label = res.statics[style], {}, style
    if not args.bg and fam.palettes:
        # a palette with a color that the paper would hide (white snow on white) gets a contrasting ground
        look["paper"] = proof.ground_for(proof.Renderer(font, variations, args.palette).colors, look["paper"])
        if look["paper"] != proof.PAPER:
            print(f"note: a color of this palette does not show on white, so the proof has a ground of "
                  f"{look['paper']}. Choose another with --bg.")
    if args.styles:
        rows = [(res.statics[s], {}, s) for s in fam.styles]
        print("proof:", proof.compare(rows, out / f"{stem}-styles.png", args.text or fam.sample or proof.PANGRAM,
                                    args.size, **look, **bands))
    elif args.text:
        # "\n" (typed as two characters, or a real line break) starts a new line
        rows = [t for t in args.text.replace("\\n", "\n").split("\n")]
        name = args.name or f"{stem}-text"
        print("proof:", proof.lines(font, out / f"{name}.png", rows, args.size, variations,
                                    labels=[f"{fam.name} {label}"] + [""] * (len(rows) - 1), **look, **bands))
    else:
        print("proof:", proof.sheet(font, out / f"{stem}-{label.replace(' ', '').replace('=', '').replace(',', '-')}-sheet.png",
                                    variations, f"{fam.name} {label}", fam.sample, **look))
    return 0


def _short(text: str, limit: int = 150) -> str:
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def cmd_probe(args) -> int:
    from . import probe, project
    proj = project.load(args.path)
    fam = _family(proj, args.family)
    report = probe.probe(fam, _location(args.at), args.glyphs)
    if args.problems:
        for line in report["problems"] or ["no problems found"]:
            print(line)
        if report.get("skipped"):
            print(f"note: {report['skipped']}")
        return 1 if report["problems"] and args.strict else 0
    if not args.full:
        report.pop("glyphs")          # the per-glyph table is long; ask for it with --full
    print(json.dumps(report, indent=2))
    return 1 if report["problems"] and args.strict else 0


def cmd_board(args) -> int:
    from . import board, project
    proj = project.load(args.path)
    reused = set()
    results = project.build(proj, variable=True, force=False,
                            on_build=lambda fam, was: reused.add(fam.name) if was else None)
    _report(results, reused)
    if args.serve:
        board.serve(proj, results, args.port)
    else:
        print(f"board: {board.build_board(proj, results)}")
        print("Open it in a browser. Use --serve to receive feedback as feedback.json.")
    return 0


def cmd_remix(args) -> int:
    from . import remix
    from fontTools.ttLib import TTFont
    is_open, notice = remix.declared_license(TTFont(args.font, lazy=True))
    if not is_open:
        shown = f" Its notice says: {notice.strip()[:160]!r}." if notice else ""
        print(f"whateverfont: note: this font declares no open license.{shown} Check its terms before you share "
              "the remix.", file=sys.stderr)
    out = remix.remix_file(args.font, args.out, name=args.name, round_=args.round, embolden=args.embolden,
                           slant=args.slant, width=args.width, at=_location(args.at), subset=args.latin)
    print(out)
    return 0


def cmd_retrace(args) -> int:
    from fontTools.ttLib import TTFont
    from . import remix, trace
    font = TTFont(args.font, lazy=True)
    is_open, notice = remix.declared_license(font)
    if not is_open:
        shown = f" Its notice says: {notice.strip()[:160]!r}." if notice else ""
        print(f"whateverfont: note: this font declares no open license.{shown} Check its terms before you share "
              "the redrawn font.", file=sys.stderr)
    trace.check_name(font, args.name)
    family = trace.load_family(args.pen)
    effect, label = trace.load_effect(args.effect) if args.effect else (None, "")
    palettes = trace.load_family(args.palettes).palettes if args.palettes else None
    only = None
    if args.only:
        from . import charsets
        only = charsets.resolve(args.only)
        have = set(font.getBestCmap() or {})
        print(f"keeping {len(only & have)} of the {len(only)} characters asked for (the source has "
              f"{len(have)})")
    try:
        traced = trace.trace_font(args.font, headline={"auto": None, "on": True, "off": False}[args.headline],
                                  at=_location(args.at), jobs=args.jobs, only=only, corners=args.corners)
    except trace.MissingDependency as exc:
        print(f"whateverfont: {exc}", file=sys.stderr)
        return 2
    line = f", joins at y={traced.line:.0f}" if traced.line is not None else ""
    kind = f", {traced.corners} corners" if traced.cjk else ""
    print(f"traced {len(traced.glyphs)} glyphs in {traced.seconds:.0f}s ({len(traced.composites)} composites kept"
          f"{line}{', with a headline' if traced.headline else ''}{kind})")
    for w in traced.warnings:
        print(f"  warning: {w}")
    res = trace.redraw(traced, args.out, args.name, family, effect, palettes, check_glyphs=not args.no_check,
                       jobs=args.jobs, effect_label=label)
    for f in (res.ttf, res.woff2, res.css):
        print(f"  {f}")
    chars = {}
    for cp, n in sorted((traced.font.getBestCmap() or {}).items()):
        chars.setdefault(n, chr(cp))
    shown = lambda n: f"{n!r} ({chars[n]})" if n in chars and chars[n].isprintable() else repr(n)
    for n, e in res.failed.items():
        print(f"  warning: glyph {shown(n)} was left empty: {e}")
    for n, e in res.plain.items():
        print(f"  warning: glyph {shown(n)}: the effect failed ({e}); it has the letter's color only")
    for n, problems in res.flagged.items():
        print(f"  warning: glyph {shown(n)}: {'; '.join(problems)}")
    if not args.no_check:
        print(f"self-check: {len(res.flagged)} of {res.traced} traced glyphs flagged")
    for n in res.notes:
        print(f"  note: {n}")
    print(f"drawn in {res.seconds:.0f}s. The letter shapes are {traced.font['name'].getBestFamilyName()}'s: the "
          "result keeps its license and copyright notice.")
    return 0


def cmd_skill(args) -> int:
    from . import resources
    if args.action == "show":
        print(resources.skill_file().read_text(), end="")
        return 0
    if args.action == "path":
        print(resources.skill_file())
        return 0
    if args.dest:
        dest = Path(args.dest)
    elif args.project:
        dest = Path(".claude") / "skills"
    else:
        dest = Path.home() / ".claude" / "skills"
    print(f"skill: {resources.install_skill(dest)}")
    print('Start a new agent session, then ask: "Use whateverfont. Make me a font that ..."')
    return 0


def cmd_docs(args) -> int:
    from . import resources
    if args.path:
        print(resources.docs_dir())
    elif args.page:
        print(resources.page(args.page).read_text(), end="")
    else:
        width = max(len(n) for n in resources.PAGES)
        for name, what in resources.PAGES.items():
            print(f"{name.ljust(width)}  {what}")
        print("\nRun `whateverfont docs NAME` to read one. `whateverfont docs --path` prints the folder.")
    return 0


def cmd_examples(args) -> int:
    from . import resources
    if args.name:
        folder = resources.examples_dir() / args.name
        if not (folder / "font.py").is_file():
            raise ValueError(f"no example named {args.name!r}; run `whateverfont examples` for the list")
        print(folder)
        return 0
    rows = resources.examples()
    width = max((len(n) for n, _ in rows), default=0)
    for name, what in rows:
        print(f"{name.ljust(width)}  {what}")
    print(f"\nSources: {resources.examples_dir()}\nRun `whateverfont examples NAME` for the folder of one. "
          "Copy it to change it.")
    return 0


def cmd_library(args) -> int:
    from . import library
    repo = library.find_repo(args.repo or ".")
    if args.action == "add":
        if not args.path or not args.github:
            raise ValueError("usage: whateverfont library add DIR --github YOUR_USERNAME")
        target = library.add(args.path, repo, args.github, prompt=args.prompt, agent=args.agent, name=args.name,
                             update=args.update)
        found = library.problems(target, repo, author=args.github, sources_only=True)
        rel = target.relative_to(repo)
        print(f"entry: {target}")
        if found:
            for line in found:
                print(f"  problem: {line}")
            print("Fix these in your project, then run the command again with --update.")
            return 1
        branch = f"library-{target.name}"
        print("It builds and passes the checks. To open the pull request:")
        print(f"  cd {repo}")
        print(f"  git checkout -b {branch} && git add {rel} && git commit -m \"Add {target.name} to the library\"")
        print(f"  git push -u origin {branch} && gh pr create --fill")
        return 0
    if args.action == "changed":
        print("\n".join(library.changed(repo, args.since or "origin/main")))
        return 0
    if args.action == "check":
        if args.since:
            args.only = library.changed(repo, args.since)
            if not args.only:
                print(f"no entry differs from {args.since}")
                return 0
        found = library.check(repo, only=args.only, author=args.author, sources_only=args.sources_only)
        bad = 0
        for name, lines in found.items():
            print(f"{name}: " + ("ok" if not lines else f"{len(lines)} problem(s)"))
            for line in lines:
                print(f"  {line}")
            bad += bool(lines)
        if not found:
            print("the library has no entries yet")
        return 1 if bad else 0
    done = library.build(repo, only=args.only)
    for name, results in done.items():
        for fam, res in results.items():
            print(f"{name}: {fam}, {len(res.statics)} static styles" + (", 1 variable font" if res.variable else ""))
            for w in res.warnings:
                print(f"  warning: {w}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="whateverfont", description="WhateverFont You Want. Design a typeface from a brief, in code.",
        epilog="If you are an agent, run `whateverfont skill show` first and follow it.")
    ap.add_argument("--version", action="version", version=f"whateverfont {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="start a font project")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--preset", default="humanist")
    p.add_argument("--brief", help="the brief, in the user's words")
    p.add_argument("--sample", help="text the font is meant for")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("presets", help="list starting points")
    p.set_defaults(fn=cmd_presets)

    p = sub.add_parser("build", help="build font files and the review board")
    p.add_argument("path")
    p.add_argument("--family", help="build only this family")
    p.add_argument("--no-variable", action="store_true")
    p.add_argument("--no-board", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="build again even if nothing changed (use it when font.py reads a file whateverfont cannot see)")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("look", help="render a proof image and print its path")
    p.add_argument("path")
    p.add_argument("--family")
    p.add_argument("--style", help="a named style (default: the first)")
    p.add_argument("--at", help="a variable-font location, for example wght=650,slnt=-8")
    p.add_argument("--text", help="render this text instead of the full sheet; \\n starts a new line")
    p.add_argument("--name", help="file name for a --text or --directions proof, without .png")
    p.add_argument("--styles", action="store_true", help="one row per named style")
    p.add_argument("--xray", metavar="CHARS", help="large glyphs with their skeletons")
    p.add_argument("--directions", action="store_true", help="one row per family of the project")
    p.add_argument("--palette", help="for a color font: the palette to show, by name (default: the first)")
    p.add_argument("--bg", metavar="#RRGGBB", help="background color of the proof (default: white)")
    p.add_argument("--size", type=float, default=96)
    p.add_argument("--out", help="folder for the image (default: PROJECT/proofs)")
    p.set_defaults(fn=cmd_look)

    p = sub.add_parser("probe", help="measure the design and report problems as JSON")
    p.add_argument("path")
    p.add_argument("--family")
    p.add_argument("--at")
    p.add_argument("--glyphs", help="limit to these characters")
    p.add_argument("--full", action="store_true", help="include the table of every glyph")
    p.add_argument("--problems", action="store_true", help="print only the problems, one on each line")
    p.add_argument("--strict", action="store_true", help="exit 1 if there are problems")
    p.set_defaults(fn=cmd_probe)

    p = sub.add_parser("board", help="build the review board")
    p.add_argument("path")
    p.add_argument("--serve", action="store_true", help="serve it and save feedback to feedback.json")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(fn=cmd_board)

    p = sub.add_parser("remix", help="restyle an existing font")
    p.add_argument("font", help="a .ttf file (static or variable)")
    p.add_argument("--out", required=True)
    p.add_argument("--name", required=True, help="the new family name (must differ from the original)")
    p.add_argument("--round", type=float, default=0.0, help="corner radius in font units per 1000")
    p.add_argument("--embolden", type=float, default=0.0, help="extra stroke weight in units per 1000")
    p.add_argument("--slant", type=float, default=0.0, help="degrees")
    p.add_argument("--width", type=float, default=1.0, help="horizontal scale")
    p.add_argument("--at", help="instance of a variable source, for example wght=500")
    p.add_argument("--latin", action="store_true",
                   help="keep only Latin letters and the basic features, for a small file (default: keep everything)")
    p.set_defaults(fn=cmd_remix)

    p = sub.add_parser("retrace", help="redraw an existing font (Arabic, Devanagari, Japanese ...) with a family's pen")
    p.add_argument("font", help="a .ttf file (static or variable) under an open license")
    p.add_argument("--name", required=True, help="the new family name (not the source's, and none it reserves)")
    p.add_argument("--pen", required=True, metavar="PROJECT[:FAMILY]",
                   help="the family whose pen draws the letters, at its default style")
    p.add_argument("--effect", metavar="NAME[:k=v] | FILE.py:FUNCTION[:k=v]",
                   help="an effect from whateverfont.effects (glow:size=80) or a project's own (snow.py:capped)")
    p.add_argument("--palettes", metavar="PROJECT[:FAMILY]",
                   help="for a color effect: the family whose palettes to use (default: the pen's family)")
    p.add_argument("--out", required=True, help="the folder for ttf/, woff2/ and the CSS file")
    p.add_argument("--headline", choices=["auto", "on", "off"], default="auto",
                   help="trace a line the letters hang from (Devanagari) as one straight stroke")
    p.add_argument("--at", help="instance of a variable source, for example wght=500")
    p.add_argument("--only", action="append", metavar="SET|FILE",
                   help="keep only these characters: a named set (japanese, chinese, traditional, korean) or a "
                        "UTF-8 text file "
                        "of characters. Give it more than once, or separate with commas, to add sets together")
    p.add_argument("--corners", choices=["auto", "sharp", "soft"], default="auto",
                   help="rebuild corners sharp (type) or keep them round (handwriting); auto decides from the "
                        "source for Japanese, Chinese and Korean, and is sharp for other scripts")
    p.add_argument("--no-check", action="store_true", help="skip the comparison of each glyph with its source")
    p.add_argument("--jobs", type=int, help="worker processes (default: WHATEVERFONT_JOBS or the processor count)")
    p.set_defaults(fn=cmd_retrace)

    p = sub.add_parser("skill", help="install or print the instructions for an agent")
    p.add_argument("action", choices=["install", "show", "path"])
    p.add_argument("--project", action="store_true", help="install into ./.claude/skills, for this project only")
    p.add_argument("--dest", help="install into this skills folder (default: ~/.claude/skills)")
    p.set_defaults(fn=cmd_skill)

    p = sub.add_parser("docs", help="list or print the reference pages")
    p.add_argument("page", nargs="?", help="workflow, parameters, recipes, effects, scripts or roadmap")
    p.add_argument("--path", action="store_true", help="print the folder that holds the pages")
    p.set_defaults(fn=cmd_docs)

    p = sub.add_parser("examples", help="list the example projects and where their sources are")
    p.add_argument("name", nargs="?")
    p.set_defaults(fn=cmd_examples)

    p = sub.add_parser("library", help="add a font to the public library, or check and build its entries")
    p.add_argument("action", choices=["add", "check", "build", "changed"])
    p.add_argument("path", nargs="?", help="add: the project to share")
    p.add_argument("--github", help="add: your GitHub username, for the credit")
    p.add_argument("--prompt", help="add: the request that made the font (default: the brief)")
    p.add_argument("--agent", help='add: what drew it, for example "Claude Code"')
    p.add_argument("--name", help="add: the folder name in the library (default: from the family name)")
    p.add_argument("--update", action="store_true", help="add: replace your own entry")
    p.add_argument("--repo", help="a checkout of the whateverfont repository (default: the current folder)")
    p.add_argument("--only", nargs="*", help="check, build: only these entries")
    p.add_argument("--since", metavar="REV", help="check, changed: only the entries that differ from this git revision")
    p.add_argument("--author", help="check: the account that opened the pull request")
    p.add_argument("--sources-only", action="store_true", help="check: fail if an entry holds built fonts")
    p.set_defaults(fn=cmd_library)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (FileNotFoundError, FileExistsError, ValueError, KeyError) as exc:
        print(f"whateverfont: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
