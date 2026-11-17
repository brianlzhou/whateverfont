"""Put the skill, the reference pages and the example sources into the wheel, under whateverfont/_data.

`whateverfont skill`, `whateverfont docs` and `whateverfont examples` read them from there, so a
user needs no checkout. An editable install skips this: it reads the files where the repository keeps them.
"""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class DataHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name != "wheel" or version == "editable":
            return
        root = Path(self.root)
        files = [*root.glob("docs/*.md"), *root.glob("skills/*/SKILL.md"), root / "examples" / "OFL.txt",
                 *root.glob("examples/*/*.py"), *root.glob("examples/*/BRIEF.md")]
        for src in sorted(files):
            if src.name == "research.md" or not src.is_file():
                continue
            build_data["force_include"][str(src)] = f"whateverfont/_data/{src.relative_to(root).as_posix()}"
