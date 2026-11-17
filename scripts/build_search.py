#!/usr/bin/env python3
"""Make the word vectors that the library's search by meaning uses.

The search runs in the reader's browser: no server, no key, and nothing a reader types leaves the page.
Each font has a few mood words (site/search/moods.json, the font's name and its description). Each word
of a query takes its best match among them, by the angle between two word vectors. The vectors say that
"ocean" is near "sea" and "wave", so a reader can type a need in their own words.

This script cuts the vectors down to what a page can load: the most frequent words, 50 numbers each,
stored as one byte per number. It writes site/search/vocab.txt and site/search/vectors.bin (about 2 MB
together). Run it once, or again to change the number of words:

    python scripts/build_search.py glove-wiki-gigaword-50.gz --words 40000

The source is GloVe (Pennington, Socher and Manning, Stanford, 2014), the 50-dimension vectors trained on
Wikipedia and Gigaword, under the Public Domain Dedication and License 1.0. The file is in the gensim-data
releases: https://github.com/RaRe-Technologies/gensim-data/releases/tag/glove-wiki-gigaword-50
It needs numpy (pip install 'whateverfont[trace]').
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "search"


def main() -> int:
    import numpy as np
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vectors", help="the GloVe file: text or .gz, one word and its numbers on a line")
    ap.add_argument("--words", type=int, default=40000, help="how many of the most frequent words to keep")
    args = ap.parse_args()

    # every mood word must be findable, however rare it is
    moods = json.loads((OUT / "moods.json").read_text(encoding="utf-8"))
    must = {w for text in moods.values() for w in re.findall(r"[a-z]+", text.lower())}
    opener = gzip.open if args.vectors.endswith(".gz") else open
    words, rows = [], []
    with opener(args.vectors, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip().split(" ")
            if len(parts) < 20 or not re.fullmatch(r"[a-z]+", parts[0]):
                continue                                    # the header, and words with figures or signs
            if len(words) >= args.words and parts[0] not in must:
                continue
            words.append(parts[0])
            rows.append(np.array(parts[1:], dtype=np.float32))
            must.discard(parts[0])
    v = np.vstack(rows)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    packed = np.clip(np.round(v * 127), -127, 127).astype(np.int8)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vocab.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
    (OUT / "vectors.bin").write_bytes(packed.tobytes())
    print(f"{len(words)} words, {packed.shape[1]} numbers each: vocab.txt {(OUT / 'vocab.txt').stat().st_size / 1e6:.2f} MB, "
          f"vectors.bin {(OUT / 'vectors.bin').stat().st_size / 1e6:.2f} MB")
    if must:
        print(f"mood words with no vector (they match only themselves): {' '.join(sorted(must))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
