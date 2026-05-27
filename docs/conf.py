# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
# conf.py
import sys
from unittest.mock import MagicMock


class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


# Mock modules that might cause import errors
MOCK_MODULES = ['xarray', 'numpy', 'pandas']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# Add autodoc_type_aliases for modern type annotations
autodoc_type_aliases = {
    'xr.Dataset | None': 'Optional[xarray.Dataset]',
}

# Add autodoc_typehints_format to handle modern type annotations
autodoc_typehints_format = 'fully-qualified'

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
from eviz import __version__
about = {"__version__": __version__}

project = 'EViz'
author = 'EViz Developers'

# The full version, including alpha/beta/rc tags
release = about["__version__"]

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autosectionlabel',  # link from text to a heading using :ref:
    'sphinx.ext.autodoc',  # autodocument
    'sphinx.ext.napoleon',  # google and numpy doc string support
    'sphinx.ext.mathjax',  # latex rendering of equations using MathJax
    'sphinx.ext.viewcode',  # add links to view code
    'sphinx.ext.intersphinx',  # link to other projects
    'sphinx.ext.autosummary',  # generate summary tables
    'sphinx.ext.doctest',  # test code examples
    'sphinx.ext.githubpages',  # publish to GitHub pages
    'myst_parser',
    'sphinxcontrib.mermaid',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".

# -- Napoleon autodoc options -------------------------------------------------
napoleon_numpy_docstring = True
napoleon_use_ivar = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Autodoc options ----------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': False,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# Generate autosummary even if no references
autosummary_generate = False  # Disabled to avoid import issues
autosummary_imported_members = False

# Document __init__ methods
autoclass_content = 'both'

# -- Intersphinx mapping ------------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'xarray': ('https://docs.xarray.dev/en/stable/', None),
    'cartopy': ('https://scitools.org.uk/cartopy/docs/latest/', None),
    'dask': ('https://docs.dask.org/en/stable/', None),
}

# -- Other settings -----------------------------------------------------------

# Path to logo image file
html_logo = 'static/ASTG_logo_simple.png'

html_theme_options = {
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#175762',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# Add custom CSS
html_static_path = ['static']
html_css_files = ['custom.css']

# Show source link
html_show_sourcelink = True
html_copy_source = True

# Allows to build the docs with a minimal environment without warnings about missing packages
autodoc_mock_imports = [
    'matplotlib',
    'mpl_toolkits',
    'holoviews',
    'cartopy',
    'xesmf',
    'numpy',
    'pyhdf',
    'dask',
    'panel',
    'param',
    'bokeh',
    'geoviews',
    'hvplot',
    'h5py',
    'netcdf4',
    'pandas',
    'scipy',
    'tqdm',
    'yaml',
    'cftime',
    'xarray',
    'pytest',
    'pydap',
    'streamlit',
    'sklearn',
    'PIL',
]

suppress_warnings = ['autosectionlabel.*', 'app.add_directive']
