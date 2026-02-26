# Configuration file for the Sphinx documentation builder.

import os
import sys
from datetime import datetime

from ansys_sphinx_theme import ansys_favicon, get_version_match

from ansys.mapdl.mcp import __version__ as version

# Add source directory to path
sys.path.insert(0, os.path.abspath("../.."))

# Project information
project = "PyMAPDL-MCP"
copyright = f"{datetime.now().year}, ANSYS, Inc."
author = "ANSYS, Inc."
cname = os.getenv("DOCUMENTATION_CNAME", "mapdl-mcp.docs.pyansys.com")

USERNAME = "ansys"
REPOSITORY_NAME = "pymapdl-mcp"
BRANCH = "main"
DOC_PATH = "doc/source"

release = version
switcher_version = get_version_match(version)

# General configuration
extensions = [
    "numpydoc",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.video",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# autodoc configuration
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "show-inheritance": True,
}

autosummary_generate = True

# HTML output configuration
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "style_nav_header_background": "#2c3e50",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_static_path = ["_static"]
html_logo = None
html_favicon = ansys_favicon

html_css_files = [
    "custom.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
]

# Options for HTMLHelp output
htmlhelp_basename = "pymapdl_mcp_doc"

# LaTeX configuration
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
}

latex_documents = [
    ("index", "pymapdl_mcp.tex", "PyMAPDL-MCP Documentation", author, "manual"),
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "ansys-mapdl-core": ("https://mapdl.docs.pyansys.com/version/stable/", None),
}

# Numpydoc configuration
numpydoc_use_plots = True
numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_validate = True
numpydoc_validation_checks = {
    # "GL06",  # Found unknown section
    # "GL07",  # Sections are in the wrong order.
    "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
html_short_title = html_title = "PyMAPDL-MCP"
html_theme = "ansys_sphinx_theme"
html_theme_options = {
    "logo": "pyansys",
    "analytics": {"google_analytics_id": "G-JQJKPV6ZVB"},
    "github_url": f"https://github.com/{USERNAME}/{REPOSITORY_NAME}",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "collapse_navigation": True,
    "use_edit_page_button": True,
    "navigation_with_keys": False,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "icon_links": [
        {
            "name": "Support",
            "url": f"https://github.com/{USERNAME}/{REPOSITORY_NAME}/discussions",
            "icon": "fa fa-comment fa-fw",
        },
        {
            "name": "Contribute",
            "url": "https://mapdl-mcp.docs.pyansys.com/version/dev/getting_started/contribution.html",  # noqa: E501
            "icon": "fa fa-wrench",
        },
    ],
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": switcher_version,
    },
    "secondary_sidebar_items": {
        "**": [],  # "page-toc", "edit-this-page", "sourcelink"]
    },
    "navbar_persistent": [],
    "primary_sidebar_end": ["edit-this-page", "sourcelink"],
    "navbar_end": [
        "search-button-field",
        "version-switcher",
        "theme-switcher",
        "navbar-icon-links",
    ],
}


html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": USERNAME,
    "github_repo": REPOSITORY_NAME,
    "github_version": BRANCH,
    "doc_path": str(DOC_PATH),
    "source_path": "src",
    "pyansys_tags": ["Structures"],
}
html_show_sourcelink = False


# notfound.extension
notfound_template = "404.rst"
notfound_urls_prefix = "/../"
html_baseurl = f"https://{cname}/version/stable"
