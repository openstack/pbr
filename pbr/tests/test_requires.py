# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# Copyright 2012 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mox
import unittest2

from pbr import requires

raw_reqs = [
    '-e git://github.com/openstack/nova/master#egg=nova',
    'http://github.com/openstack/glance/zipball/master#egg=glance',
    '-f http://pypi.openstack.org',
    '# Comment test',
    'setuptools',
    'mox>=7.5',
]

parsed_reqs = [
    'nova',
    'glance',
    '# Comment test',
    'setuptools',
    'mox>=7.5'
]


class RequiresTestCase(unittest2.TestCase):
    """Test cases for requirements parsing"""

    def setUp(self):
        super(RequiresTestCase, self).setUp()
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_parse_requirements(self):
        self.mox.StubOutWithMock(requires, "get_reqs_from_files")
        requires.get_reqs_from_files(mox.IgnoreArg()).AndReturn(raw_reqs)
        self.mox.ReplayAll()

        self.assertEqual(requires.parse_requirements(mox.IgnoreArg()),
                         parsed_reqs)
