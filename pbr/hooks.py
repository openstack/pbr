# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2012 OpenStack LLC
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

"""
Location of the setuptools hooks for manipulating setup.py metadata.
"""

import os

from pbr import requires


def __inject_parsed_file(value, func):
    TOKEN = '#:'
    new_reqs = []
    old_tokens = []
    for req in value:
        if req.startswith(TOKEN):
            old_tokens.append(req)
            req_file = req[len(TOKEN):]
            new_reqs.extend(func(req_file))
    for val in old_tokens:
        value.remove(val)
    value.extend(new_reqs)


def inject_requires(dist, attr, value):
    __inject_parsed_file(value, requires.parse_requirements)


def inject_dependency_links(dist, attr, value):
    __inject_parsed_file(value, requires.parse_dependency_links)


def inject_version(dist, attr, value):
    """Manipulate the version provided to setuptools to be one calculated
    from git.
    If the setuptools version starts with the token #:, we'll take over
    and replace it with something more friendly."""
    import setuptools

    version = dist.metadata.version
    if version and version.startswith("#:"):

        # Modify version number
        if len(version[2:]) > 0:
            (version_module, version_object) = version[2:].split(":")
        else:
            version_module = "%s" % dist.metadata.name
            version_object = "version_info"
        vinfo = __import__(version_module).__dict__[version_object]
        versioninfo_path = os.path.join(vinfo.package, 'versioninfo')
        dist.metadata.version = vinfo.canonical_version_string(always=True)

        # Inject cmdclass values here
        import cmdclass
        dist.cmdclass.update(cmdclass.get_cmdclass(versioninfo_path))

        # Inject long_description
        for readme in ("README.rst", "README.txt", "README"):
            if dist.long_description is None and os.path.exists(readme):
                dist.long_description = open(readme).read()
        dist.include_package_data = True

        # Set sensible default for test_suite
        if dist.test_suite is None:
            dist.test_suite = 'nose.collector'
        if dist.packages is None:
            dist.packages = setuptools.find_packages(exclude=['tests',
                                                              'tests.*'])
