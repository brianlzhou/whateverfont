"""Builds: the same result in one process or many, the same bytes twice, and no build when nothing changed."""

import hashlib

from fontTools.ttLib import TTFont

from whateverfont import Axis, Family, Params, build_family
from whateverfont import cli, project
from whateverfont.compile import default_jobs
from whateverfont.project import _summary


def family():
    return Family(
        name="Jobs Test",
        base=Params(flare=0.2, contrast=0.7),
        axes=[Axis("wght", "Weight", 300, 400, 800, {300: {"weight": 50}, 800: {"weight": 150}})],
        styles={"Regular": {}, "Bold": {"wght": 700}},
    )


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_parallel_build_gives_the_same_files_as_a_build_in_one_process(tmp_path):
    one = build_family(family(), tmp_path / "one", jobs=1)
    many = build_family(family(), tmp_path / "many", jobs=4)
    assert one.warnings == many.warnings == []
    assert list(one.statics) == list(many.statics) == ["Regular", "Bold"]
    assert [f.name for f in one.files] == [f.name for f in many.files]
    for a, b in zip(one.files, many.files):
        assert _digest(a) == _digest(b), a.name
    assert one.kerning_pairs == many.kerning_pairs > 0


def test_building_twice_gives_the_same_bytes(tmp_path):
    a = build_family(family(), tmp_path / "a", styles=["Regular"], variable=False)
    b = build_family(family(), tmp_path / "b", styles=["Regular"], variable=False)
    assert _digest(a.statics["Regular"]) == _digest(b.statics["Regular"])
    assert TTFont(a.statics["Regular"])["head"].created == TTFont(b.statics["Regular"])["head"].created


def test_jobs_setting_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("WHATEVERFONT_JOBS", "3")
    assert default_jobs() == 3
    monkeypatch.setenv("WHATEVERFONT_JOBS", "many")
    assert 1 <= default_jobs() <= 8


def test_a_project_is_built_again_only_when_it_changes(tmp_path, capsys):
    path = tmp_path / "cached"
    assert cli.main(["new", str(path), "--preset", "grotesk", "--brief", "A plain sans."]) == 0
    assert cli.main(["build", str(path), "--no-board"]) == 0
    assert "up to date" not in capsys.readouterr().out
    font = path / "fonts" / "Cached" / "ttf" / "Cached-Regular.ttf"
    first = font.stat().st_mtime_ns

    # look and board reuse a build that is up to date
    assert cli.main(["look", str(path), "--text", "Hello"]) == 0
    assert "built:" not in capsys.readouterr().out
    assert font.stat().st_mtime_ns == first

    proj = project.load(path)
    seen = []
    project.build(proj, force=False, on_build=lambda fam, reused: seen.append(reused))
    assert seen == [True]

    # a change to the design is a new build, and look says that it built
    source = path / "font.py"
    source.write_text(source.read_text().replace('preset("grotesk")', 'preset("grotesk", weight=120)'))
    assert cli.main(["look", str(path), "--text", "Hello"]) == 0
    assert "built:" in capsys.readouterr().out
    assert font.stat().st_mtime_ns != first

    # a missing file is a new build too
    font.unlink()
    seen.clear()
    project.build(project.load(path), force=False, on_build=lambda fam, reused: seen.append(reused))
    assert seen == [False] and font.exists()


def test_build_always_builds_when_forced(tmp_path, capsys):
    path = tmp_path / "forced"
    cli.main(["new", str(path), "--preset", "grotesk"])
    cli.main(["build", str(path), "--no-board", "--no-variable"])
    capsys.readouterr()
    assert cli.main(["build", str(path), "--no-board", "--no-variable"]) == 0
    assert "up to date" in capsys.readouterr().out
    assert cli.main(["build", str(path), "--no-board", "--no-variable", "--force"]) == 0
    assert "up to date" not in capsys.readouterr().out


def test_the_summary_of_a_brief_ends_at_a_sentence_or_a_word():
    assert _summary("A soft sans. For children's books.") == "A soft sans."
    long = ("A calm serif for a long essay about rivers, with no default web serifs anywhere near it, and several "
            "more words that take it well past the limit")
    short = _summary(long)
    assert short.endswith("…") and len(short) <= 111 and long.startswith(short[:-1])
    assert not short[:-1].endswith(" ")
    assert _summary("") == "A custom typeface."
    assert '"' not in _summary('Call it "Quill"')


def test_font_py_may_import_a_file_next_to_it_and_two_projects_may_share_a_name(tmp_path):
    for i, weight in enumerate((70, 130)):
        path = tmp_path / f"p{i}"
        path.mkdir()
        (path / "helper.py").write_text(f"WEIGHT = {weight}\n")
        (path / "font.py").write_text(
            "from whateverfont import Family, Params\nimport helper\n"
            "FAMILY = Family(name='Sibling', base=Params(weight=helper.WEIGHT))\n")
    first, second = project.load(tmp_path / "p0"), project.load(tmp_path / "p1")
    assert (first.family.base.weight, second.family.base.weight) == (70, 130)
    import sys
    assert "helper" not in sys.modules and str((tmp_path / "p1").resolve()) not in sys.path


def test_the_brief_is_not_an_input_and_removed_families_lose_their_folders(tmp_path):
    path = tmp_path / "tidy"
    cli.main(["new", str(path), "--preset", "grotesk"])
    source = path / "font.py"
    source.write_text(source.read_text() + "\nEXTRA = Family(name='Extra', base=preset('rounded'))\nDIRECTIONS = [FAMILY, EXTRA]\n")
    cli.main(["build", str(path), "--no-board", "--no-variable"])
    assert (path / "fonts" / "Extra").is_dir()
    # editing the brief does not make the fonts stale
    (path / "BRIEF.md").write_text("# Tidy\n\nA new thought.\n")
    seen = []
    project.build(project.load(path), variable=False, force=False, on_build=lambda fam, reused: seen.append(reused))
    assert seen == [True, True]
    # a family that is gone takes its folder with it; a folder the build did not make stays
    (path / "fonts" / "Mine").mkdir()
    source.write_text(source.read_text().replace("DIRECTIONS = [FAMILY, EXTRA]", "DIRECTIONS = [FAMILY]"))
    cli.main(["build", str(path), "--no-board", "--no-variable"])
    assert not (path / "fonts" / "Extra").exists() and (path / "fonts" / "Mine").is_dir()


def test_look_takes_several_lines_a_name_a_palette_and_a_background(tmp_path, capsys):
    from PIL import Image
    path = tmp_path / "glow"
    path.mkdir()
    (path / "font.py").write_text(
        "from whateverfont import Family, effects, latin\n"
        "FAMILY = Family(name='Lit', recipes=effects.glow(latin().only('Open')),\n"
        "                palettes={'Pink': effects.glow_palette('#FF2E9A'), 'Blue': effects.glow_palette('#22A6FF')})\n")
    assert cli.main(["look", str(path), "--text", "Open\\nOp", "--name", "night", "--palette", "Blue", "--bg", "#0B0A12"]) == 0
    out = path / "proofs" / "night.png"
    assert f"proof: {out}" in capsys.readouterr().out
    im = Image.open(out).convert("RGB")
    assert im.getpixel((3, 3)) == (11, 10, 18)                       # the background that was asked for
    pixels = [im.getpixel((x, y)) for y in range(0, im.height, 2) for x in range(0, im.width, 2)]
    blue = sum(1 for r, g, b in pixels if b > 200 and r < 120)
    pink = sum(1 for r, g, b in pixels if r > 200 and b < 180 and g < 120)
    assert blue > 120 and pink == 0                                  # the Blue palette, not the first one
    assert im.height > 300                                           # two lines
    assert cli.main(["look", str(path), "--text", "Open", "--palette", "Green"]) == 2
    assert "no palette named 'Green'" in capsys.readouterr().err


def test_skill_docs_and_examples_ship_with_the_package(tmp_path, capsys):
    from whateverfont import resources
    from whateverfont.cli import main

    assert resources.skill_file().is_file()
    for name in resources.PAGES:
        assert resources.page(name).is_file()
    assert {"arroyo", "tally"} <= {name for name, _ in resources.examples()}

    assert main(["skill", "install", "--dest", str(tmp_path / "skills")]) == 0
    installed = tmp_path / "skills" / "whateverfont" / "SKILL.md"
    assert installed.read_text() == resources.skill_file().read_text()
    assert main(["skill", "install", "--dest", str(tmp_path / "skills")]) == 0   # again: replaces the file

    # an older setup linked the folder into a checkout: the link goes, and the checkout stays as it was
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "whateverfont").symlink_to(resources.skill_file().parent, target_is_directory=True)
    assert main(["skill", "install", "--dest", str(linked)]) == 0
    assert not (linked / "whateverfont").is_symlink() and (linked / "whateverfont" / "SKILL.md").is_file()
    assert resources.skill_file().is_file()

    capsys.readouterr()
    assert main(["docs", "parameters"]) == 0
    assert capsys.readouterr().out.startswith("# Parameters")
    assert main(["docs", "nothing"]) == 2
    assert main(["examples", "arroyo"]) == 0
    assert capsys.readouterr().out.strip().endswith("arroyo")


def test_a_new_recipe_can_start_from_a_stock_one():
    from whateverfont import latin
    from whateverfont.presets import preset

    stock = latin()
    recipes = latin()

    @recipes.add("r", "r")
    def r(g):
        stock["r"](g)

    p = preset("grotesk")
    assert recipes.draw("r", p).advance == stock.draw("r", p).advance


def test_look_directions_reports_a_failed_recipe(tmp_path, capsys):
    from whateverfont.cli import main

    (tmp_path / "font.py").write_text(
        "from whateverfont import Family, latin\n"
        "recipes = latin().only('nor')\n"
        "@recipes.add('r', 'r')\n"
        "def r(g):\n"
        "    raise RuntimeError('no arm')\n"
        "FAMILY = Family(name='Broken', recipes=recipes)\n"
        "DIRECTIONS = [FAMILY]\n")
    assert main(["look", str(tmp_path), "--directions"]) == 0
    assert "warning (Broken): glyph 'r' failed" in capsys.readouterr().out


def test_probe_does_not_count_stems_in_an_outlined_font():
    from whateverfont import Family, effects, latin
    from whateverfont.probe import probe

    report = probe(Family(name="Hollow", recipes=effects.outlined(latin().only("neoaB8"))))
    assert not [line for line in report["problems"] if "expected" in line]
    assert "an effect changes their outlines" in report["skipped"]


def test_probe_warns_about_very_heavy_stems():
    from whateverfont import Family, Params
    from whateverfont.probe import probe

    assert any("stems are up to" in line for line in probe(Family(name="Heavy", base=Params(weight=200)))["problems"])
    assert not any("stems are up to" in line for line in probe(Family(name="Fine", base=Params(weight=120)))["problems"])


def test_a_proof_gets_a_ground_that_shows_a_pale_palette():
    from whateverfont import proof

    assert proof.ground_for([(213, 64, 43), (255, 255, 255)]) == proof.DARK_GROUND     # white snow on white paper
    assert proof.ground_for([(213, 64, 43), (31, 107, 74)]) == proof.PAPER
    assert proof.ground_for([(20, 20, 24)], "#101216") == proof.LIGHT_GROUND
    # one pale color among many is bordered by the others, and needs no special ground
    assert proof.ground_for([(255, 255, 255), (30, 78, 126), (20, 40, 80), (120, 160, 200)]) == proof.PAPER


def test_the_index_names_a_ground_for_a_palette_that_white_would_hide():
    from whateverfont import Family, project

    fam = Family(name="Snowy", palettes={"Mitten": {"letter": "#D5402B", "snow": "#FFFFFF"},
                                         "Ink": {"letter": "#1B1A17", "snow": "#7A7468"}})
    assert set(project.grounds(fam)) == {"Mitten"}
