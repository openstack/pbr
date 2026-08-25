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

# this code will only work on Python 3.11+ (which adds tomllib), but nothing
# should be importing this code on older versions

import tomllib

from pbr.hooks import metadata as metadata_hooks
from pbr.setupcfg import split_multiline


def pbr(dist):
    """Inject dynamic config for PEP 517 / pyproject.toml-only builds.

    This is the setuptools.finalize_distribution_options hook. It handles
    projects that use only pyproject.toml with no setup.py (and therefore
    never trigger the distutils.setup_keywords handler in setupcfg.py).

    When setup.py with pbr=True is present, that handler sets
    _pbr_initialized before this hook runs, so we skip to avoid
    double-injection.
    """
    if hasattr(dist, '_pbr_initialized'):
        return

    try:
        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
    except FileNotFoundError:
        return

    # Only activate for projects that have explicitly chosen pbr as their
    # build backend. Checking this prevents us from injecting into projects
    # that merely have pbr as a runtime dependency but use a different backend.
    build_backend = pyproject.get("build-system", {}).get("build-backend", "")
    if not build_backend.startswith("pbr"):
        return

    project = pyproject.get("project", {})
    dynamic = project.get("dynamic", [])

    name = dist.metadata.name or project.get("name")
    if not name:
        return

    dist._pbr_initialized = True

    config = {'metadata': {'name': name}}
    metadata_hooks.MetadataConfig(config).run()

    meta = config.get('metadata', {})
    if 'version' in meta and 'version' in dynamic:
        dist.metadata.version = meta['version']
    if 'requires_dist' in meta and 'dependencies' in dynamic:
        dist.install_requires = split_multiline(meta['requires_dist'])

    if 'sdist' not in dist.cmdclass:
        from pbr._compat.commands import LocalSDist

        dist.cmdclass['sdist'] = LocalSDist
