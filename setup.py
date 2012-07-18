# Copyright 2011 OpenStack, LLC
# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pkg_resources
import setuptools

import pbr
from pbr import cmdclass
from pbr import requires


def _fake_require(*args, **kwargs):
    """We need to block this from recursing - we're instaling an
    entry_point, which trys to install us while it's getting installed."""
    pass
pkg_resources.EntryPoint.require = _fake_require


setuptools.setup(
    name="pbr",
    version=pbr.version_info.canonical_version_string(always=True),
    author='Hewlett-Packard Development Company, L.P.',
    author_email='openstack@lists.launchpad.net',
    description="Python Build Reasonableness",
    license="Apache License, Version 2.0",
    url="https://github.com/openstack-dev/pbr",
    install_requires=requires.parse_requirements('tools/pip-requires'),
    tests_require=requires.parse_requirements('tools/test-requires'),
    dependency_links=requires.parse_dependency_links('tools/pip-requires',
                                                     'tools/test-requires'),
    setup_requires=['setuptools-git>0.4'],
    cmdclass=cmdclass.get_cmdclass('pbr/versioninfo'),
    long_description=open('README.rst').read(),
    include_package_data=True,
    test_suite='nose.collector',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python"
    ],
    entry_points={
        "distutils.setup_keywords": [
            "version = pbr.hooks:inject_version",
            "install_requires = pbr.hooks:inject_requires",
            "dependency_links = pbr.hooks:inject_dependency_links",
        ]
    }
)
