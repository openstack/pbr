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
import sysconfig

from pbr.tests.functional import base

try:
    import importlib.machinery

    get_suffixes = importlib.machinery.all_suffixes
# NOTE(JayF): ModuleNotFoundError only exists in Python 3.6+, not in 2.7
except ImportError:
    import imp

    # NOTE(JayF) imp.get_suffixes returns a list of three-tuples;
    # we need the first value from each tuple.

    def get_suffixes():
        return [x[0] for x in imp.get_suffixes]


def get_soabi():
    soabi = None
    try:
        soabi = sysconfig.get_config_var('SOABI')
        arch = sysconfig.get_config_var('MULTIARCH')
    except IOError:
        pass
    if soabi and arch and 'pypy' in sysconfig.get_scheme_names():
        soabi = '%s-%s' % (soabi, arch)
    if soabi is None and 'pypy' in sysconfig.get_scheme_names():
        # NOTE(sigmavirus24): PyPy only added support for the SOABI config var
        # to sysconfig in 2015. That was well after 2.2.1 was published in the
        # Ubuntu 14.04 archive.
        for suffix in get_suffixes():
            if suffix.startswith('.pypy') and suffix.endswith('.so'):
                soabi = suffix.split('.')[1]
                break
    return soabi


class TestCExtension(base.BaseWheelTestCase):

    def test_generates_c_extensions(self):
        built_package_dir = os.path.join(
            self.extracted_wheel_dir, 'pbr_testpackage'
        )
        static_object_filename = 'testext.so'
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        if ext_suffix is not None:
            static_object_filename = 'testext' + ext_suffix
        else:
            soabi = get_soabi()
            if soabi:
                static_object_filename = 'testext.{0}.so'.format(soabi)
        static_object_path = os.path.join(
            built_package_dir, static_object_filename
        )

        self.assertTrue(os.path.exists(built_package_dir))
        self.assertTrue(os.path.exists(static_object_path))
