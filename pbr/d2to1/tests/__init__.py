from __future__ import with_statement
import os
import shutil
import subprocess
import sys
import tempfile

import pkg_resources

from .util import rmtree, open_config


D2TO1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.pardir, os.pardir))


def fake_d2to1_dist():
    # Fake a d2to1 distribution from the d2to1 package that these tests reside
    # in and make sure it's active on the path with the appropriate entry
    # points installed

    class _FakeProvider(pkg_resources.EmptyProvider):
        """A fake metadata provider that does almost nothing except to return
        entry point metadata.
        """

        def has_metadata(self, name):
            return name == 'entry_points.txt'

        def get_metadata(self, name):
            if name == 'entry_points.txt':
                return '[distutils.setup_keywords]\nd2to1 = d2to1.core:d2to1\n'
            else:
                return ''


    sys.path.insert(0, D2TO1_DIR)
    if 'd2to1' in sys.modules:
        del sys.modules['d2to1']
    if 'd2to1' in pkg_resources.working_set.by_key:
        del pkg_resources.working_set.by_key['d2to1']
    dist = pkg_resources.Distribution(location=D2TO1_DIR, project_name='d2to1',
                                      metadata=_FakeProvider())
    pkg_resources.working_set.add(dist)


class D2to1TestCase(object):
    def setup(self):
        self.temp_dir = tempfile.mkdtemp(prefix='d2to1-test-')
        self.package_dir = os.path.join(self.temp_dir, 'testpackage')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'testpackage'),
                        self.package_dir)
        self.oldcwd = os.getcwd()
        os.chdir(self.package_dir)

    def teardown(self):
        os.chdir(self.oldcwd)
        # Remove d2to1.testpackage from sys.modules so that it can be freshly
        # re-imported by the next test
        for k in list(sys.modules):
            if (k == 'd2to1_testpackage' or
                k.startswith('d2to1_testpackage.')):
                del sys.modules[k]
        rmtree(self.temp_dir)

    def run_setup(self, *args):
        cmd = ('-c',
               'import sys;sys.path.insert(0, %r);'
               'from d2to1.tests import fake_d2to1_dist;'
               'fake_d2to1_dist();execfile("setup.py")' % D2TO1_DIR)
        return self._run_cmd(sys.executable, cmd + args)

    def run_svn(self, *args):
        return self._run_cmd('svn', args)

    def _run_cmd(self, cmd, args):
        """
        Runs a command, with the given argument list, in the root of the test
        working copy--returns the stdout and stderr streams and the exit code
        from the subprocess.
        """

        os.chdir(self.package_dir)
        p = subprocess.Popen([cmd] + list(args), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        streams = tuple(s.decode('latin1').strip() for s in p.communicate())
        return (streams) + (p.returncode,)
