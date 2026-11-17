# Pebble Sans

Inter with rounded corners. It shows `whateverfont remix`, which restyles the outlines of an existing open font.

```sh
curl -L -o Inter.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
whateverfont remix Inter.ttf --name "Pebble Sans" --round 46 --at wght=480,opsz=28 --out examples/pebble/fonts
```

`--round 46` replaces every sharp corner with an arc of 46 units per 1000. `--at` picks the instance of the
variable source. The remix keeps all of Inter: 2,849 characters (Latin, Greek, Cyrillic, arrows, signs) and its
39 OpenType features, such as tabular figures, fractions and the slashed zero. It takes about 4 seconds.
Add `--latin` to cut the result down to Latin letters for a smaller file.

## License

Pebble Sans is a modified version of [Inter](https://github.com/rsms/inter), copyright 2020 The Inter Project
Authors. It is distributed under the SIL Open Font License 1.1, the same license as Inter. See
[OFL.txt](OFL.txt). The remix has a different name, as the license asks.
