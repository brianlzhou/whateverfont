"""Build every example project, its proofs, and the gallery image in docs/images.

Run from the repository root:  python scripts/build_examples.py [project ...]
With --gallery it draws only the gallery image again, from the fonts as they are.

Builds are reproducible: a project whose design did not change gives the same bytes again.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from whateverfont import board, project, proof

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"

#: Every example with a font.py, in the order of the README. Pebble is a remix and has no font.py, and
#: retrace (built last, by build_retrace) redraws other fonts.
PROJECTS = ["arroyo", "caliper", "tally", "platen", "pinout", "greenbar", "lastbell", "wassail", "aviary", "hopstep", "neon",
            "crate", "effects", "starry", "haystack", "gilt", "cutout", "kanagawa", "cabochon", "ombrelle", "panework", "lacentine", "drippelgang", "leafpile",
            "dayshift", "setsquare", "softboil", "knollrise", "teacloth", "tinsheen", "etchant", "scanstep", "lowslung", "doorstep", "hedmast"]


def build(name: str) -> dict:
    proj = project.load(EXAMPLES / name)
    results = project.build(proj)
    for fam_name, res in results.items():
        for w in res.warnings:
            print(f"  warning ({fam_name}): {w}")
    board.build_board(proj, results)
    proofs = proj.proofs_dir()
    for old in proofs.glob("*.png") if proofs.exists() else []:
        old.unlink()
    for fam in proj.families:
        res = results[fam.name]
        first = next(iter(res.statics.values()))
        stem = fam.name.replace(" ", "")
        proof.sheet(first, proofs / f"{stem}-sheet.png", title=f"{fam.name} {next(iter(fam.styles))}", sample=fam.sample)
        if len(res.statics) > 1:
            rows = [(path, {}, f"{fam.name} {style}") for style, path in res.statics.items()]
            proof.compare(rows, proofs / f"{stem}-styles.png", fam.sample or proof.PANGRAM, 64)
    return results


def build_retrace():
    """examples/retrace: families redrawn over the centerlines of Arabic and Devanagari fonts.

    It needs the trace extra (numpy). Without it, the step is skipped and the fonts stay as they are."""
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("  skipped: examples/retrace needs numpy (pip install 'whateverfont[trace]')")
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("retrace_build", EXAMPLES / "retrace" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main([])


def gallery(rows: list, out: Path, px: float = 78):
    """One image with a row per font: (font path, variations, label, text, palette, paper, size), the last three optional."""
    tiles = []
    for i, (path, variations, label, text, *more) in enumerate(rows):
        palette = more[0] if more else None
        paper = more[1] if len(more) > 1 and more[1] else proof.PAPER
        size = more[2] if len(more) > 2 else px
        tmp = out.parent / f"_row{i}.png"
        proof.compare([(path, variations, label)], tmp, text, size, width=1400, palette=palette, paper=paper, bands=False)
        tiles.append(Image.open(tmp).copy())
        tmp.unlink()
    w = max(t.width for t in tiles)
    sheet = Image.new("RGB", (w, sum(t.height for t in tiles)), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(out, optimize=True)
    print(f"gallery: {out}")


def main(argv=None) -> int:
    names = (argv if argv is not None else sys.argv[1:]) or PROJECTS + ["retrace"]
    if names == ["--gallery"]:
        names = []                      # only the gallery image, from the fonts as they are
    for name in names:
        print(f"building {name}")
        build_retrace() if name == "retrace" else build(name)
    e = EXAMPLES
    f = lambda project_, family, style="Regular": e / f"{project_}/fonts/{family}/ttf/{family}-{style}.ttf"
    arroyo = e / "arroyo/fonts/Arroyo/variable/Arroyo[wght,FLAR,slnt].ttf"
    caliper = e / "caliper/fonts/Caliper/variable/Caliper[wght,wdth,FLAR,slnt].ttf"
    gantry = e / "caliper/fonts/Gantry/variable/Gantry[wght,ROND,wdth].ttf"
    tally = e / "tally/fonts/TallyMono/variable/TallyMono[wght,slnt].ttf"
    platen = e / "platen/fonts/Platen/variable/Platen[wght].ttf"
    pinout = e / "pinout/fonts/Pinout/variable/Pinout[wght].ttf"
    rows = [
        (f("starry", "StarryInitials"), {}, "Starry Initials: \"a font like Starry Night\"", "The Night Is Full Of Stars"),
        (arroyo, {}, "Arroyo: \"a calm serif for a long essay\"", "A quiet serif for long arguments"),
        (arroyo, {"wght": 700, "slnt": -11}, "Arroyo at wght 700, slnt -11: the same file", "The same file, bold and slanted"),
        (caliper, {"wght": 600, "wdth": 60}, "Caliper: \"tall and condensed, for headlines\"", "Compressed for the tallest headline"),
        (f("lastbell", "LastBellSnow"), {}, "Last Bell Snow: \"the feeling of winter break in middle school\", then \"now put snow on it\"",
         "No school till January", "Mitten", "#12372A"),
        (f("gilt", "Gilt"), {}, "Gilt, palette Gold on Dark: \"like Klimt's The Kiss\"", "Anna & Felix", "Gold on Dark", "#0E0B07"),
        (f("kanagawa", "Kanagawa"), {}, "Kanagawa: \"like Hokusai's Great Wave\"", "THE GREAT WAVE", None, "#EFE4C8"),
        (f("cutout", "CutoutColor"), {}, "Cutout Color: \"like Matisse's paper cut-outs\"", "Children's Museum"),
        (f("haystack", "HaystackInitials"), {}, "Haystack Initials, palette Sunset: \"like Monet's haystacks\"", "Late Afternoon", "Sunset"),
        (f("aviary", "AviaryColor"), {}, "Aviary Color: \"make me a font of birds\"", "FLOCKBIRDS", None, "#F3ECDC", 124),
        (f("hopstep", "Hopstep"), {}, "Hopstep: \"make every letter a person who dances\"", "DANCE PARTY", None, "#FBF7EC", 118),
        (platen, {}, "Platen: \"a typewriter, like a 1960s portable\"", "The quarterly figures are attached."),
        (pinout, {}, "Pinout: \"a monospace like an old datasheet\"", "PIN 14  VCC +5V  [0x3F] -> {CLK, /RESET}"),
        (f("greenbar", "Greenbar"), {}, "Greenbar: \"a dot-matrix printer from 1985\"", "INVOICE 004417   TOTAL DUE $44.55"),
        (tally, {}, "Tally Mono: \"a monospaced font for my terminal\"", "for i in range(10): total += x[i]  # il1I O0o"),
        (gantry, {"ROND": 100, "wght": 600}, "Gantry at ROND 100: \"labels on a machine\", fully rounded", "Torque 4.2 N·m at 310 rpm"),
        (f("wassail", "WassailInitials"), {}, "Wassail Initials: \"illuminated Christmas capitals\"", "Hark the Herald Angels Sing"),
        (f("neon", "NeonGlow"), {}, "Neon Glow: \"a neon sign for a bar\"", "Open Late", "Pink", "#0B0A12"),
        (f("crate", "CrateStencil", "Bold"), {}, "Crate Stencil: \"a stencil for shipping crates\"", "FRAGILE THIS SIDE UP"),
        (f("cabochon", "Cabochon"), {}, "Cabochon: \"a font that looks cut from polished jade\"", "Jade & Ruby", "Jade", "#7A1418"),
        (f("ombrelle", "OmbrelleInitials"), {}, "Ombrelle Initials: \"like Seurat's Sunday on La Grande Jatte\"", "A Sunday On The Island",
         "Afternoon", "#F3EBD5"),
        (f("panework", "Panework"), {}, "Panework: \"like Mondrian's grid paintings\"", "Composition in Red", "Primary", "#F3F1EC"),
        (f("lacentine", "Lacentine"), {}, "Lacentine: \"a valentine glued on a paper doily\"", "Be Mine, Valentine", "Valentine", "#F4BFCB"),
        (f("drippelgang", "Drippelgang"), {}, "Drippelgang: \"a Halloween party, dipped in slime\"", "Trick or Treat!", "Slime", "#1C0E2B"),
        (f("leafpile", "Leafpile"), {}, "Leafpile: \"a pile of fall leaves\"", "Harvest Fair", "Maple", "#F4E9D4"),
    ]
    pebble = e / "pebble/fonts/PebbleSans-Regular.ttf"
    if pebble.exists():
        rows.append((pebble, {}, "Pebble Sans: a remix of Inter, rounded in one command", "Rounded in one command"))
    rows = [r for r in rows if Path(r[0]).exists()]
    gallery(rows, ROOT / "docs/images/gallery.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
