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
from __future__ import print_function

import email.errors
import os
import re
import sys
import tempfile

import fixtures
import testscenarios
from testtools import matchers

from pbr import packaging
from pbr.tests import base
from pbr.tests import fixtures as pbr_fixtures

if sys.version_info >= (3, 3):
    from unittest import mock
else:
    import mock  # noqa


class ParseRequirementsTest(base.BaseTestCase):

    def test_empty_requirements(self):
        actual = packaging.parse_requirements([])
        self.assertEqual([], actual)

    def test_default_requirements(self):
        """Ensure default files used if no files provided."""
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        with open(requirements, 'w') as f:
            f.write('pbr')
        # the defaults are relative to where pbr is called from so we need to
        # override them. This is OK, however, as we want to validate that
        # defaults are used - not what those defaults are
        with mock.patch.object(
            packaging, 'REQUIREMENTS_FILES', (requirements,)
        ):
            result = packaging.parse_requirements()
        self.assertEqual(['pbr'], result)

    def test_override_with_env(self):
        """Ensure environment variable used if no files provided."""
        _, tmp_file = tempfile.mkstemp(prefix='openstack', suffix='.setup')
        with open(tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.useFixture(
            fixtures.EnvironmentVariable('PBR_REQUIREMENTS_FILES', tmp_file)
        )
        self.assertEqual(['foo', 'bar'], packaging.parse_requirements())

    def test_override_with_env_multiple_files(self):
        _, tmp_file = tempfile.mkstemp(prefix='openstack', suffix='.setup')
        with open(tmp_file, 'w') as fh:
            fh.write("foo\nbar")
        self.useFixture(
            fixtures.EnvironmentVariable(
                'PBR_REQUIREMENTS_FILES', "no-such-file," + tmp_file
            )
        )
        self.assertEqual(['foo', 'bar'], packaging.parse_requirements())

    def test_index_present(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        with open(requirements, 'w') as f:
            f.write('-i https://myindex.local\n')
            f.write('  --index-url https://myindex.local\n')
            f.write(' --extra-index-url https://myindex.local\n')
            f.write('--find-links https://myindex.local\n')
            f.write('arequirement>=1.0\n')
        result = packaging.parse_requirements([requirements])
        self.assertEqual(['arequirement>=1.0'], result)

    def test_nested_requirements(self):
        tempdir = tempfile.mkdtemp()
        requirements = os.path.join(tempdir, 'requirements.txt')
        nested = os.path.join(tempdir, 'nested.txt')
        with open(requirements, 'w') as f:
            f.write('-r ' + nested)
        with open(nested, 'w') as f:
            f.write('pbr')
        result = packaging.parse_requirements([requirements])
        self.assertEqual(['pbr'], result)


class ParseRequirementsTestScenarios(base.BaseTestCase):

    versioned_scenarios = [
        ('non-versioned', {'versioned': False, 'expected': ['bar']}),
        ('versioned', {'versioned': True, 'expected': ['bar>=1.2.3']}),
    ]

    subdirectory_scenarios = [
        ('non-subdirectory', {'has_subdirectory': False}),
        ('has-subdirectory', {'has_subdirectory': True}),
    ]

    scenarios = [
        ('normal', {'url': "foo\nbar", 'expected': ['foo', 'bar']}),
        (
            'normal_with_comments',
            {
                'url': "# this is a comment\nfoo\n# and another one\nbar",
                'expected': ['foo', 'bar'],
            },
        ),
        ('removes_index_lines', {'url': '-f foobar', 'expected': []}),
    ]

    scenarios = scenarios + testscenarios.multiply_scenarios(
        [
            ('ssh_egg_url', {'url': 'git+ssh://foo.com/zipball#egg=bar'}),
            (
                'git_https_egg_url',
                {'url': 'git+https://foo.com/zipball#egg=bar'},
            ),
            ('http_egg_url', {'url': 'https://foo.com/zipball#egg=bar'}),
        ],
        versioned_scenarios,
        subdirectory_scenarios,
    )

    scenarios = scenarios + testscenarios.multiply_scenarios(
        [
            (
                'git_egg_url',
                {'url': 'git://foo.com/zipball#egg=bar', 'name': 'bar'},
            )
        ],
        [
            ('non-editable', {'editable': False}),
            ('editable', {'editable': True}),
        ],
        versioned_scenarios,
        subdirectory_scenarios,
    )

    def test_parse_requirements(self):
        tmp_file = tempfile.NamedTemporaryFile()
        req_string = self.url
        if hasattr(self, 'editable') and self.editable:
            req_string = "-e %s" % req_string
        if hasattr(self, 'versioned') and self.versioned:
            req_string = "%s-1.2.3" % req_string
        if hasattr(self, 'has_subdirectory') and self.has_subdirectory:
            req_string = "%s&subdirectory=baz" % req_string
        with open(tmp_file.name, 'w') as fh:
            fh.write(req_string)
        self.assertEqual(
            self.expected, packaging.parse_requirements([tmp_file.name])
        )


class ParseDependencyLinksTest(base.BaseTestCase):

    def setUp(self):
        super(ParseDependencyLinksTest, self).setUp()
        _, self.tmp_file = tempfile.mkstemp(
            prefix="openstack", suffix=".setup"
        )

    def test_parse_dependency_normal(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("http://test.com\n")
        self.assertEqual(
            ["http://test.com"],
            packaging.parse_dependency_links([self.tmp_file]),
        )

    def test_parse_dependency_with_git_egg_url(self):
        with open(self.tmp_file, "w") as fh:
            fh.write("-e git://foo.com/zipball#egg=bar")
        self.assertEqual(
            ["git://foo.com/zipball#egg=bar"],
            packaging.parse_dependency_links([self.tmp_file]),
        )


class TestVersions(base.BaseTestCase):

    scenarios = [
        ('preversioned', {'preversioned': True}),
        ('postversioned', {'preversioned': False}),
    ]

    def setUp(self):
        super(TestVersions, self).setUp()
        self.repo = self.useFixture(pbr_fixtures.GitRepo(self.package_dir))
        self.useFixture(pbr_fixtures.GPGKey())
        self.useFixture(pbr_fixtures.Chdir(self.package_dir))

    def tearDown(self):
        super(TestVersions, self).tearDown()
        os.environ.pop('SKIP_WRITE_GIT_CHANGELOG', None)

    def test_email_parsing_errors_are_handled(self):
        mocked_open = mock.mock_open()
        with mock.patch('pbr.packaging.open', mocked_open):
            with mock.patch('email.message_from_file') as message_from_file:
                message_from_file.side_effect = [
                    email.errors.MessageError('Test'),
                    {'Name': 'pbr_testpackage'},
                ]
                version = packaging._get_version_from_pkg_metadata(
                    'pbr_testpackage'
                )

        self.assertTrue(message_from_file.called)
        self.assertIsNone(version)

    def test_capitalized_headers(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('Sem-Ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_capitalized_headers_partial(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('Sem-ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_multi_inline_symbols_no_space(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('Sem-ver: feature,api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_multi_inline_symbols_spaced(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('Sem-ver: feature, api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_multi_inline_symbols_reversed(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('Sem-ver: api-break,feature')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_leading_space(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('   sem-ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_leading_space_multiline(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit(('   Some cool text\n   sem-ver: api-break'))
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_leading_characters_symbol_not_found(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('  ssem-ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.4.dev1'))

    def test_tagged_version_has_tag_version(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        version = packaging._get_version_from_git('1.2.3')
        self.assertEqual('1.2.3', version)

    def test_tagged_version_with_semver_compliant_prerelease(self):
        self.repo.commit()
        self.repo.tag('1.2.3-rc2')
        version = packaging._get_version_from_git()
        self.assertEqual('1.2.3.0rc2', version)

    def test_non_canonical_tagged_version_bump(self):
        self.repo.commit()
        self.repo.tag('1.4')
        self.repo.commit('Sem-Ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_untagged_version_has_dev_version_postversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.4.dev1'))

    def test_untagged_pre_release_has_pre_dev_version_postversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3.0a1')
        self.repo.commit()
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.3.0a2.dev1'))

    def test_untagged_version_minor_bump(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('sem-ver: deprecation')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.3.0.dev1'))

    def test_untagged_version_major_bump(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('sem-ver: api-break')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.0.dev1'))

    def test_untagged_version_has_dev_version_preversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        version = packaging._get_version_from_git('1.2.5')
        self.assertThat(version, matchers.StartsWith('1.2.5.dev1'))

    def test_untagged_version_after_pre_has_dev_version_preversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3.0a1')
        self.repo.commit()
        version = packaging._get_version_from_git('1.2.5')
        self.assertThat(version, matchers.StartsWith('1.2.5.dev1'))

    def test_untagged_version_after_rc_has_dev_version_preversion(self):
        self.repo.commit()
        self.repo.tag('1.2.3.0a1')
        self.repo.commit()
        version = packaging._get_version_from_git('1.2.3')
        self.assertThat(version, matchers.StartsWith('1.2.3.0a2.dev1'))

    def test_untagged_version_after_semver_compliant_prerelease_tag(self):
        self.repo.commit()
        self.repo.tag('1.2.3-rc2')
        self.repo.commit()
        version = packaging._get_version_from_git()
        self.assertEqual('1.2.3.0rc3.dev1', version)

    def test_preversion_too_low_simple(self):
        # That is, the target version is either already released or not high
        # enough for the semver requirements given api breaks etc.
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        # Note that we can't target 1.2.3 anymore - with 1.2.3 released we
        # need to be working on 1.2.4.
        err = self.assertRaises(
            ValueError, packaging._get_version_from_git, '1.2.3'
        )
        self.assertThat(err.args[0], matchers.StartsWith('git history'))

    def test_preversion_too_low_semver_headers(self):
        # That is, the target version is either already released or not high
        # enough for the semver requirements given api breaks etc.
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit('sem-ver: feature')
        # Note that we can't target 1.2.4, the feature header means we need
        # to be working on 1.3.0 or above.
        err = self.assertRaises(
            ValueError, packaging._get_version_from_git, '1.2.4'
        )
        self.assertThat(err.args[0], matchers.StartsWith('git history'))

    def test_get_kwargs_corner_cases(self):
        # No tags:

        def get_kwargs(tag):
            git_dir = self.repo._basedir + '/.git'
            return packaging._get_increment_kwargs(git_dir, tag)

        def _check_combinations(tag):
            self.repo.commit()
            self.assertEqual({}, get_kwargs(tag))
            self.repo.commit('sem-ver: bugfix')
            self.assertEqual({}, get_kwargs(tag))
            self.repo.commit('sem-ver: feature')
            self.assertEqual({'minor': True}, get_kwargs(tag))
            self.repo.uncommit()
            self.repo.commit('sem-ver: deprecation')
            self.assertEqual({'minor': True}, get_kwargs(tag))
            self.repo.uncommit()
            self.repo.commit('sem-ver: api-break')
            self.assertEqual({'major': True}, get_kwargs(tag))
            self.repo.commit('sem-ver: deprecation')
            self.assertEqual({'major': True, 'minor': True}, get_kwargs(tag))

        _check_combinations('')
        self.repo.tag('1.2.3')
        _check_combinations('1.2.3')

    def test_invalid_tag_ignored(self):
        # Fix for bug 1356784 - we treated any tag as a version, not just those
        # that are valid versions.
        self.repo.commit()
        self.repo.tag('1')
        self.repo.commit()
        # when the tree is tagged and its wrong:
        self.repo.tag('badver')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.0.1.dev1'))
        # When the tree isn't tagged, we also fall through.
        self.repo.commit()
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.0.1.dev2'))
        # We don't fall through x.y versions
        self.repo.commit()
        self.repo.tag('1.2')
        self.repo.commit()
        self.repo.tag('badver2')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.1.dev1'))
        # Or x.y.z versions
        self.repo.commit()
        self.repo.tag('1.2.3')
        self.repo.commit()
        self.repo.tag('badver3')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.4.dev1'))
        # Or alpha/beta/pre versions
        self.repo.commit()
        self.repo.tag('1.2.4.0a1')
        self.repo.commit()
        self.repo.tag('badver4')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('1.2.4.0a2.dev1'))
        # Non-release related tags are ignored.
        self.repo.commit()
        self.repo.tag('2')
        self.repo.commit()
        self.repo.tag('non-release-tag/2014.12.16-1')
        version = packaging._get_version_from_git()
        self.assertThat(version, matchers.StartsWith('2.0.1.dev1'))

    def test_valid_tag_honoured(self):
        # Fix for bug 1370608 - we converted any target into a 'dev version'
        # even if there was a distance of 0 - indicating that we were on the
        # tag itself.
        self.repo.commit()
        self.repo.tag('1.3.0.0a1')
        version = packaging._get_version_from_git()
        self.assertEqual('1.3.0.0a1', version)

    def test_skip_write_git_changelog(self):
        # Fix for bug 1467440
        self.repo.commit()
        self.repo.tag('1.2.3')
        os.environ['SKIP_WRITE_GIT_CHANGELOG'] = '1'
        version = packaging._get_version_from_git('1.2.3')
        self.assertEqual('1.2.3', version)


class TestRepositoryURLDependencies(base.BaseTestCase):

    def setUp(self):
        super(TestRepositoryURLDependencies, self).setUp()
        self.requirements = os.path.join(
            tempfile.mkdtemp(), 'requirements.txt'
        )
        with open(self.requirements, 'w') as f:
            f.write(
                '\n'.join(
                    [
                        '-e git+git://git.pro-ject.org/oslo.messaging#egg=oslo.messaging-1.0.0-rc',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize-beta',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-4.0.1',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-1.0.0-alpha.beta.1',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',  # noqa
                        '-e git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-2.0.0-rc.1+build.123',  # noqa
                        '-e git+git://git.project.org/Proj#egg=Proj1',
                        'git+https://git.project.org/Proj#egg=Proj2-0.0.1',
                        '-e git+ssh://git.project.org/Proj#egg=Proj3',
                        'svn+svn://svn.project.org/svn/Proj#egg=Proj4-0.0.2',
                        '-e svn+http://svn.project.org/svn/Proj/trunk@2019#egg=Proj5',
                        'hg+http://hg.project.org/Proj@da39a3ee5e6b#egg=Proj-0.0.3',
                        '-e hg+http://hg.project.org/Proj@2019#egg=Proj',
                        'hg+http://hg.project.org/Proj@v1.0#egg=Proj-0.0.4',
                        '-e hg+http://hg.project.org/Proj@special_feature#egg=Proj',
                        'git://foo.com/zipball#egg=foo-bar-1.2.4',
                        'pypi-proj1',
                        'pypi-proj2',
                    ]
                )
            )

    def test_egg_fragment(self):
        expected = [
            'django-thumborize',
            'django-thumborize-beta',
            'django-thumborize2-beta',
            'django-thumborize2-beta>=4.0.1',
            'django-thumborize2-beta>=1.0.0-alpha.beta.1',
            'django-thumborize2-beta>=1.0.0-alpha-a.b-c-long+build.1-aef.1-its-okay',  # noqa
            'django-thumborize2-beta>=2.0.0-rc.1+build.123',
            'django-thumborize-beta>=0.0.4',
            'django-thumborize-beta>=1.2.3',
            'django-thumborize-beta>=10.20.30',
            'django-thumborize-beta>=1.1.2-prerelease+meta',
            'django-thumborize-beta>=1.1.2+meta',
            'django-thumborize-beta>=1.1.2+meta-valid',
            'django-thumborize-beta>=1.0.0-alpha',
            'django-thumborize-beta>=1.0.0-beta',
            'django-thumborize-beta>=1.0.0-alpha.beta',
            'django-thumborize-beta>=1.0.0-alpha.beta.1',
            'django-thumborize-beta>=1.0.0-alpha.1',
            'django-thumborize-beta>=1.0.0-alpha0.valid',
            'django-thumborize-beta>=1.0.0-alpha.0valid',
            'django-thumborize-beta>=1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',  # noqa
            'django-thumborize-beta>=1.0.0-rc.1+build.1',
            'django-thumborize-beta>=2.0.0-rc.1+build.123',
            'django-thumborize-beta>=1.2.3-beta',
            'django-thumborize-beta>=10.2.3-DEV-SNAPSHOT',
            'django-thumborize-beta>=1.2.3-SNAPSHOT-123',
            'django-thumborize-beta>=1.0.0',
            'django-thumborize-beta>=2.0.0',
            'django-thumborize-beta>=1.1.7',
            'django-thumborize-beta>=2.0.0+build.1848',
            'django-thumborize-beta>=2.0.1-alpha.1227',
            'django-thumborize-beta>=1.0.0-alpha+beta',
            'django-thumborize-beta>=1.2.3----RC-SNAPSHOT.12.9.1--.12+788',
            'django-thumborize-beta>=1.2.3----R-S.12.9.1--.12+meta',
            'django-thumborize-beta>=1.2.3----RC-SNAPSHOT.12.9.1--.12',
            'django-thumborize-beta>=1.0.0+0.build.1-rc.10000aaa-kk-0.1',
            'django-thumborize-beta>=999999999999999999.99999999999999.9999999999999',  # noqa
            'Proj1',
            'Proj2>=0.0.1',
            'Proj3',
            'Proj4>=0.0.2',
            'Proj5',
            'Proj>=0.0.3',
            'Proj',
            'Proj>=0.0.4',
            'Proj',
            'foo-bar>=1.2.4',
        ]
        tests = [
            'egg=django-thumborize',
            'egg=django-thumborize-beta',
            'egg=django-thumborize2-beta',
            'egg=django-thumborize2-beta-4.0.1',
            'egg=django-thumborize2-beta-1.0.0-alpha.beta.1',
            'egg=django-thumborize2-beta-1.0.0-alpha-a.b-c-long+build.1-aef.1-its-okay',  # noqa
            'egg=django-thumborize2-beta-2.0.0-rc.1+build.123',
            'egg=django-thumborize-beta-0.0.4',
            'egg=django-thumborize-beta-1.2.3',
            'egg=django-thumborize-beta-10.20.30',
            'egg=django-thumborize-beta-1.1.2-prerelease+meta',
            'egg=django-thumborize-beta-1.1.2+meta',
            'egg=django-thumborize-beta-1.1.2+meta-valid',
            'egg=django-thumborize-beta-1.0.0-alpha',
            'egg=django-thumborize-beta-1.0.0-beta',
            'egg=django-thumborize-beta-1.0.0-alpha.beta',
            'egg=django-thumborize-beta-1.0.0-alpha.beta.1',
            'egg=django-thumborize-beta-1.0.0-alpha.1',
            'egg=django-thumborize-beta-1.0.0-alpha0.valid',
            'egg=django-thumborize-beta-1.0.0-alpha.0valid',
            'egg=django-thumborize-beta-1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',  # noqa
            'egg=django-thumborize-beta-1.0.0-rc.1+build.1',
            'egg=django-thumborize-beta-2.0.0-rc.1+build.123',
            'egg=django-thumborize-beta-1.2.3-beta',
            'egg=django-thumborize-beta-10.2.3-DEV-SNAPSHOT',
            'egg=django-thumborize-beta-1.2.3-SNAPSHOT-123',
            'egg=django-thumborize-beta-1.0.0',
            'egg=django-thumborize-beta-2.0.0',
            'egg=django-thumborize-beta-1.1.7',
            'egg=django-thumborize-beta-2.0.0+build.1848',
            'egg=django-thumborize-beta-2.0.1-alpha.1227',
            'egg=django-thumborize-beta-1.0.0-alpha+beta',
            'egg=django-thumborize-beta-1.2.3----RC-SNAPSHOT.12.9.1--.12+788',  # noqa
            'egg=django-thumborize-beta-1.2.3----R-S.12.9.1--.12+meta',
            'egg=django-thumborize-beta-1.2.3----RC-SNAPSHOT.12.9.1--.12',
            'egg=django-thumborize-beta-1.0.0+0.build.1-rc.10000aaa-kk-0.1',  # noqa
            'egg=django-thumborize-beta-999999999999999999.99999999999999.9999999999999',  # noqa
            'egg=Proj1',
            'egg=Proj2-0.0.1',
            'egg=Proj3',
            'egg=Proj4-0.0.2',
            'egg=Proj5',
            'egg=Proj-0.0.3',
            'egg=Proj',
            'egg=Proj-0.0.4',
            'egg=Proj',
            'egg=foo-bar-1.2.4',
        ]
        for index, test in enumerate(tests):
            self.assertEqual(
                expected[index],
                re.sub(r'egg=([^&]+).*$', packaging.egg_fragment, test),
            )

    def test_parse_repo_url_requirements(self):
        result = packaging.parse_requirements([self.requirements])
        self.assertEqual(
            [
                'oslo.messaging>=1.0.0-rc',
                'django-thumborize',
                'django-thumborize-beta',
                'django-thumborize2-beta',
                'django-thumborize2-beta>=4.0.1',
                'django-thumborize2-beta>=1.0.0-alpha.beta.1',
                'django-thumborize2-beta>=1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',  # noqa
                'django-thumborize2-beta>=2.0.0-rc.1+build.123',
                'Proj1',
                'Proj2>=0.0.1',
                'Proj3',
                'Proj4>=0.0.2',
                'Proj5',
                'Proj>=0.0.3',
                'Proj',
                'Proj>=0.0.4',
                'Proj',
                'foo-bar>=1.2.4',
                'pypi-proj1',
                'pypi-proj2',
            ],
            result,
        )

    def test_parse_repo_url_dependency_links(self):
        result = packaging.parse_dependency_links([self.requirements])
        self.assertEqual(
            [
                'git+git://git.pro-ject.org/oslo.messaging#egg=oslo.messaging-1.0.0-rc',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize-beta',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-4.0.1',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-1.0.0-alpha.beta.1',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay',  # noqa
                'git+git://git.pro-ject.org/django-thumborize#egg=django-thumborize2-beta-2.0.0-rc.1+build.123',  # noqa
                'git+git://git.project.org/Proj#egg=Proj1',
                'git+https://git.project.org/Proj#egg=Proj2-0.0.1',
                'git+ssh://git.project.org/Proj#egg=Proj3',
                'svn+svn://svn.project.org/svn/Proj#egg=Proj4-0.0.2',
                'svn+http://svn.project.org/svn/Proj/trunk@2019#egg=Proj5',
                'hg+http://hg.project.org/Proj@da39a3ee5e6b#egg=Proj-0.0.3',
                'hg+http://hg.project.org/Proj@2019#egg=Proj',
                'hg+http://hg.project.org/Proj@v1.0#egg=Proj-0.0.4',
                'hg+http://hg.project.org/Proj@special_feature#egg=Proj',
                'git://foo.com/zipball#egg=foo-bar-1.2.4',
            ],
            result,
        )
