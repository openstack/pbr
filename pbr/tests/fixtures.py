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

from __future__ import absolute_import

import os
import re
import subprocess
import textwrap

import fixtures
from testtools import content
import virtualenv

from pbr.tests import util

PBR_ROOT = os.path.abspath(os.path.join(__file__, '..', '..', '..'))


class Chdir(fixtures.Fixture):
    """Dive into given directory and return back on cleanup.

    :ivar path: The target directory.
    """

    def __init__(self, path):
        self.path = path

    def setUp(self):
        super(Chdir, self).setUp()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.path)


class CapturedSubprocess(fixtures.Fixture):
    """Run a process and capture its output.

    :attr stdout: The output (a string). Only set if the process fails.
    :attr stderr: The standard error (a string). Only set if the process fails.
    :attr returncode: The return code of the process.

    Note that stdout and stderr are decoded from the bytestrings subprocess
    returns using error=replace
    """

    def __init__(self, label, *args, **kwargs):
        """Create a CapturedSubprocess.

        :param label: A label for the subprocess in the test log. E.g. 'foo'.
        :param *args: The *args to pass to Popen.
        :param **kwargs: The **kwargs to pass to Popen.
        """
        super(CapturedSubprocess, self).__init__()
        self.label = label
        self.args = args
        self.kwargs = kwargs
        self.kwargs['stderr'] = subprocess.PIPE
        self.kwargs['stdin'] = subprocess.PIPE
        self.kwargs['stdout'] = subprocess.PIPE

    def setUp(self):
        super(CapturedSubprocess, self).setUp()
        # setuptools can be very shouty
        env = os.environ.copy()
        env['PYTHONWARNINGS'] = 'ignore'
        self.kwargs['env'] = env
        proc = subprocess.Popen(*self.args, **self.kwargs)
        out, err = proc.communicate()
        self.out = out.decode('utf-8', 'replace')
        self.err = err.decode('utf-8', 'replace')
        self.addDetail(self.label + '-stdout', content.text_content(self.out))
        self.addDetail(self.label + '-stderr', content.text_content(self.err))
        self.returncode = proc.returncode
        if proc.returncode:
            raise AssertionError(
                'Failed process args=%r, kwargs=%r, returncode=%s'
                % (self.args, self.kwargs, proc.returncode)
            )
        self.addCleanup(delattr, self, 'out')
        self.addCleanup(delattr, self, 'err')
        self.addCleanup(delattr, self, 'returncode')


class GitRepo(fixtures.Fixture):
    """A git repo for testing with.

    Use of TempHomeDir with this fixture is strongly recommended as due to the
    lack of config --local in older gits, it will write to the users global
    configuration without TempHomeDir.
    """

    def __init__(self, basedir):
        super(GitRepo, self).__init__()
        self._basedir = basedir

    def setUp(self):
        super(GitRepo, self).setUp()
        util.run_cmd(['git', 'init', '.'], self._basedir)
        util.config_git()
        util.run_cmd(['git', 'add', '.'], self._basedir)

    def commit(self, message_content='test commit'):
        files = len(os.listdir(self._basedir))
        path = self._basedir + '/%d' % files
        open(path, 'wt').close()
        util.run_cmd(['git', 'add', path], self._basedir)
        util.run_cmd(['git', 'commit', '-m', message_content], self._basedir)

    def uncommit(self):
        util.run_cmd(['git', 'reset', '--hard', 'HEAD^'], self._basedir)

    def tag(self, version):
        util.run_cmd(['git', 'tag', '-sm', 'test tag', version], self._basedir)


class GPGKey(fixtures.Fixture):
    """Creates a GPG key for testing.

    It's recommended that this be used in concert with a unique home
    directory.
    """

    def setUp(self):
        super(GPGKey, self).setUp()
        # If a temporary home dir is in use (and it should be), ensure gpg is
        # aware of it. This seems to be necessary on Fedora.
        self.useFixture(
            fixtures.EnvironmentVariable('GNUPGHOME', os.getenv('HOME'))
        )
        tempdir = self.useFixture(fixtures.TempDir())
        gnupg_version_re = re.compile(r'^gpg\s.*\s([\d+])\.([\d+])\.([\d+])')
        gnupg_version = util.run_cmd(['gpg', '--version'], tempdir.path)
        for line in gnupg_version[0].split('\n'):
            gnupg_version = gnupg_version_re.match(line)
            if gnupg_version:
                gnupg_version = (
                    int(gnupg_version.group(1)),
                    int(gnupg_version.group(2)),
                    int(gnupg_version.group(3)),
                )
                break
        else:
            if gnupg_version is None:
                gnupg_version = (0, 0, 0)

        config_file = os.path.join(tempdir.path, 'key-config')
        with open(config_file, 'wt') as f:
            if gnupg_version[0] == 2 and gnupg_version[1] >= 1:
                f.write(
                    """
                %no-protection
                %transient-key
                """
                )
            f.write(
                """
            %no-ask-passphrase
            Key-Type: RSA
            Name-Real: Example Key
            Name-Comment: N/A
            Name-Email: example@example.com
            Expire-Date: 2d
            %commit
            """
            )

        # Note that --quick-random (--debug-quick-random in GnuPG 2.x)
        # does not have a corresponding preferences file setting and
        # must be passed explicitly on the command line instead
        if gnupg_version[0] == 1:
            gnupg_random = '--quick-random'
        elif gnupg_version[0] >= 2:
            gnupg_random = '--debug-quick-random'
        else:
            gnupg_random = ''

        _, _, retcode = util.run_cmd(
            ['gpg', '--gen-key', '--batch', gnupg_random, config_file],
            tempdir.path,
        )
        assert retcode == 0, 'gpg key generation failed!'


class Venv(fixtures.Fixture):
    """Create a virtual environment for testing with.

    :attr path: The path to the environment root.
    :attr python: The path to the python binary in the environment.
    """

    def __init__(self, reason, modules=(), pip_cmd=None):
        """Create a Venv fixture.

        :param reason: A human readable string to bake into the venv
            file path to aid diagnostics in the case of failures.
        :param modules: A list of modules to install, defaults to latest
            pip, wheel, and the working copy of PBR.
        :attr pip_cmd: A list to override the default pip_cmd passed to
            python for installing base packages.
        """
        self._reason = reason
        if modules == ():
            modules = ['pip', 'wheel', 'build', 'setuptools', PBR_ROOT]
        self.modules = modules
        if pip_cmd is None:
            self.pip_cmd = ['-m', 'pip', '-v', 'install']
        else:
            self.pip_cmd = pip_cmd

    def _setUp(self):
        path = self.useFixture(fixtures.TempDir()).path
        virtualenv.cli_run([path])

        python = os.path.join(path, 'bin', 'python')
        command = [python] + self.pip_cmd + ['-U']
        if self.modules and len(self.modules) > 0:
            command.extend(self.modules)
            self.useFixture(
                CapturedSubprocess('mkvenv-' + self._reason, command)
            )
        self.addCleanup(delattr, self, 'path')
        self.addCleanup(delattr, self, 'python')
        self.path = path
        self.python = python
        return path, python


class Packages(fixtures.Fixture):
    """Creates packages from dict with defaults

    :param package_dirs: A dict of package name to directory strings
    {'pkg_a': '/tmp/path/to/tmp/pkg_a', 'pkg_b': '/tmp/path/to/tmp/pkg_b'}
    """

    defaults = {
        'setup.py': textwrap.dedent(
            u"""\
            #!/usr/bin/env python
            import setuptools
            setuptools.setup(
                setup_requires=['pbr'],
                pbr=True,
            )
        """
        ),
        'setup.cfg': textwrap.dedent(
            u"""\
            [metadata]
            name = {pkg_name}
        """
        ),
    }

    def __init__(self, packages):
        """Creates packages from dict with defaults

        :param packages: a dict where the keys are the package name and a
        value that is a second dict that may be empty, containing keys of
        filenames and a string value of the contents.
        {'package-a': {'requirements.txt': 'string', 'setup.cfg': 'string'}
        """
        self.packages = packages

    def _writeFile(self, directory, file_name, contents):
        path = os.path.abspath(os.path.join(directory, file_name))
        path_dir = os.path.dirname(path)
        if not os.path.exists(path_dir):
            if path_dir.startswith(directory):
                os.makedirs(path_dir)
            else:
                raise ValueError
        with open(path, 'wt') as f:
            f.write(contents)

    def _setUp(self):
        tmpdir = self.useFixture(fixtures.TempDir()).path
        package_dirs = {}
        for pkg_name in self.packages:
            pkg_path = os.path.join(tmpdir, pkg_name)
            package_dirs[pkg_name] = pkg_path
            os.mkdir(pkg_path)
            for cf in ['setup.py', 'setup.cfg']:
                if cf in self.packages[pkg_name]:
                    contents = self.packages[pkg_name].pop(cf)
                else:
                    contents = self.defaults[cf].format(pkg_name=pkg_name)
                self._writeFile(pkg_path, cf, contents)

            for cf in self.packages[pkg_name]:
                self._writeFile(pkg_path, cf, self.packages[pkg_name][cf])
            self.useFixture(GitRepo(pkg_path)).commit()
        self.addCleanup(delattr, self, 'package_dirs')
        self.package_dirs = package_dirs
        return package_dirs
