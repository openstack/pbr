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

from __future__ import absolute_import
from __future__ import print_function

import os
import sys

import fixtures

from pbr.tests.functional import base


class TestConsoleScripts(base.BaseTestCase):
    """Test generation of custom console scripts.

    We generate custom console scripts that do not rely on pkg_resources to
    handle imports. This is no longer a concern starting with pip 19.0, since
    pip handles generation of scripts for wheel and starting in 19.0, pip nows
    generate an intermediate wheel during installation.
    """

    cmd_names = ('pbr_test_cmd', 'pbr_test_cmd_with_class')

    def check_script_install(self, install_stdout):
        for cmd_name in self.cmd_names:
            install_txt = 'Installing %s script to %s' % (
                cmd_name,
                self.temp_dir,
            )
            self.assertIn(install_txt, install_stdout)

            cmd_filename = os.path.join(self.temp_dir, cmd_name)

            script_txt = open(cmd_filename, 'r').read()
            self.assertNotIn('pkg_resources', script_txt)

            stdout, _, return_code = self._run_cmd(cmd_filename)
            self.assertIn("PBR", stdout)

    def test_console_script_install(self):
        """Test that we install a non-pkg-resources console script."""

        if os.name == 'nt':
            self.skipTest('Windows support is passthrough')

        stdout, _, return_code = self.run_setup(
            'install_scripts', '--install-dir=%s' % self.temp_dir
        )

        self.useFixture(fixtures.EnvironmentVariable('PYTHONPATH', '.'))

        self.check_script_install(stdout)

    def test_console_script_develop(self):
        """Test that we develop a non-pkg-resources console script."""

        if sys.version_info < (3, 0):
            self.skipTest(
                'Fails with recent virtualenv due to '
                'https://github.com/pypa/virtualenv/issues/1638'
            )

        if os.name == 'nt':
            self.skipTest('Windows support is passthrough')

        # setuptools v80.0.0 switched to using pip for the 'develop' command,
        # which means easy_install is no longer invoked
        #
        # https://github.com/pypa/setuptools/commit/98e6b4cac625c6c13b718eeccea42d00d75f2577
        # https://setuptools.pypa.io/en/stable/history.html#v80-0-0
        if self.get_setuptools_version() >= (80, 0):
            self.skipTest('setuptools is too new')

        self.useFixture(
            fixtures.EnvironmentVariable('PYTHONPATH', ".:%s" % self.temp_dir)
        )

        stdout, _, return_code = self.run_setup(
            'develop', '--install-dir=%s' % self.temp_dir
        )

        self.check_script_install(stdout)
