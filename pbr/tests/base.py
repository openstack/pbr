# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
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

"""Common utilities used in testing"""

from __future__ import absolute_import
from __future__ import print_function

import os
import shutil
import sys

import fixtures
import testresources
import testtools

from pbr import options


class BaseTestCase(testtools.TestCase, testresources.ResourcedTestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 30)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            # If timeout value is invalid, fail hard.
            print(
                "OS_TEST_TIMEOUT set to invalid value"
                " defaulting to no timeout"
            )
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        if os.environ.get('OS_STDOUT_CAPTURE') in options.TRUE_VALUES:
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if os.environ.get('OS_STDERR_CAPTURE') in options.TRUE_VALUES:
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))
        self.log_fixture = self.useFixture(fixtures.FakeLogger('pbr'))

        # Older git does not have config --local, so create a temporary home
        # directory to permit using git config --global without stepping on
        # developer configuration.
        self.useFixture(fixtures.TempHomeDir())
        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.FakeLogger())
        # TODO(lifeless) we should remove PBR_VERSION from the environment.
        # rather than setting it, because thats not representative - we need to
        # test non-preversioned codepaths too!
        self.useFixture(fixtures.EnvironmentVariable('PBR_VERSION', '0.0'))

        self.temp_dir = self.useFixture(fixtures.TempDir()).path
        self.package_dir = os.path.join(self.temp_dir, 'testpackage')
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), 'testpackage'),
            self.package_dir,
        )
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.package_dir)
        self.addCleanup(self._discard_testpackage)
        # Tests can opt into non-PBR_VERSION by setting preversioned=False as
        # an attribute.
        if not getattr(self, 'preversioned', True):
            self.useFixture(fixtures.EnvironmentVariable('PBR_VERSION'))
            setup_cfg_path = os.path.join(self.package_dir, 'setup.cfg')
            with open(setup_cfg_path, 'rt') as cfg:
                content = cfg.read()
            content = content.replace(u'version = 0.1.dev', u'')
            with open(setup_cfg_path, 'wt') as cfg:
                cfg.write(content)

    def _discard_testpackage(self):
        # Remove pbr.testpackage from sys.modules so that it can be freshly
        # re-imported by the next test
        for k in list(sys.modules):
            if k == 'pbr_testpackage' or k.startswith('pbr_testpackage.'):
                del sys.modules[k]
