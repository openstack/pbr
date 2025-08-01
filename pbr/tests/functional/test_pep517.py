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

import textwrap

from pbr.tests import fixtures as pbr_fixtures
from pbr.tests.functional import base


class TestPEP517Support(base.BaseTestCase):
    def test_pep_517_support(self):
        # Note that the current PBR PEP517 entrypoints rely on a valid
        # PBR setup.py existing.
        pkgs = {
            'test_pep517': {
                'requirements.txt': textwrap.dedent(
                    """\
                        sphinx
                        iso8601
                    """
                ),
                # Override default setup.py to remove setup_requires.
                'setup.py': textwrap.dedent(
                    """\
                        #!/usr/bin/env python
                        import setuptools
                        setuptools.setup(pbr=True)
                    """
                ),
                'setup.cfg': textwrap.dedent(
                    """\
                        [metadata]
                        name = test_pep517
                        summary = A tiny test project
                        author = PBR Team
                        author_email = foo@example.com
                        home_page = https://example.com/
                        classifier =
                            Intended Audience :: Information Technology
                            Intended Audience :: System Administrators
                            License :: OSI Approved :: Apache Software License
                            Operating System :: POSIX :: Linux
                            Programming Language :: Python
                            Programming Language :: Python :: 2
                            Programming Language :: Python :: 2.7
                            Programming Language :: Python :: 3
                            Programming Language :: Python :: 3.6
                            Programming Language :: Python :: 3.7
                            Programming Language :: Python :: 3.8
                    """
                ),
                # note that we use 36.6.0 rather than 64.0.0 since the
                # latter doesn't support Python < 3.8 and we run our tests
                # against Python 2.7 still. That's okay since we're not
                # testing PEP-660 functionality here (which requires the
                # newer setuptools)
                'pyproject.toml': textwrap.dedent(
                    """\
                        [build-system]
                        requires = ["pbr", "setuptools>=36.6.0", "wheel"]
                        build-backend = "pbr.build"
                    """
                ),
            },
        }
        pkg_dirs = self.useFixture(pbr_fixtures.Packages(pkgs)).package_dirs
        pkg_dir = pkg_dirs['test_pep517']
        venv = self.useFixture(pbr_fixtures.Venv('PEP517'))

        # Test building sdists and wheels works. Note we do not use pip here
        # because pip will forcefully install the latest version of PBR on
        # pypi to satisfy the build-system requires. This means we can't self
        # test changes using pip. Build with --no-isolation appears to avoid
        # this problem.
        self._run_cmd(
            venv.python,
            ('-m', 'build', '--no-isolation', '.'),
            allow_fail=False,
            cwd=pkg_dir,
        )
