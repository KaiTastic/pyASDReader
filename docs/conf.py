# Configuration file for the Sphinx documentation builder.

project = "pyASDReader"
copyright = "2026, Kai Cao"
author = "Kai Cao"

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