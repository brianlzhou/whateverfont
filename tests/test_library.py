"""The public library: adding an entry and the checks a pull request runs."""

import json

import pytest

from whateverfont import library
from whateverfont.cli import main

FONT = '''from whateverfont import Family, latin
from whateverfont.presets import preset

FAMILY = Family(name="{name}", base=preset("grotesk"), recipes=latin().only("nor"), copyright="Copyright 2026 Octo Cat"{more})
'''


def repo_with(tmp_path, example_name="Arroyo"):
    """A stand-in for a checkout: a library, and one example whose family name is taken."""
    repo = tmp_path / "repo"
    (repo / "library").mkdir(parents=True)
    (repo / "library" / "README.md").write_text("# The library\n")
    (repo / "pyproject.toml").write_text('[project]\nname = "whateverfont"\n')
    example = repo / "examples" / "arroyo"
    example.mkdir(parents=True)
    (example / "font.py").write_text(FONT.format(name=example_name, more=""))
    return repo


def project(tmp_path, name="Snow Day", more=""):
    folder = tmp_path / "work" / library.slug(name)
    folder.mkdir(parents=True)
    (folder / "font.py").write_text(FONT.format(name=name, more=more))
    (folder / "BRIEF.md").write_text(f"# {name}\n\n## Brief\n\nA font that feels like a snow day.\n\n## Decisions\n")
    return folder


def test_add_copies_the_sources_and_writes_the_credit(tmp_path):
    repo = repo_with(tmp_path)
    target = library.add(project(tmp_path), repo, "octocat", agent="Claude Code")
    assert target == repo / "library" / "snow-day"
    assert sorted(p.name for p in target.iterdir()) == ["BRIEF.md", "entry.json", "font.py"]
    entry = json.loads((target / "entry.json").read_text())
    assert entry == {"github": "octocat", "prompt": "A font that feels like a snow day.", "agent": "Claude Code"}
    assert library.problems(target, repo, author="octocat", sources_only=True) == []
    assert library.find_repo(target) == repo.resolve()


def test_the_credit_goes_to_the_account_that_opens_the_pull_request(tmp_path):
    repo = repo_with(tmp_path)
    target = library.add(project(tmp_path), repo, "octocat")
    found = library.problems(target, repo, author="someone-else", build=False)
    assert len(found) == 1 and "pull request is from 'someone-else'" in found[0]
    with pytest.raises(ValueError):
        library.add(project(tmp_path, "Other"), repo, "not a username")


def test_an_entry_is_refused_for_a_taken_name_a_closed_license_or_built_fonts(tmp_path):
    repo = repo_with(tmp_path)
    taken = library.add(project(tmp_path, "Arroyo"), repo, "octocat")
    assert any("already has a family of this name" in line for line in library.problems(taken, repo, build=False))
    closed = library.add(project(tmp_path, "Shut", ', license="All rights reserved"'), repo, "octocat")
    assert any("license must be OFL-1.1" in line for line in library.problems(closed, repo, build=False))
    fine = library.add(project(tmp_path, "Fine Day"), repo, "octocat")
    (fine / "fonts").mkdir()
    (fine / "notes.txt").write_text("hello")
    found = library.problems(fine, repo, sources_only=True, build=False)
    assert any(line.startswith("fonts/") for line in found) and any(line.startswith("notes.txt") for line in found)


def test_an_entry_can_name_the_word_of_its_tile_and_its_mood_words(tmp_path):
    import json
    repo = repo_with(tmp_path)
    target = library.add(project(tmp_path), repo, "octocat")
    entry = json.loads((target / "entry.json").read_text())
    (target / "entry.json").write_text(json.dumps(dict(entry, word="Snow", moods="cozy winter school holiday")))
    assert library.problems(target, repo, build=False) == []
    (target / "entry.json").write_text(json.dumps(dict(entry, word="A whole sentence, not a word", moods="", color="red")))
    found = library.problems(target, repo, build=False)
    assert len(found) == 3 and any('"word"' in line for line in found) and any('"moods"' in line for line in found)
    assert any("unknown key 'color'" in line for line in found)


def test_only_the_owner_replaces_an_entry(tmp_path):
    repo = repo_with(tmp_path)
    work = project(tmp_path)
    library.add(work, repo, "octocat")
    with pytest.raises(FileExistsError):
        library.add(work, repo, "octocat")
    with pytest.raises(ValueError):
        library.add(work, repo, "mallory", update=True)
    assert library.add(work, repo, "octocat", update=True).is_dir()


def test_the_command_adds_checks_and_builds(tmp_path, capsys):
    repo = repo_with(tmp_path)
    work = project(tmp_path)
    assert main(["library", "add", str(work), "--github", "octocat", "--repo", str(repo)]) == 0
    assert "gh pr create" in capsys.readouterr().out
    assert main(["library", "check", "--repo", str(repo), "--author", "octocat", "--sources-only"]) == 0
    assert main(["library", "build", "--repo", str(repo)]) == 0
    assert (repo / "library" / "snow-day" / "fonts" / "index.json").is_file()
    assert main(["library", "check", "--repo", str(repo), "--sources-only"]) == 1      # the fonts are there now
    assert main(["library", "add", str(work), "--github", "octocat", "--repo", str(tmp_path)]) == 2   # not a checkout
