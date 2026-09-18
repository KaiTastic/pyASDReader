# Configuration file for the Sphinx documentation builder.

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import sys

project = "pyASDReader"
copyright = "2026, Kai Cao"
author = "Kai Cao"

try:
    release = package_version(project)
except PackageNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from _version import __version__  # type: ignore[import-not-found]

    release = __version__

version = release

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