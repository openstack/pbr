# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

import os
import StringIO
import sys
import tempfile

import fixtures

from pbr import packaging
from pbr.tests import utils


class DiveDir(fixtures.Fixture):
    """Dive into given directory and return back on cleanup.

    :ivar path: The target directory.
    """

    def __init__(self, path):
        self.path = path

    def setUp(self):
        super(DiveDir, self).setUp()
        self.old_path = os.getcwd()
        os.chdir(self.path)
        self.addCleanup(os.chdir, self.old_path)


class EmailTestCase(utils.BaseTestCase):

    def test_str_dict_replace(self):
        string = 'Johnnie T. Hozer'
        mapping = {'T.': 'The'}
        self.assertEqual('Johnnie The Hozer',
                         packaging.canonicalize_emails(string, mapping))


class MailmapTestCase(utils.BaseTestCase):

    def setUp(self):
        super(MailmapTestCase, self).setUp()
        self.git_dir = self.useFixture(fixtures.TempDir()).path
        self.mailmap = os.path.join(self.git_dir, '.mailmap')

    def test_mailmap_with_fullname(self):
        print self.mailmap, self.git_dir
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("Foo Bar <email@foo.com> Foo Bar <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.git_dir))

    def test_mailmap_with_firstname(self):
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("Foo <email@foo.com> Foo <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.git_dir))

    def test_mailmap_with_noname(self):
        with open(self.mailmap, 'w') as mm_fh:
            mm_fh.write("<email@foo.com> <email@bar.com>\n")
        self.assertEqual({'<email@bar.com>': '<email@foo.com>'},
                         packaging.read_git_mailmap(self.git_dir))


class GitLogsTest(utils.BaseTestCase):

    def setUp(self):
        super(GitLogsTest, self).setUp()
        self.temp_path = self.useFixture(fixtures.TempDir()).path
        self.root_dir = os.path.abspath(os.path.curdir)
        self.git_dir = os.path.join(self.root_dir, ".git")

    def test_write_git_changelog(self):
        exist_files = [os.path.join(self.root_dir, f)
                       for f in ".git", ".mailmap"]
        self.useFixture(fixtures.MonkeyPatch(
            "os.path.exists",
            lambda path: os.path.abspath(path) in exist_files))
        self.useFixture(fixtures.FakePopen(lambda _: {
            "stdout": StringIO.StringIO("Author: Foo Bar <email@bar.com>\n")
        }))

        def _fake_read_git_mailmap(*args):
            return {"email@bar.com": "email@foo.com"}

        self.useFixture(fixtures.MonkeyPatch("pbr.packaging.read_git_mailmap",
                                             _fake_read_git_mailmap))

        packaging.write_git_changelog(git_dir=self.git_dir,
                                      dest_dir=self.temp_path)

        with open(os.path.join(self.temp_path, "ChangeLog"), "r") as ch_fh:
            self.assertTrue("email@foo.com" in ch_fh.read())

    def _fake_log_output(self, cmd, mapping):
        for (k, v) in mapping.items():
            if cmd.startswith(k):
                return v
        return ""

    def test_generate_authors(self):
        author_old = "Foo Foo <email@foo.com>"
        author_new = "Bar Bar <email@bar.com>"
        co_author = "Foo Bar <foo@bar.com>"
        co_author_by = "Co-authored-by: " + co_author

        git_log_cmd = ("git --git-dir=%s log --format" % self.git_dir)
        git_co_log_cmd = ("git log --git-dir=%s" % self.git_dir)
        cmd_map = {
            git_log_cmd: author_new,
            git_co_log_cmd: co_author_by,
        }

        exist_files = [self.git_dir,
                       os.path.join(self.temp_path, "AUTHORS.in")]
        self.useFixture(fixtures.MonkeyPatch(
            "os.path.exists",
            lambda path: os.path.abspath(path) in exist_files))

        self.useFixture(fixtures.FakePopen(lambda proc_args: {
            "stdout": StringIO.StringIO(
                self._fake_log_output(proc_args["args"][2], cmd_map))
        }))

        with open(os.path.join(self.temp_path, "AUTHORS.in"), "w") as auth_fh:
            auth_fh.write("%s\n" % author_old)

        packaging.generate_authors(git_dir=self.git_dir,
                                   dest_dir=self.temp_path)

        with open(os.path.join(self.temp_path, "AUTHORS"), "r") as auth_fh:
            authors = auth_fh.read()
            self.assertTrue(author_old in authors)
            self.assertTrue(author_new in authors)
            self.assertTrue(co_author in authors)


class BuildSphinxTest(utils.BaseTestCase):

    def test_build_sphinx(self):

        self.useFixture(fixtures.MonkeyPatch(
            "sphinx.setup_command.BuildDoc.run", lambda self: None))
        from distutils import dist
        distr = dist.Distribution()
        distr.packages = ("fake_package",)
        distr.command_options["build_sphinx"] = {"source_dir": ["a", "."]}
        pkg_fixture = fixtures.PythonPackage(
            "fake_package", [("fake_module.py", "")])
        self.useFixture(pkg_fixture)
        self.useFixture(DiveDir(pkg_fixture.base))

        build_doc = packaging.LocalBuildDoc(distr)
        build_doc.run()

        self.assertTrue(
            os.path.exists("api/autoindex.rst"))
        self.assertTrue(
            os.path.exists("api/fake_package.fake_module.rst"))


class ParseRequirementsTest(utils.BaseTestCase):

    def setUp(self):
        super(ParseRequirementsTest, self).setUp()
        (fd, self.tmp_file) = tempfile.mkstemp(prefix='openstack',
                                               suffix='.setup')

    def test_parse_requirements_normal(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.assertEqual(['foo', 'bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_git_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("-e git://foo.com/zipball#egg=bar")
        self.assertEqual(['bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_with_http_egg_url(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("https://foo.com/zipball#egg=bar")
        self.assertEqual(['bar'],
                         packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_removes_index_lines(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("-f foobar")
        self.assertEqual([], packaging.parse_requirements([self.tmp_file]))

    def test_parse_requirements_removes_argparse(self):
        with open(self.tmp_file, 'w') as fh:
            fh.write("argparse")
        if sys.version_info >= (2, 7):
            self.assertEqual([], packaging.parse_requirements([self.tmp_file]))

    def test_get_requirement_from_file_empty(self):
        actual = packaging.get_reqs_from_files([])
        self.assertEqual([], actual)


class ParseDependencyLinksTest(utils.BaseTestCase):

    def setUp(self):
        super(ParseDependencyLinksTest, self).setUp()
        (fd, self.tmp_file) = tempfile.mkstemp(prefix="openstack",
                                               suffix=".setup")

    def test_parse_dependency_normal(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("http://test.com\n")
        self.assertEqual(
            ["http://test.com"],
            packaging.parse_dependency_links([self.tmp_file]))

    def test_parse_dependency_with_git_egg_url(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("-e git://foo.com/zipball#egg=bar")
        self.assertEqual(
            ["git://foo.com/zipball#egg=bar"],
            packaging.parse_dependency_links([self.tmp_file]))
