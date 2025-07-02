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

"""Metadata parsing."""

from __future__ import absolute_import
from __future__ import print_function

import json
import sys

_metadata_lib = None

METADATA_LIB_STDLIB = 'importlib.metadata'
METADATA_LIB_BACKPORT = 'importlib_metadata'
METADATA_LIB_LEGACY = 'pkg_resources'


def _get_metadata_lib():
    """Retrieve the correct metadata library to use."""
    global _metadata_lib

    if _metadata_lib is not None:
        return _metadata_lib

    # try importlib.metadata first. This will be available from the stdlib
    # starting in python >= 3.8
    if sys.version_info >= (3, 8):
        _metadata_lib = METADATA_LIB_STDLIB
        return _metadata_lib

    # try importlib_metadata next. This must be installed from PyPI and we
    # don't vendor it, but if available it will be preferred since later
    # versions of pkg_resources issue very annoying deprecation warnings
    try:
        import importlib_metadata  # noqa

        _metadata_lib = METADATA_LIB_BACKPORT
        return _metadata_lib
    except ImportError:
        pass

    # pkg_resources is our fallback. This will always be available on older
    # Python versions since it's part of setuptools.
    try:
        import pkg_resources  # noqa

        _metadata_lib = METADATA_LIB_LEGACY
        return _metadata_lib
    except ImportError:
        pass

    raise RuntimeError(
        'Failed to find a library for loading metadata. This should not '
        'happen. Please report a bug against pbr.'
    )


def get_distributions():
    metadata_lib = _get_metadata_lib()
    if metadata_lib == METADATA_LIB_STDLIB:
        import importlib.metadata

        data = sorted(
            importlib.metadata.distributions(),
            key=lambda x: x.metadata['name'].lower(),
        )
    elif metadata_lib == METADATA_LIB_BACKPORT:
        import importlib_metadata

        data = sorted(
            importlib_metadata.distributions(),
            key=lambda x: x.metadata['name'].lower(),
        )
    else:  # METADATA_LIB_LEGACY
        import pkg_resources

        data = sorted(
            pkg_resources.working_set,
            key=lambda dist: dist.project_name.lower(),
        )

    return list(data)


class PackageNotFound(Exception):
    def __init__(self, package_name):
        self.package_name = package_name

    def __str__(self):
        return 'Package {0} not installed'.format(self.package_name)


def get_metadata(package_name):
    metadata_lib = _get_metadata_lib()
    if metadata_lib == METADATA_LIB_STDLIB:
        import importlib.metadata

        try:
            data = importlib.metadata.distribution(package_name).metadata[
                'pbr.json'
            ]
        except importlib.metadata.PackageNotFoundError:
            raise PackageNotFound(package_name)
    elif metadata_lib == METADATA_LIB_BACKPORT:
        import importlib_metadata

        try:
            data = importlib_metadata.distribution(package_name).metadata[
                'pbr.json'
            ]
        except importlib_metadata.PackageNotFoundError:
            raise PackageNotFound(package_name)
    else:  # METADATA_LIB_LEGACY
        import pkg_resources

        try:
            data = pkg_resources.get_distribution(package_name).get_metadata(
                'pbr.json'
            )
        except pkg_resources.DistributionNotFound:
            raise PackageNotFound(package_name)

    try:
        return json.loads(data)
    except Exception:
        # TODO(stephenfin): We should log an error here. Can we still use
        # distutils.log in the future?
        return None


def get_version(package_name):
    metadata_lib = _get_metadata_lib()
    if metadata_lib == METADATA_LIB_STDLIB:
        import importlib.metadata

        try:
            return importlib.metadata.distribution(package_name).version
        except importlib.metadata.PackageNotFoundError:
            raise PackageNotFound(package_name)
    elif metadata_lib == METADATA_LIB_BACKPORT:
        import importlib_metadata

        try:
            return importlib_metadata.distribution(package_name).version
        except importlib_metadata.PackageNotFoundError:
            raise PackageNotFound(package_name)
    else:  # METADATA_LIB_LEGACY
        import pkg_resources

        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            raise PackageNotFound(package_name)
