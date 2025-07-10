# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from testtools import matchers

from pbr.tests import fixtures as pbr_fixtures
from pbr.tests.functional import base


class TestPackagingInPlainDirectory(base.BaseTestCase):

    def test_authors(self):
        self.run_setup('sdist', allow_fail=False)
        # Not a git repo, no AUTHORS file created
        filename = os.path.join(self.package_dir, 'AUTHORS')
        self.assertFalse(os.path.exists(filename))

    def test_changelog(self):
        self.run_setup('sdist', allow_fail=False)
        # Not a git repo, no ChangeLog created
        filename = os.path.join(self.package_dir, 'ChangeLog')
        self.assertFalse(os.path.exists(filename))

    def test_install_no_ChangeLog(self):
        stdout, _, _ = self.run_setup(
            'install', '--root', self.temp_dir + 'installed', allow_fail=False
        )
        self.expectThat(
            stdout, matchers.Not(matchers.Contains('Generating ChangeLog'))
        )


class TestPackagingInGitRepoWithoutCommit(base.BaseTestCase):

    def setUp(self):
        super(TestPackagingInGitRepoWithoutCommit, self).setUp()
        self.useFixture(pbr_fixtures.GitRepo(self.package_dir))
        self.run_setup('sdist', allow_fail=False)

    def test_authors(self):
        # No commits, no authors in list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertEqual('\n', body)

    def test_changelog(self):
        # No commits, nothing should be in the ChangeLog list
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertEqual('CHANGES\n=======\n\n', body)


class TestPackagingInGitRepoWithCommit(base.BaseTestCase):

    scenarios = [
        ('preversioned', {'preversioned': True}),
        ('postversioned', {'preversioned': False}),
    ]

    def setUp(self):
        super(TestPackagingInGitRepoWithCommit, self).setUp()
        self.repo = self.useFixture(pbr_fixtures.GitRepo(self.package_dir))
        self.repo.commit()

    def test_authors(self):
        self.run_setup('sdist', allow_fail=False)
        # One commit, something should be in the authors list
        with open(os.path.join(self.package_dir, 'AUTHORS'), 'r') as f:
            body = f.read()
        self.assertNotEqual(body, '')

    def test_changelog(self):
        self.run_setup('sdist', allow_fail=False)
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        # One commit, something should be in the ChangeLog list
        self.assertNotEqual(body, '')

    def test_changelog_handles_astrisk(self):
        self.repo.commit(message_content="Allow *.openstack.org to work")
        self.run_setup('sdist', allow_fail=False)
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertIn(r'\*', body)

    def test_changelog_handles_dead_links_in_commit(self):
        self.repo.commit(message_content="See os_ for to_do about qemu_.")
        self.run_setup('sdist', allow_fail=False)
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertIn(r'os\_', body)
        self.assertIn(r'to\_do', body)
        self.assertIn(r'qemu\_', body)

    def test_changelog_handles_backticks(self):
        self.repo.commit(message_content="Allow `openstack.org` to `work")
        self.run_setup('sdist', allow_fail=False)
        with open(os.path.join(self.package_dir, 'ChangeLog'), 'r') as f:
            body = f.read()
        self.assertIn(r'\`', body)

    def test_manifest_exclude_honoured(self):
        self.run_setup('sdist', allow_fail=False)
        with open(
            os.path.join(
                self.package_dir, 'pbr_testpackage.egg-info/SOURCES.txt'
            ),
            'r',
        ) as f:
            body = f.read()
        self.assertThat(
            body, matchers.Not(matchers.Contains('pbr_testpackage/extra.py'))
        )
        self.assertThat(body, matchers.Contains('pbr_testpackage/__init__.py'))

    def test_install_writes_changelog(self):
        stdout, _, _ = self.run_setup(
            'install', '--root', self.temp_dir + 'installed', allow_fail=False
        )
        self.expectThat(stdout, matchers.Contains('Generating ChangeLog'))
