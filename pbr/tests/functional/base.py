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

"""Common utilities used in functional testing"""

import os
import sys

from wheel import wheelfile

from pbr.tests import base
from pbr.tests import fixtures as pbr_fixtures
from pbr.tests import util


class BaseTestCase(base.BaseTestCase):

    def _run_cmd(self, cmd, args=[], allow_fail=True, cwd=None):
        """Run a command in the root of the test working copy.

        Runs a command, with the given argument list, in the root of the test
        working copy--returns the stdout and stderr streams and the exit code
        from the subprocess.

        :param cwd: If falsy run within the test package dir, otherwise run
            within the named path.
        """
        cwd = cwd or self.package_dir
        result = util.run_cmd([cmd] + list(args), cwd=cwd)
        if result[2] and not allow_fail:
            raise Exception("Command failed retcode=%s" % result[2])
        return result

    def get_setuptools_version(self):
        # we rely on this to determine whether to skip tests, so we can't allow
        # this to fail silently
        stdout, _, _ = self._run_cmd(
            sys.executable,
            ('-c', 'import setuptools; print(setuptools.__version__)'),
            allow_fail=False,
        )
        return tuple(int(x) for x in stdout.strip().split('.')[:3])

    def run_pbr(self, *args, **kwargs):
        return self._run_cmd('pbr', args, **kwargs)

    def run_setup(self, *args, **kwargs):
        return self._run_cmd(sys.executable, ('setup.py',) + args, **kwargs)


class BaseWheelTestCase(BaseTestCase):
    """Base test case for tests that build wheels."""

    def setUp(self):
        super(BaseWheelTestCase, self).setUp()
        self.useFixture(pbr_fixtures.GitRepo(self.package_dir))
        # Build the wheel
        self.run_setup('bdist_wheel', allow_fail=False)
        # Slowly construct the path to the generated whl
        dist_dir = os.path.join(self.package_dir, 'dist')
        relative_wheel_filename = os.listdir(dist_dir)[0]
        absolute_wheel_filename = os.path.join(
            dist_dir, relative_wheel_filename
        )
        wheel_file = wheelfile.WheelFile(absolute_wheel_filename)
        wheel_name = wheel_file.parsed_filename.group('namever')
        # Create a directory path to unpack the wheel to
        self.extracted_wheel_dir = os.path.join(dist_dir, wheel_name)
        # Extract the wheel contents to the directory we just created
        wheel_file.extractall(self.extracted_wheel_dir)
        wheel_file.close()
