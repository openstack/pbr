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
import shutil
import subprocess
import sys

import fixtures
import testtools


class D2to1TestCase(testtools.TestCase):
    def setUp(self):
        super(D2to1TestCase, self).setUp()
        self.temp_dir = self.useFixture(fixtures.TempDir()).path
        self.package_dir = os.path.join(self.temp_dir, 'testpackage')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'testpackage'),
                        self.package_dir)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.package_dir)

    def tearDown(self):
        # Remove d2to1.testpackage from sys.modules so that it can be freshly
        # re-imported by the next test
        for k in list(sys.modules):
            if (k == 'd2to1_testpackage' or
                    k.startswith('d2to1_testpackage.')):
                del sys.modules[k]
        super(D2to1TestCase, self).tearDown()

    def run_setup(self, *args):
        return self._run_cmd(sys.executable, ('setup.py',) + args)

    def _run_cmd(self, cmd, args):
        """Run a command in the root of the test working copy.

        Runs a command, with the given argument list, in the root of the test
        working copy--returns the stdout and stderr streams and the exit code
        from the subprocess.
        """

        os.chdir(self.package_dir)
        p = subprocess.Popen([cmd] + list(args), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        streams = tuple(s.decode('latin1').strip() for s in p.communicate())
        print(streams)
        return (streams) + (p.returncode,)
