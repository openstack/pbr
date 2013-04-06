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

    pbr_config = config.get('pbr', dict())
    if (('single-version-externally-mananged' in pbr_config and
            pbr_config['single-version-externally-mananged'] in
            packaging.TRUE_VALUES) or 'manpages' in pbr_config):
        config['global']['commands'] = config['global']['commands'] + """
pbr.packaging.DistutilsInstall
"""

    #config['backwards_compat']['dependency_links'] = parse_dependency_links()
    #config['backwards_compat']['include_package_data'] = True
    #config['backwards_compat']['tests_require'] = parse_requirements(
    #    ["test-requirements.txt", "tools/test-requires"])

    files = config.get('files', dict())
    package = files.get('packages', metadata['name']).strip()
    if os.path.isdir(package):
        files['packages'] = smart_find_packages(package)

    if 'manpages' in pbr_config:
        man_sections = dict()
        manpages = pbr_config['manpages']
        data_files = files.get('data_files', '')
        for manpage in manpages.split():
            section_number = manpage.strip()[-1]
            section = man_sections.get(section_number, list())
            section.append(manpage.strip())
            man_sections[section_number] = section
        for (section, pages) in man_sections.items():
            manpath = os.path.join(packaging.get_manpath(), 'man%s' % section)
            data_files = "%s\n%s" % (data_files, "%s =" % manpath)
            for page in pages:
                data_files = "%s\n%s" % (data_files, page)
        files['data_files'] = data_files

    config['files'] = files
