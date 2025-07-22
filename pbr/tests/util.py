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

import contextlib
import os
import shutil
import stat
import subprocess
import sys

from pbr._compat.five import ConfigParser


@contextlib.contextmanager
def open_config(filename):
    cfg = ConfigParser()
    cfg.read(filename)
    yield cfg
    with open(filename, 'w') as fp:
        cfg.write(fp)


def rmtree(path):
    """shutil.rmtree() with error handler.

    Handle 'access denied' from trying to delete read-only files.
    """

    def onexc(func, path, exc_info):
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    if sys.version_info >= (3, 12):
        return shutil.rmtree(path, onexc=onexc)
    else:
        return shutil.rmtree(path, onerror=onexc)


def run_cmd(args, cwd):
    """Run the command args in cwd.

    :param args: The command to run e.g. ['git', 'status']
    :param cwd: The directory to run the command in.
    :param env: The environment variables to set. If unset, fallback to the
        default of inheriting those from the current process.
    :return: ((stdout, stderr), returncode)
    """
    env = os.environ.copy()
    env['PYTHONWARNINGS'] = 'ignore'

    print('Running %s' % ' '.join(args))
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    streams = tuple(s.decode('latin1').strip() for s in p.communicate())
    print('STDOUT:')
    print(streams[0])
    print('STDERR:')
    print(streams[1])
    return (streams) + (p.returncode,)


def config_git():
    run_cmd(
        ['git', 'config', '--global', 'user.email', 'example@example.com'],
        None,
    )
    run_cmd(
        ['git', 'config', '--global', 'user.name', 'OpenStack Developer'], None
    )
    run_cmd(
        [
            'git',
            'config',
            '--global',
            'user.signingkey',
            'example@example.com',
        ],
        None,
    )
