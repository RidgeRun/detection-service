# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# pylint: skip-file

import os
import shutil
import sys

project = 'Detection'
copyright = '2024, RidgeRun, LLC'
author = 'RidgeRun, LLC'
release = '1.0.0'

sys.path.insert(0, os.path.abspath('../..'))


def copy_custom_files(source_dir, target_dir, file_list):
    for file in file_list:
        source_file = os.path.join(source_dir, file)
        target_file = os.path.join(target_dir, file)
        shutil.copyfile(source_file, target_file)
        print(f"Copied {file} to {target_dir}")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_mdinclude'
]

# Allow documentation to be built even with missing dependencies
autodoc_mock_imports = []
try:
    import jetson_utils
except ImportError:
    autodoc_mock_imports.append('jetson_utils')

try:
    import mmj_utils
except ImportError:
    autodoc_mock_imports.append('mmj_utils')

try:
    import rrmsutils
except ImportError:
    autodoc_mock_imports.append('rrmsutils')

try:
    import rrmsutils.models.detection
except ImportError:
    autodoc_mock_imports.append('rrmsutils.models.detection')

try:
    import nanoowl
except ImportError:
    autodoc_mock_imports.append('nanoowl')

try:
    import rrmsutils.schemagenerator
except ImportError:
    autodoc_mock_imports.append('rrmsutils.schemagenerator')


templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_show_sourcelink = False
html_static_path = ['_static']
files_to_copy = ['openapi.html', 'openapi.yaml']

# Copy swagger api
copy_custom_files(os.path.abspath('../../api'), '_static', files_to_copy)
