# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import setuptools

from pbr import packaging


def smart_find_packages(package_list):
    """Run find_packages the way we intend."""
    packages = []
    for pkg in package_list.strip().split("\n"):
        pkg_path = pkg.replace('.', os.path.sep)
        packages.append(pkg)
        packages.extend(['%s.%s' % (pkg, f)
                         for f in setuptools.find_packages(pkg_path)])
    return "\n".join(set(packages))


def setup_hook(config):
    """Filter config parsed from a setup.cfg to inject our defaults."""
    metadata = config['metadata']
    metadata['version'] = packaging.get_version(metadata['name'],
                                                metadata.get('version', None))
    metadata['requires_dist'] = "\n".join(packaging.parse_requirements())
    config['metadata'] = metadata

    config['global'] = config.get('global', dict())
    config['global']['commands'] = config['global'].get('commands', "") + """
pbr.packaging.LocalSDist
"""
    if packaging.have_sphinx():
        config['global']['commands'] = config['global']['commands'] + """
pbr.packaging.LocalBuildDoc
pbr.packaging.LocalBuildLatex
"""

    #config['backwards_compat']['dependency_links'] = parse_dependency_links()
    #config['backwards_compat']['include_package_data'] = True
    #config['backwards_compat']['tests_require'] = parse_requirements(
    #    ["test-requirements.txt", "tools/test-requires"])

    files = config.get('files', dict())
    files['packages'] = smart_find_packages(
        files.get('packages', metadata['name']))
    config['files'] = files
