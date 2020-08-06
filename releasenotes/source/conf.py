# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pbr Release Notes documentation build configuration file


# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'openstackdocstheme',
    'reno.sphinxext',
]

# The master toctree document.
master_doc = 'index'

# Release notes are version independent
# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'openstackdocs'

# -- Options for openstackdocstheme ---------------------------------------

# Deprecated options for openstackdocstheme < 2.2.0, can be removed once
# pbr stops supporting py27.
repository_name = 'openstack/pbr'
bug_project = 'pbr'
bug_tag = ''

# New options with openstackdocstheme >=2.2.0
openstackdocs_repo_name = 'openstack/pbr'
openstackdocs_auto_name = False
openstackdocs_bug_project = 'pbr'
openstackdocs_bug_tag = ''
