"""The search by meaning of the library (site/search.js), run with node on the word vectors of the site."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
node = shutil.which("node")
WANT = {"cozy winter holiday": "lastbell", "retro computer terminal": "pinout", "elegant wedding invitation": "gilt",
        "ocean": "kanagawa", "techno club night": "neon", "serious report": "arroyo", "a sign for my bakery": "doorstep",
        "fast cars": "lowslung", "birds": "aviary", "minimal startup landing page": "setsquare", "old typewriter": "platen",
        "dancing people": "hopstep", "shipping boxes": "crate", "a plain font for my app": "dayshift",
        "soft friendly rounded": "softboil"}


@pytest.mark.skipif(node is None, reason="node is not installed")
def test_a_need_in_plain_words_finds_the_font():
    done = subprocess.run([node, str(ROOT / "tests" / "search_harness.js"), json.dumps(list(WANT) + ["zzzz qqqq"])],
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    wrong = {q: out[q]["top"] for q, font in WANT.items() if font not in [name for name, _ in out[q]["top"][:2]]}
    assert not wrong, wrong
    assert out["ocean"]["top"][0][1] >= 0.9                      # its own mood word: a full match
    assert out["ocean"]["why"] == [["ocean", "ocean"]]           # and the reason is shown
    assert out["zzzz qqqq"]["top"][0][1] == 0                    # words that mean nothing find nothing
    assert out["cozy winter holiday"]["next"]                    # there are words to go on with


def test_the_word_vectors_match_their_word_list():
    words = (ROOT / "site" / "search" / "vocab.txt").read_text(encoding="utf-8").split()
    assert len(words) == len(set(words)) >= 30000
    assert (ROOT / "site" / "search" / "vectors.bin").stat().st_size == len(words) * 50
