# The search by meaning

`vocab.txt` and `vectors.bin` are word vectors for the library's search: 40,013 English words, 50 numbers
each, one byte per number. `scripts/build_search.py` makes them from GloVe (Pennington, Socher and Manning,
Stanford, 2014; the 50-dimension vectors trained on Wikipedia and Gigaword), which is under the Public Domain
Dedication and License 1.0.

`moods.json` holds the mood words of each font, by the name of its folder. A font of the library can bring
its own in its `entry.json` (`"moods": "..."`). The search itself is `site/search.js`. It runs in the reader's browser, and nothing that a
reader types leaves the page.
