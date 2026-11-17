"""The votes and views of the site (worker/src/counts.js), run with node and SQLite in memory."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
node = shutil.which("node")


def has_sqlite() -> bool:
    if node is None:
        return False
    done = subprocess.run([node, "-e", "require('node:sqlite')"], capture_output=True, text=True, timeout=60)
    return done.returncode == 0


@pytest.mark.skipif(not has_sqlite(), reason="node 22.5 or newer is not installed")
def test_votes_and_views_count_each_visitor_once():
    done = subprocess.run([node, str(ROOT / "tests" / "counts_harness.mjs")], capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    assert out["first"] == {"status": 200, "cors": None, "id": "arroyo", "votes": 1, "voted": True}
    assert out["again"]["votes"] == 1                      # one visitor, one vote
    assert out["other"]["votes"] == 2
    assert out["back"] == {"status": 200, "cors": None, "id": "arroyo", "votes": 1, "voted": False}
    assert out["backAgain"]["votes"] == 1                  # a vote can be taken back once
    assert out["bad"]["status"] == 400 and out["get"]["status"] == 405 and out["broken"]["status"] == 400
    assert out["unknown"]["status"] == 400 and out["unknownView"]["status"] == 400 and out["nowhere"]["status"] == 404
    assert out["view"]["views"] == 1 and out["reload"]["views"] == 1 and out["viewOther"]["views"] == 2
    assert out["nextDay"]["views"] == 3                    # the same visitor counts again on another day
    assert out["statsOne"]["fonts"] == {"arroyo": {"votes": 1, "views": 3}}        # and not the font that left
    assert out["statsOne"]["mine"] == [] and out["statsTwo"]["mine"] == ["arroyo"]
    assert out["addresses"] is False                       # the database never holds an address
    assert out["salts"] is True
    assert out["manyViews"]["status"] == 200 and out["voteAfterViews"]["status"] == 200
    assert out["flood"]["status"] == 429                   # more than 40 votes a minute are refused


@pytest.mark.skipif(not has_sqlite(), reason="node 22.5 or newer is not installed")
def test_only_the_site_may_ask_from_a_page():
    done = subprocess.run([node, str(ROOT / "tests" / "counts_harness.mjs")], capture_output=True, text=True, timeout=120)
    out = json.loads(done.stdout)
    assert out["fromSite"]["status"] == 200 and out["fromSite"]["cors"] == "https://fonts.example"
    assert out["fromPreview"]["cors"] == "https://freefont-git-new-me.vercel.app"      # a preview of the site
    assert out["fromElsewhere"]["status"] == 403 and out["fromElsewhere"]["cors"] is None
    assert out["preflight"]["status"] == 204 and out["preflight"]["cors"] == "https://fonts.example"


def test_the_worker_names_its_object_and_its_address():
    """The settings of the Worker and the site's build agree on where the counts are."""
    text = (ROOT / "worker" / "wrangler.jsonc").read_text(encoding="utf-8")
    assert '"class_name": "Library"' in text and '"storage": "sqlite"' in text
    assert "export class Library extends DurableObject" in (ROOT / "worker" / "src" / "index.js").read_text(encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)
    host, _, path = site.COUNTS_ADDRESS.removeprefix("https://").partition("/")
    assert f'"pattern": "{host}/{path}/*"' in text
    assert "https://fonts.brianzhou.org" in text                 # the site may ask
