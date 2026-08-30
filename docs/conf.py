"""Sphinx configuration for qmath documentation."""

import os
import sys

# Add source directory to path
sys.path.insert(0, os.path.abspath("../src"))

project = "qmath"
copyright = "2024, Alexander Arias"
author = "Alexander Arias"

release = "0.1.0.dev0"
version = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_gallery.gen_gallery",
    "sphinxcontrib.bibtex",
]

autosummary_generate = True
autosummary_generate_overwrite = False
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# Numpydoc configuration
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

# sphinx-gallery configuration
sphinx_gallery_conf = {
    "examples_dirs": ["../examples"],
    "gallery_dirs": ["auto_examples"],
    "plot_gallery": True,
    "download_all_examples": False,
    "abort_on_example_error": False,
    "backreferences_dir": None,
    "doc_module": ("qmath",),
    "reference_url": {"qmath": None},
    "show_memory": False,
    "junit": "",
    "reset_modules": ("matplotlib", "seaborn"),
    "first_notebook_cell": None,
    "last_notebook_cell": None,
    "notebook_images": False,
}

# BibTeX configuration
bibtex_bibfiles = ["theory/references.bib"]

# Theme
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "github_url": "https://github.com/aleexarias/qmath",
    "show_nav_level": 2,
}

html_static_path = ["_static"]
html_logo = None

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

exclude_patterns = ["_build", ".ipynb_checkpoints"]

# Output
html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_show_sourcelink = True
html_show_sphinx = False

# Warnings
suppress_warnings = ["app.add_config_value"]
