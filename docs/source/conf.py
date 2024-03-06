# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os, sys
import shutil
import subprocess
from subprocess import check_output

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- Custom configuration values and roles -----------------------------------
from docutils import nodes

def setup(app):
    app.add_config_value('sphinx_build_mode', '', 'env')
    app.add_role('latex', latexPassthru)

def latexPassthru(name, rawtext, text, lineno, inliner, options={}, content=[]):
    node = nodes.raw('',rawtext[8:-1],format='latex')
    return [node],[]

# -- Auto detect runs on readthedocs.org -------------------------------------
running_on_rtd = False

# Get current doxygen version
# (there may not be one in the system $PATH)
try:
    out = check_output(["doxygen","-v"])
    doxygen_version = out.strip().decode('utf-8')
    print("Doxygen version found in $PATH: %s" % (doxygen_version))
except:
    print("No doxygen found in system $PATH")
    pass

# Detect if we are running on readthedocs.org
out = check_output(["pwd"])
out = out.strip().decode('utf-8')
# On RTD you would see something like:
# /home/docs/checkouts/readthedocs.org/user_builds/mom6devesmgnew/checkouts/latest/docsNew
if out.find('readthedocs.org') >= 0:
    running_on_rtd = True

# -- Clean out generated content ---------------------------------------------

# Running build-sphinx for html and latexpdf requires a rebuild of auto
# generated content.  Intermediate rendering for html and pdf are very
# different.  For each pass through build-sphinx, we remove intermediate
# content.

if os.path.isdir("api/generated"):
    shutil.rmtree("api/generated/")

if os.path.isdir("xml"):
    shutil.rmtree("xml")

# Make sure there is a _build directory (this might be different
# so we can do better than blindly check here) TODO
if not(os.path.isdir("_build/html")):
    os.makedirs("_build/html")

# -- Determine how sphinx-build was called -----------------------------------

# Determine how sphinx-build called.  This is helps create proper content
# for html vs latex/pdf
sphinx_build_mode = "undefined"

# hunt for -M (or -b) and then we want the argument after it
#import pdb; pdb.set_trace()
if '-M' in sys.argv:
    idx = sys.argv.index('-M')
    sphinx_build_mode = sys.argv[idx+1]
elif '-b' in sys.argv:
    idx = sys.argv.index('-b')
    sphinx_build_mode = sys.argv[idx+1]

# RTD has a special mode: readthedocs => html
if sphinx_build_mode == 'readthedocs':
    sphinx_build_mode = 'html'

print("Sphinx-build mode: %s" % (sphinx_build_mode))

# -- Configure binary and doxygen configuration files ------------------------

# Default binary and configuration file
doxygen_bin = 'doxygen'
doxygen_conf = 'Doxyfile_rtd'

if os.path.exists('./doxygen/bin/doxygen'):
    doxygen_bin = './doxygen/bin/doxygen'

# User specified binary and configuration file
if os.environ.get('DOXYGEN_BIN'):
    if os.path.exists(os.environ.get('DOXYGEN_BIN')):
        doxygen_bin = os.environ.get('DOXYGEN_BIN')
if os.environ.get('DOXYGEN_CONF'):
    if os.path.exists(os.environ.get('DOXYGEN_CONF')):
        doxygen_conf = os.environ.get('DOXYGEN_CONF')

# -- Run the normal doxygen for the RTD sphinx run ------------------------

out = check_output([doxygen_bin,"-v"])
doxygen_version = out.strip().decode('utf-8')
print("Running Doxygen %s" % (doxygen_version))
doxygenize = "%s %s" % (doxygen_bin, doxygen_conf)
print("Running: %s" % (doxygenize))
return_code = subprocess.call(doxygenize, shell=True)
if return_code != 0: sys.exit(return_code)

# -- Project information -----------------------------------------------------

project = 'CEFI-regional-MOM6 Users Guide'
copyright = '2024, '
author = ' '

# The short X.Y version
version = 'develop'
# The full version, including alpha/beta/rc tags
release = 'main Branch Documentation'

numfig = True

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
        'sphinxcontrib.bibtex',
        'sphinx.ext.ifconfig',
        'sphinxcontrib.autodoc_doxygen',
        'sphinxfortran.fortran_domain',
]

bibtex_bibfiles = ['references.bib']

autosummary_generate = ['api/modules.rst', 'api/pages.rst']
doxygen_xml = 'xml'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'default'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_path = ["_themes", ]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}
html_theme_options = {"body_max_width": "none"}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = []
#html_static_path = ['_static']
#html_context = {}

#def setup(app):
#    app.add_css_file('custom.css')  # may also be an URL
#    app.add_css_file('theme_overrides.css')  # may also be a URL

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'CEFI-regional-MOM6'


# -- Options for LaTeX output ------------------------------------------------

latex_engine = 'pdflatex'
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
      'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
      'pointsize': '11pt',

    # Additional stuff for the LaTeX preamble.
      'preamble': r'''
        \usepackage{charter}
        \usepackage[defaultsans]{lato}
        \usepackage{inconsolata}
    ''',
    # Release name prefix
      'releasename': ' ',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'CEFI-regional-MOM6.tex', 'CEFI-regional-MOM6 Users Guide',
     ' ', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'CEFI-regional-MOM6', 'CEFI-regional-MOM6 Users Guide',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'CEFI-regional-MOM6', 'CEFI-regional-MOM6 Users Guide',
     author, 'CEFI-regional-MOM6', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
   'CEFI-regional-MOM6': ('https://CEFI-regional-MOM6.readthedocs.io/en/latest/', None),
}

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
