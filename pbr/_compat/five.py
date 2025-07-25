# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Poor man's six."""

from __future__ import absolute_import
from __future__ import print_function

import sys

# builtins

if sys.version_info >= (3, 0):
    string_type = str
    integer_types = (int,)
else:
    string_type = basestring  # noqa
    integer_types = (int, long)  # noqa

# io

if sys.version_info >= (3, 0):
    import io

    BytesIO = io.BytesIO
else:
    import cStringIO as io

    BytesIO = io.StringIO

# configparser

if sys.version_info >= (3, 0):
    import configparser

    ConfigParser = configparser.ConfigParser
else:
    import ConfigParser as configparser

    ConfigParser = configparser.SafeConfigParser
    # monkeypatch in renamed method
    ConfigParser.read_file = ConfigParser.readfp

# urllib.parse.urlparse

if sys.version_info >= (3, 0):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse  # noqa

# urllib.request.urlopen

if sys.version_info >= (3, 0):
    from urllib.request import urlopen
else:
    from urllib2 import urlopen  # noqa
