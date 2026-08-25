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

import sys


def pbr(dist):
    """The ``setuptools.finalize_distribution_options`` entry point.

    setuptools runs *every* registered finalize_distribution_options hook
    whenever *any* ``Distribution`` is constructed -- including by unrelated
    tooling such as virtualenv, which builds a throwaway distutils
    ``Distribution`` purely to probe install paths. Resolving this entry
    point therefore imports its target module at arbitrary times and from
    arbitrary working directories.

    That is why this shim lives in the (always already-imported) ``pbr``
    package rather than in ``pbr.pyprojecttoml``. Under Python 2 develop
    installs ``pbr`` is found via a relative ``sys.path`` entry, so
    ``pbr.__path__`` is relative (``['pbr']``). Importing a not-yet-loaded
    submodule after the process has changed directory then fails with
    ``ImportError: No module named pyprojecttoml``. Anchoring the hook here
    -- and only importing the implementation on the Python versions that can
    actually build from a pyproject.toml -- avoids that fragile late import.
    """
    if sys.version_info < (3, 11):
        # pyproject.toml-only builds require tomllib, which requires Python
        # 3.11. Projects that still support older Python versions will just
        # have to continue shipping a setup.cfg and setup.py file.
        return

    from pbr import pyprojecttoml

    pyprojecttoml.pbr(dist)


# Ensure this hook runs after setuptools' built-in 'keywords' hook
pbr.order = 1
