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

import os.path
import shlex

import fixtures
import testscenarios
import testtools
import virtualenv

from pbr.tests import base

PIPFLAGS = shlex.split(os.environ.get('PIPFLAGS', ''))
PIPVERSION = os.environ.get('PIPVERSION', 'pip')
PBRVERSION = os.environ.get('PBRVERSION', 'pbr')
REPODIR = os.environ.get('REPODIR', '')
WHEELHOUSE = os.environ.get('WHEELHOUSE', '')
PIP_CMD = ['-m', 'pip'] + PIPFLAGS + ['install', '-f', WHEELHOUSE]
PROJECTS = shlex.split(os.environ.get('PROJECTS', ''))


def all_projects():
    if not REPODIR:
        return
    # Future: make this path parameterisable.
    excludes = set(['pypi-mirror', 'jeepyb', 'tempest', 'requirements'])
    for name in PROJECTS:
        name = name.strip()
        short_name = name.split('/')[-1]
        try:
            with open(os.path.join(
                    REPODIR, short_name, 'setup.py'), 'rt') as f:
                if 'pbr' not in f.read():
                    continue
        except IOError:
            continue
        if short_name in excludes:
            continue
        yield (short_name, dict(name=name, short_name=short_name))


class TestIntegration(base.BaseTestCase):

    scenarios = list(all_projects())

    def setUp(self):
        # Integration tests need a higher default - big repos can be slow to
        # clone, particularly under guest load.
        os.environ['OS_TEST_TIMEOUT'] = os.environ.get('OS_TEST_TIMEOUT',
                                                       '600')
        super(TestIntegration, self).setUp()
        base._config_git()

    def venv(self, reason):
        path = self.useFixture(fixtures.TempDir()).path
        virtualenv.create_environment(path, clear=True)
        python = os.path.join(path, 'bin', 'python')
        self.useFixture(base.CapturedSubprocess(
            'mkvenv-' + reason, [python] + PIP_CMD + [
                '-U', PIPVERSION, 'wheel', PBRVERSION]))
        return path, python

    @testtools.skipUnless(
        os.environ.get('PBR_INTEGRATION', None) == '1',
        'integration tests not enabled')
    def test_integration(self):
        # Test that we can:
        # - run sdist from the repo in a venv
        # - install the resulting tarball in a new venv
        # - pip install the repo
        # - pip install -e the repo
        # We don't break these into separate tests because we'd need separate
        # source dirs to isolate from side effects of running pip, and the
        # overheads of setup would start to beat the benefits of parallelism.
        self.useFixture(base.CapturedSubprocess(
            'sync-req',
            ['python', 'update.py', os.path.join(REPODIR, self.short_name)],
            cwd=os.path.join(REPODIR, 'requirements')))
        self.useFixture(base.CapturedSubprocess(
            'commit-requirements',
            'git diff --quiet || git commit -amrequirements',
            cwd=os.path.join(REPODIR, self.short_name), shell=True))
        path = os.path.join(
            self.useFixture(fixtures.TempDir()).path, 'project')
        self.useFixture(base.CapturedSubprocess(
            'clone',
            ['git', 'clone', os.path.join(REPODIR, self.short_name), path]))
        _, python = self.venv('sdist')
        self.useFixture(base.CapturedSubprocess(
            'sdist', [python, 'setup.py', 'sdist'], cwd=path))
        _, python = self.venv('tarball')
        filename = os.path.join(
            path, 'dist', os.listdir(os.path.join(path, 'dist'))[0])
        self.useFixture(base.CapturedSubprocess(
            'tarball', [python] + PIP_CMD + [filename]))
        root, python = self.venv('install-git')
        self.useFixture(base.CapturedSubprocess(
            'install-git', [python] + PIP_CMD + ['git+file://' + path]))
        if self.short_name == 'nova':
            found = False
            for _, _, filenames in os.walk(root):
                if 'migrate.cfg' in filenames:
                    found = True
            self.assertTrue(found)
        _, python = self.venv('install-e')
        self.useFixture(base.CapturedSubprocess(
            'install-e', [python] + PIP_CMD + ['-e', path]))


def load_tests(loader, in_tests, pattern):
    return testscenarios.load_tests_apply_scenarios(loader, in_tests, pattern)
