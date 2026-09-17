# Configuration file for the Sphinx documentation builder.

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _version import __version__  # type: ignore[import-not-found]

project = "pyASDReader"
copyright = "2026, Kai Cao"
author = "Kai Cao"
version = __version__
release = __version__

extensions = ["myst_parser"]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []

myst_heading_anchors = 3