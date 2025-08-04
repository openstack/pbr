# -*- coding: utf-8 -*-
# Copyright (C) 2020 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# -- General configuration ----------------------------------------------------

extensions = ['sphinx.ext.apidoc', 'sphinx.ext.todo', 'reno.sphinxext']

# make openstackdocstheme optional to not increase the needed dependencies
try:
    import openstackdocstheme

    extensions.append('openstackdocstheme')
except ImportError:
    openstackdocstheme = None

# openstackdocstheme options

# New options with openstackdocstheme >=2.2.0
openstackdocs_repo_name = 'openstack/pbr'
openstackdocs_auto_name = False
openstackdocs_bug_project = 'pbr'
openstackdocs_bug_tag = ''

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pbr'
copyright = '2013-, OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

exclude_trees = []

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
if openstackdocstheme is not None:
    html_theme = 'openstackdocs'
else:
    html_theme = 'default'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    (
        'index',
        '%s.tex' % project,
        '%s Documentation' % project,
        'OpenStack Foundation',
        'manual',
    ),
]

# -- Options for sphinx.ext.apidoc extension ----------------------------------

apidoc_modules = [
    {
        'path': '../../pbr',
        'destination': 'reference/api',
        'exclude_patterns': ['**/tests/*'],
    },
]
