import sys
import tomllib
from pathlib import Path

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SOURCE_DIR.parents[1]
PYPROJECT_TOML = PROJECT_DIR / "pyproject.toml"

sys.path.insert(0, str(PROJECT_DIR))

with PYPROJECT_TOML.open(mode="rb") as f:
    data = tomllib.load(f)

project = "PyEEPROM"
copyright = "%Y, Jacob Zarnstorff"
author = "Jacob Zarnstorff"
release = data["project"]["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
