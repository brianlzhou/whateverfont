"""Starting points: named parameter sets a design can begin from.

A preset is not a finished typeface. It is a place to start that already
hangs together, so the first proof is worth looking at.
"""

from __future__ import annotations

from .params import Params

PRESETS: dict = {
    "grotesk": (
        "Even, low-contrast sans with closed apertures and flat terminals.",
        dict(contrast=0.88, aperture=0.2, cut="horizontal", classical=0.0, superness=0.12, xh=520, counter=280),
    ),
    "humanist": (
        "Open, calligraphic sans with Roman capitals and a slight pen angle.",
        dict(contrast=0.74, aperture=0.85, classical=0.8, stress=12, xh=490, counter=290, apex=0.6),
    ),
    "geometric": (
        "Circles and straight lines, single-story a, sharp points.",
        dict(contrast=0.94, aperture=0.6, classical=0.6, a_story=1, apex=0.2, counter=300, xh=480, round_weight=1.02),
    ),
    "flare": (
        "Flare serif: stems swell toward their ends, Roman capitals, moderate contrast.",
        dict(flare=0.34, flare_len=230, flare_taper=1.9, contrast=0.60, aperture=0.8, classical=1.0, xh=490,
             counter=285, apex=0.5),
    ),
    "glyphic": (
        "Incised look: strong wedge-shaped flares, sharp points, high contrast.",
        dict(flare=0.62, flare_len=150, flare_taper=1.0, contrast=0.50, aperture=0.9, classical=1.0, xh=470,
             apex=0.15, counter=290, join=0.66),
    ),
    "rounded": (
        "Soft sans with fully round terminals.",
        dict(roundness=1.0, contrast=0.92, aperture=0.55, superness=0.15, xh=510, counter=290, dot="round"),
    ),
    "broadnib": (
        "Written with a broad pen held at an angle: thick diagonals, thin joins.",
        dict(contrast=0.34, stress=28, aperture=0.9, classical=0.8, flare=0.12, xh=470, counter=270, weight=96,
             join=0.9, round_weight=1.0, apex=0.2),
    ),
    "condensed": (
        "Narrow, tall sans for headlines.",
        dict(width=0.72, contrast=0.84, aperture=0.3, xh=540, cap=720, asc=750, cut="horizontal", superness=0.35),
    ),
    "mono": (
        "Monospaced, for code and terminals: every glyph 600 units wide, a dotted zero, barred i and l.",
        dict(mono=600, weight=78, contrast=0.92, aperture=0.5, cut="horizontal", superness=0.22, xh=530, cap=700,
             asc=750, counter=276, a_story=2, apex=0.8, join=0.8),
    ),
    "technical": (
        "Squared rounds and flat cuts, like labels on a machine.",
        dict(superness=0.85, contrast=0.92, aperture=0.35, cut="horizontal", roundness=0.25, xh=520, counter=275,
             a_story=1, apex=0.9),
    ),
    "typewriter": (
        "Monospaced slab serif, like a portable typewriter: even strokes, round ends, wide letters.",
        dict(mono=600, serif=56, serif_weight=0.92, roundness=0.85, contrast=0.9, weight=74, cap_weight=1.02,
             round_weight=1.0, join=0.9, xh=520, cap=690, asc=740, desc=-220, counter=300, aperture=0.62,
             apex=0.55, dot="round"),
    ),
}


def preset(name: str, **changes) -> Params:
    """Parameters for a named preset, with optional changes on top."""
    if name not in PRESETS:
        raise KeyError(f"unknown preset {name!r}; choose from {', '.join(PRESETS)}")
    values = dict(PRESETS[name][1])
    values.update(changes)
    return Params(**values)


def describe() -> str:
    width = max(len(n) for n in PRESETS)
    return "\n".join(f"{n.ljust(width)}  {d}" for n, (d, _) in PRESETS.items())
