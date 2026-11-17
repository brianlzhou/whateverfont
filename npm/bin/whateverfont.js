#!/usr/bin/env node
// whateverfont is a Python tool. This runs it through uv (or pipx), so `npx whateverfont ...` needs no setup.
// `npx whateverfont setup` installs the command for good and gives Claude Code the skill.
"use strict";
const { spawnSync } = require("node:child_process");
const { version } = require("../package.json");

const spec = process.env.WHATEVERFONT_SPEC || `whateverfont==${version}`;
const args = process.argv.slice(2);

function has(command) {
  const r = spawnSync(command, ["--version"], { stdio: "ignore" });
  return !r.error && r.status === 0;
}
function run(command, list) {
  const r = spawnSync(command, list, { stdio: "inherit" });
  if (r.error) { console.error(`whateverfont: could not run ${command}: ${r.error.message}`); return 1; }
  return r.status === null ? 1 : r.status;
}

let code;
if (has("uv")) {
  if (args[0] === "setup") {
    code = run("uv", ["tool", "install", "--upgrade", spec]) || run("uv", ["tool", "run", "--from", spec, "whateverfont", "skill", "install"]);
  } else {
    code = run("uv", ["tool", "run", "--from", spec, "whateverfont", ...args]);
  }
} else if (has("pipx")) {
  if (args[0] === "setup") {
    code = run("pipx", ["install", "--force", spec]) || run("pipx", ["run", "--spec", spec, "whateverfont", "skill", "install"]);
  } else {
    code = run("pipx", ["run", "--spec", spec, "whateverfont", ...args]);
  }
} else {
  console.error("whateverfont needs uv or pipx to run its Python package.\n" +
                "Install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
                "Then run this command again, or install for good:  uv tool install whateverfont");
  code = 1;
}
process.exit(code);
