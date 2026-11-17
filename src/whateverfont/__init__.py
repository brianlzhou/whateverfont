"""whateverfont: design a typeface from a brief, in code."""

from .compile import BuildResult, build_family
from .family import Axis, Family
from .glyph import G, H, V, Glyph, Recipes
from .params import Params
from .recipes import latin, mono
from .stroke import Pen

__version__ = "0.1.1"

__all__ = ["Axis", "BuildResult", "Family", "G", "Glyph", "H", "Params", "Pen", "Recipes", "V",
           "build_family", "latin", "mono", "__version__"]
