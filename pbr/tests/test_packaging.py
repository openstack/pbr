# Copyright (c) 2013 New Dream Network, LLC (DreamHost)
#
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
#
# Copyright (C) 2013 Association of Universities for Research in Astronomy
#                    (AURA)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.
#
#     3. The name of AURA and its representatives may not be used to
#        endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY AURA ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL AURA BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS

import os
import tempfile

import fixtures
import mock
import testscenarios
from testtools import matchers

from pbr import packaging
from pbr.tests import base


class TestRepo(fixtures.Fixture):
    """A git repo for testing with.

    Use of TempHomeDir with this fixture is strongly recommended as due to the
    lack of config --local in older gits, it will write to the users global
    configuration without TempHomeDir.
    """

    def __init__(self, basedir):
        super(TestRepo, self).__init__()
        self._basedir = basedir

    def setUp(self):
        super(TestRepo, self).setUp()
        base._run_cmd(['git', 'init', '.'], self._basedir)
        base._run_cmd(
            ['git', 'config', '--global', 'user.email', 'example@example.com'],
            self._basedir)
        base._run_cmd(
            ['git', 'config', '--global', 'user.signingkey',
             'example@example.com'], self._basedir)
        base._run_cmd(['git', 'add', '.'], self._basedir)

    def commit(self):
        files = len(os.listdir(self._basedir))
        path = self._basedir + '/%d' % files
        open(path, 'wt').close()
        base._run_cmd(['git', 'add', path], self._basedir)
        base._run_cmd(['git', 'commit', '-m', 'test commit'], self._basedir)

    def tag(self, version):
        base._run_cmd(
            ['git', 'tag', '-sm', 'test tag', version], self._basedir)


class GPGKeyFixture(fixtures.Fixture):
    """Creates a GPG key for testing.

    It's recommended that this be used in concert with a unique home
    directory.
    """

    def setUp(self):
        super(GPGKeyFixture, self).setUp()
        tempdir = self.useFixture(fixtures.TempDir())
        config_file = tempdir.path + '/key-config'
        f = open(config_file, 'wt')
        try:
            f.write("""
            #%no-protection -- these would be ideal but they are documented
            #%transient-key -- but not implemented in gnupg!
            %no-ask-passphrase
            Key-Type: RSA
            Name-Real: Example Key
            Name-Comment: N/A
            Name-Email: example@example.com
            Expire-Date: 2d
            Preferences: (setpref)
            %commit
            """)
        finally:
            f.close()
        base._run_cmd(
            ['gpg', '--gen-key', '--batch', config_file], tempdir.path)


class TestPackagingInGitRepoWithCommit(base.BaseTestCase):

    scenarios = [
        ('preversioned', dict(preversioned=True)),
        ('postversioned', dict(preversioned=False)),
    ]

    def setUp(self):
        super(TestPackagingInGitRepoWithCommit, self).setUp()
        repo = self.useFixture(TestRepo(self.package_dir))
        repo.commit()
        if not self.preversioned:
            self.useFixture(fixtures.EnvironmentVariable('PBR_VERSION'))
            setup_cfg_path = os.path.join(self.package_dir, 'setup.cfg')
            with open(setup_cfg_path, 'rt') as cfg:
                content = cfg.read()
            content = content.replace(u'version = 0.1.dev', u'')
            with open(setup_cfg_path, 'wt') as cfg:
                cfg.write(content)
        self.run_setup('sdist', allow_fail=False)

    def test_authors(self):
        # One commit, something should be in the authors list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertNotEqual(body, '')

    def test_changelog(self):
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        # One commit, something should be in the ChangeLog list
        self.assertNotEqual(body, '')


class TestPackagingInGitRepoWithoutCommit(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInGitRepoWithoutCommit, self).setUp()
        self.useFixture(TestRepo(self.package_dir))
        self.run_setup('sdist', allow_fail=False)

    def test_authors(self):
        # No commits, no authors in list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertEqual(body, '\n')

    def test_changelog(self):
        # No commits, nothing should be in the ChangeLog list
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertEqual(body, 'CHANGES\n=======\n\n')


class TestPackagingInPlainDirectory(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInPlainDirectory, self).setUp()
        self.run_setup('sdist', allow_fail=False)

    def test_authors(self):
        # Not a git repo, no AUTHORS file created
        filename = os.path.join(self.package_dir, 'AUTHORS')
        self.assertFalse(os.path.exists(filename))

    def test_changelog(self):
        # Not a git repo, no ChangeLog created
        filename = os.path.join(self.package_dir, 'ChangeLog')
        self.assertFalse(os.path.exists(filename))


class TestPresenceOfGit(base.BaseTestCase):

    def testGitIsInstalled(self):
        with mock.patch.object(packaging,
                               '_run_shell_command') as _command:
            _command.return_value = 'git version 1.8.4.1'
            self.assertEqual(True, packaging._git_is_installed())

    def testGitIsNotInstalled(self):
        with mock.patch.object(packaging,
                               '_run_shell_command') as _command:
            _command.side_effect = OSError
            self.assertEqual(False, packaging._git_is_installed())


class TestNestedRequirements(base.BaseTestCase):

    def test_nested_requirement(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        nested = os.path.join(tempdir, 'nested.txt')
        with open(requirements, 'w') as f:
            f.write('-r ' + nested)
        with open(nested, 'w') as f:
            f.write('pbr')
        result = packaging.parse_requirements([requirements])
        self.assertEqual(result, ['pbr'])


class TestVersions(base.BaseTestCase):

    def setUp(self):
        super(TestVersions, self).setUp()
        self.repo = self.useFixture(TestRepo(self.package_dir))
        self.useFixture(GPGKeyFixture())
        self.useFixture(base.DiveDir(self.package_dir))

    def test_tagged_version_has_tag_version(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        version = packaging._get_version_from_git('1.2.3')
        self.assertEqual('1.2.3', version)

    def test_untagged_version_has_dev_version_postversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.4.dev1.g'))

    def test_untagged_version_has_dev_version_preversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        version = packaging._get_version_from_git('1.2.5')
        self.assertThat(version, matchers.StartsWith('1.2.5.dev1.g'))

    def test_preversion_too_low(self):
        # That is, the target version is either already released or not high
        # enough for the semver requirements given api breaks etc.
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        # Note that we can't target 1.2.3 anymore - with 1.2.3 released we
        # need to be working on 1.2.4.
        err = self.assertRaises(
            ValueError, packaging._get_version_from_git, '1.2.3')
        self.assertThat(err.args[0], matchers.StartsWith('git history'))


def load_tests(loader, in_tests, pattern):
    return testscenarios.load_tests_apply_scenarios(loader, in_tests, pattern)
