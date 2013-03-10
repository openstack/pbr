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
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

from distutils.core import Distribution as _Distribution
from distutils.errors import DistutilsFileError, DistutilsSetupError
import os
import sys
import warnings

from distutils import log
import pkg_resources
from setuptools.dist import _get_unpatched
from .extern import six

from oslo.packaging import util
from oslo.packaging import packaging

_Distribution = _get_unpatched(_Distribution)
log.set_verbosity(log.INFO)


def setup(dist, attr, value):
    """Implements the actual oslo.packaging setup() keyword.
    
    When used, this should be the only keyword in your setup() aside from
    `setup_requires`.

    This works by reading the setup.cfg file, parsing out the supported
    metadata and command options, and using them to rebuild the
    `DistributionMetadata` object and set the newly added command options.

    The reason for doing things this way is that a custom `Distribution` class
    will not play nicely with setup_requires; however, this implementation may
    not work well with distributions that do use a `Distribution` subclass.
    """

    log.info("[oslo.packaging] Processing setup.cfg")
    if not value:
        return
    path = os.path.abspath('setup.cfg')
    if not os.path.exists(path):
        raise DistutilsFileError(
            'The setup.cfg file %s does not exist.' % path)

    # Converts the setup.cfg file to setup() arguments
    try:
        attrs = util.cfg_to_args(path)
    except:
        e = sys.exc_info()[1]
        raise DistutilsSetupError(
            'Error parsing %s: %s: %s' % (path, e.__class__.__name__,
                                          six.u(e)))

    # Repeat some of the Distribution initialization code with the newly
    # provided attrs
    if attrs:

        # Handle additional setup processing
        if 'setup_requires' in attrs:
            chainload_setups(dist, attrs['setup_requires'])

        for ep in pkg_resources.iter_entry_points(
                'oslo.packaging.attr_filters'):
            filter_method = ep.load()
            attrs = filter_method(attrs)

        # Skips 'options' and 'licence' support which are rarely used; may add
        # back in later if demanded
        for key, val in six.iteritems(attrs):
            if hasattr(dist.metadata, 'set_' + key):
                getattr(dist.metadata, 'set_' + key)(val)
            elif hasattr(dist.metadata, key):
                setattr(dist.metadata, key, val)
            elif hasattr(dist, key):
                setattr(dist, key, val)
            else:
                msg = 'Unknown distribution option: %s' % repr(key)
                warnings.warn(msg)

    # Re-finalize the underlying Distribution
    _Distribution.finalize_options(dist)

    # This bit comes out of distribute/setuptools
    if isinstance(dist.metadata.version, six.integer_types + (float,)):
        # Some people apparently take "version number" too literally :)
        dist.metadata.version = str(dist.metadata.version)


def chainload_setups(dist, requires_list):
    try:
        import pip.command.install
    except ImportError:
        from setuptools.command.easy_install import easy_install
        cmd = easy_install(dist, args=["x"], install_dir=os.curdir,
                           exclude_scripts=True, always_copy=False,
                           build_directory=None, editable=False,
                           upgrade=False, multi_version=True, no_report=True)
        cmd.ensure_finalized()
        cmd.easy_install("req")
        import pip.command.install

    pip_install = pip.command.install.InstallCommand()
    pip_install.run({}, requires_list)
