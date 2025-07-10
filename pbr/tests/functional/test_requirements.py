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
import textwrap

import pkg_resources

from pbr.tests import fixtures as pbr_fixtures
from pbr.tests.functional import base


class TestRequirementParsing(base.BaseTestCase):

    def test_requirement_parsing(self):
        pkgs = {
            'test_reqparse': {
                'requirements.txt': textwrap.dedent(
                    """\
                        bar
                        quux<1.0; python_version=='2.6'
                        requests-aws>=0.1.4    # BSD License (3 clause)
                        Routes>=1.12.3,!=2.0,!=2.1;python_version=='2.7'
                        requests-kerberos>=0.6;python_version=='2.7' # MIT
                    """
                ),
                'setup.cfg': textwrap.dedent(
                    """\
                        [metadata]
                        name = test_reqparse

                        [extras]
                        test =
                            foo
                            baz>3.2 :python_version=='2.7' # MIT
                            bar>3.3 :python_version=='2.7' # MIT # Apache
                    """
                ),
            },
        }
        pkg_dirs = self.useFixture(pbr_fixtures.Packages(pkgs)).package_dirs
        pkg_dir = pkg_dirs['test_reqparse']
        # pkg_resources.split_sections uses None as the title of an
        # anonymous section instead of the empty string. Weird.
        expected_requirements = {
            None: ['bar', 'requests-aws>=0.1.4'],
            ":(python_version=='2.6')": ['quux<1.0'],
            ":(python_version=='2.7')": [
                'Routes!=2.0,!=2.1,>=1.12.3',
                'requests-kerberos>=0.6',
            ],
            'test': ['foo'],
            "test:(python_version=='2.7')": ['baz>3.2', 'bar>3.3'],
        }
        venv = self.useFixture(pbr_fixtures.Venv('reqParse'))
        bin_python = venv.python
        # Two things are tested by this
        # 1) pbr properly parses markers from requirements.txt and setup.cfg
        # 2) bdist_wheel causes pbr to not evaluate markers
        self._run_cmd(
            bin_python,
            ('setup.py', 'bdist_wheel'),
            allow_fail=False,
            cwd=pkg_dir,
        )
        egg_info = os.path.join(pkg_dir, 'test_reqparse.egg-info')

        requires_txt = os.path.join(egg_info, 'requires.txt')
        with open(requires_txt, 'rt') as requires:
            generated_requirements = dict(
                pkg_resources.split_sections(requires)
            )

        # NOTE(dhellmann): We have to spell out the comparison because
        # the rendering for version specifiers in a range is not
        # consistent across versions of setuptools.

        for section, expected in expected_requirements.items():
            exp_parsed = [pkg_resources.Requirement.parse(s) for s in expected]
            gen_parsed = [
                pkg_resources.Requirement.parse(s)
                for s in generated_requirements[section]
            ]
            self.assertEqual(exp_parsed, gen_parsed)
