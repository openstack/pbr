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

"""Utilities to paste over differences between Python versions."""

from __future__ import absolute_import
from __future__ import print_function

import re

_packaging_lib = None

PACKAGING_LIB_PACKAGING = 'packaging'
PACKAGING_LIB_LEGACY = 'pkg_resources'


def _get_packaging_lib():
    global _packaging_lib

    if _packaging_lib is not None:
        return _packaging_lib

    # packaging should almost always be available since setuptools vendors it
    # and has done so since forever
    #
    # https://github.com/pypa/setuptools/commit/84c9006110e53c84296a05741edb7b9edd305f12
    try:
        import packaging  # noqa

        _packaging_lib = PACKAGING_LIB_PACKAGING
        return _packaging_lib
    except ImportError:
        pass

    # pkg_resources is our fallback. This will always be available on older
    # Python versions since it's part of setuptools.
    try:
        import pkg_resources  # noqa

        _packaging_lib = PACKAGING_LIB_LEGACY
        return _packaging_lib
    except ImportError:
        pass

    raise RuntimeError(
        'Failed to find a library for parsing packaging information. This '
        'should not happen. Please report a bug against pbr.'
    )


def extract_project_name(requirement_line):
    packaging_lib = _get_packaging_lib()
    if packaging_lib == PACKAGING_LIB_PACKAGING:
        import packaging.requirements

        try:
            requirement = packaging.requirements.Requirement(requirement_line)
        except ValueError:
            return None

        # the .project_name attribute is not part of the
        # packaging.requirements.Requirement API so we mimic it
        #
        # https://github.com/pypa/setuptools/blob/v80.9.0/pkg_resources/__init__.py#L2918
        return re.sub('[^A-Za-z0-9.]+', '-', requirement.name)
    else:  # PACKAGING_LIB_LEGACY
        import pkg_resources

        try:
            requirement = pkg_resources.Requirement.parse(requirement_line)
        except ValueError:
            return None
        return requirement.project_name


def parse_version(version):
    packaging_lib = _get_packaging_lib()
    if packaging_lib == PACKAGING_LIB_PACKAGING:
        import packaging.version

        return packaging.version.Version(version)
    else:  # PACKAGING_LIB_LEGACY
        import pkg_resources

        return pkg_resources.parse_version(version)


def evaluate_marker(marker):
    packaging_lib = _get_packaging_lib()
    if packaging_lib == PACKAGING_LIB_PACKAGING:
        import packaging.markers

        try:
            return packaging.markers.Marker(marker).evaluate()
        except packaging.markers.InvalidMarker as e:
            # setuptools expects a SyntaxError here, so we do the same.
            # we can't chain the exceptions since that is a Python 3 only thing
            raise SyntaxError(e)
    else:  # PACKAGING_LIB_LEGACY
        import pkg_resources

        return pkg_resources.evaluate_marker(marker)
