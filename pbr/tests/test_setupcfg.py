# -*- coding: utf-8 -*-
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P. (HP)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
from __future__ import print_function

import io
import os
import tempfile
import textwrap
import warnings

from pbr._compat.five import ConfigParser
from pbr import setupcfg
from pbr.tests import base


def config_from_ini(ini):
    config = {}
    ini = textwrap.dedent(ini)
    parser = ConfigParser()
    parser.read_file(io.StringIO(ini))
    for section in parser.sections():
        config[section] = dict(parser.items(section))
    return config


class TestBasics(base.BaseTestCase):

    def test_basics(self):
        self.maxDiff = None
        config_text = u"""
            [metadata]
            name = foo
            version = 1.0
            author = John Doe
            author_email = jd@example.com
            maintainer = Jim Burke
            maintainer_email = jb@example.com
            home_page = http://example.com
            summary = A foobar project.
            description = Hello, world. This is a long description.
            download_url = http://opendev.org/x/pbr
            classifier =
                Development Status :: 5 - Production/Stable
                Programming Language :: Python
            platform =
                any
            license = Apache 2.0
            requires_dist =
                Sphinx
                requests
            setup_requires_dist =
                docutils
            python_requires = >=3.6
            provides_dist =
                bax
            provides_extras =
                bar
            obsoletes_dist =
                baz

            [files]
            packages_root = src
            packages =
                foo
            package_data =
                "" = *.txt, *.rst
                foo = *.msg
            namespace_packages =
                hello
            data_files =
                bitmaps =
                    bm/b1.gif
                    bm/b2.gif
                config =
                    cfg/data.cfg
            scripts =
                scripts/hello-world.py
            modules =
                mod1

            [backwards_compat]
            zip_safe = true
            tests_require =
              fixtures
            dependency_links =
              https://example.com/mypackage/v1.2.3.zip#egg=mypackage-1.2.3
            include_package_data = true
            """
        expected = {
            'name': u'foo',
            'version': u'1.0',
            'author': u'John Doe',
            'author_email': u'jd@example.com',
            'maintainer': u'Jim Burke',
            'maintainer_email': u'jb@example.com',
            'url': u'http://example.com',
            'description': u'A foobar project.',
            'long_description': u'Hello, world. This is a long description.',
            'download_url': u'http://opendev.org/x/pbr',
            'classifiers': [
                u'Development Status :: 5 - Production/Stable',
                u'Programming Language :: Python',
            ],
            'platforms': [u'any'],
            'license': u'Apache 2.0',
            'install_requires': [
                u'Sphinx',
                u'requests',
            ],
            'setup_requires': [u'docutils'],
            'python_requires': u'>=3.6',
            'provides': [u'bax'],
            'provides_extras': [u'bar'],
            'obsoletes': [u'baz'],
            'extras_require': {},
            'package_dir': {'': u'src'},
            'packages': [u'foo'],
            'package_data': {
                '': ['*.txt,', '*.rst'],
                'foo': ['*.msg'],
            },
            'namespace_packages': [u'hello'],
            'data_files': [
                ('bitmaps', ['bm/b1.gif', 'bm/b2.gif']),
                ('config', ['cfg/data.cfg']),
            ],
            'scripts': [u'scripts/hello-world.py'],
            'py_modules': [u'mod1'],
            'zip_safe': True,
            'tests_require': [
                'fixtures',
            ],
            'dependency_links': [
                'https://example.com/mypackage/v1.2.3.zip#egg=mypackage-1.2.3',
            ],
            'include_package_data': True,
        }
        config = config_from_ini(config_text)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            actual = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertDictEqual(expected, actual)

        # split on colon to avoid having to repeat the entire string...
        warning_messages = set(str(x.message).split(':')[0] for x in w)
        for warning_message in (
            "The '[metadata] home_page' option is deprecated",
            "The '[metadata] summary' option is deprecated",
            "The '[metadata] classifier' option is deprecated",
            "The '[metadata] platform' option is deprecated",
            "The '[metadata] requires_dist' option is deprecated",
            "The '[metadata] setup_requires_dist' option is deprecated",
            "The '[metadata] python_requires' option is deprecated",
            # "The '[metadata] requires_python' option is deprecated",
            "The '[metadata] provides_dist' option is deprecated",
            "The '[metadata] provides_extras' option is deprecated",
            "The '[metadata] obsoletes_dist' option is deprecated",
            "The '[files] packages' option is deprecated",
            "The '[files] package_data' option is deprecated",
            "The '[files] namespace_packages' option is deprecated",
            "The '[files] data_files' option is deprecated",
            "The '[files] scripts' option is deprecated",
            "The '[files] modules' option is deprecated",
            "The '[backwards_compat] zip_safe' option is deprecated",
            "The '[backwards_compat] dependency_links' option is deprecated",
            "The '[backwards_compat] tests_require' option is deprecated",
            "The '[backwards_compat] include_package_data' option is deprecated",
        ):
            self.assertIn(warning_message, warning_messages)

    def test_bug_2120575(self):
        # check behavior with description, long_description (modern)
        config_text = u"""
            [metadata]
            name = foo
            description = A short package summary
            long_description = file: README.rst
        """
        expected = {
            'name': u'foo',
            'description': u'A short package summary',
            # long_description should *not* be set: setuptools will handle this
            # for us
            'extras_require': {},
            'install_requires': [],
        }
        config = config_from_ini(config_text)
        actual = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertDictEqual(expected, actual)

        readme = os.path.join(self.temp_dir, 'README.rst')
        with open(readme, 'w') as f:
            f.write('A longer summary from the README')

        # check behavior with description, description_file (semi-modern)
        config_text = (
            u"""
            [metadata]
            name = foo
            description = A short package summary
            description_file = %s
        """
            % readme
        )
        expected = {
            'name': u'foo',
            'description': u'A short package summary',
            'long_description': u'A longer summary from the README\n\n',
            'extras_require': {},
            'install_requires': [],
        }
        config = config_from_ini(config_text)
        actual = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertDictEqual(expected, actual)

        # check behavior with summary, long_description (old)
        config_text = (
            u"""
            [metadata]
            name = foo
            summary = A short package summary
            long_description = %s
        """
            % readme
        )
        expected = {
            'name': u'foo',
            'description': u'A short package summary',
            # long_description is retrieved by setuptools
            'extras_require': {},
            'install_requires': [],
        }
        config = config_from_ini(config_text)
        actual = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertDictEqual(expected, actual)

        # check behavior with summary, description_file (ancient)
        config_text = (
            u"""
            [metadata]
            name = foo
            summary = A short package summary
            description_file = %s
        """
            % readme
        )
        expected = {
            'name': u'foo',
            'description': u'A short package summary',
            'long_description': u'A longer summary from the README\n\n',
            'extras_require': {},
            'install_requires': [],
        }
        config = config_from_ini(config_text)
        actual = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertDictEqual(expected, actual)


class TestExtrasRequireParsingScenarios(base.BaseTestCase):

    scenarios = [
        (
            'simple_extras',
            {
                'config_text': u"""
                [extras]
                first =
                    foo
                    bar==1.0
                second =
                    baz>=3.2
                    foo
                """,
                'expected_extra_requires': {
                    'first': ['foo', 'bar==1.0'],
                    'second': ['baz>=3.2', 'foo'],
                    'test': ['requests-mock'],
                    "test:(python_version=='2.6')": ['ordereddict'],
                },
            },
        ),
        (
            'with_markers',
            {
                'config_text': u"""
                [extras]
                test =
                    foo:python_version=='2.6'
                    bar
                    baz<1.6 :python_version=='2.6'
                    zaz :python_version>'1.0'
                """,
                'expected_extra_requires': {
                    "test:(python_version=='2.6')": ['foo', 'baz<1.6'],
                    "test": ['bar', 'zaz'],
                },
            },
        ),
        (
            'no_extras',
            {
                'config_text': u"""
            [metadata]
            long_description = foo
            """,
                'expected_extra_requires': {},
            },
        ),
    ]

    def test_extras_parsing(self):
        config = config_from_ini(self.config_text)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)

        self.assertEqual(
            self.expected_extra_requires, kwargs['extras_require']
        )


class TestInvalidMarkers(base.BaseTestCase):

    def test_invalid_marker_raises_error(self):
        config = {'extras': {'test': "foo :bad_marker>'1.0'"}}
        self.assertRaises(
            SyntaxError, setupcfg.setup_cfg_to_setup_kwargs, config
        )


class TestMapFieldsParsingScenarios(base.BaseTestCase):

    scenarios = [
        (
            'simple_project_urls',
            {
                'config_text': u"""
                [metadata]
                project_urls =
                    Bug Tracker = https://bugs.launchpad.net/pbr/
                    Documentation = https://docs.openstack.org/pbr/
                    Source Code = https://opendev.org/openstack/pbr
                """,  # noqa: E501
                'expected_project_urls': {
                    'Bug Tracker': 'https://bugs.launchpad.net/pbr/',
                    'Documentation': 'https://docs.openstack.org/pbr/',
                    'Source Code': 'https://opendev.org/openstack/pbr',
                },
            },
        ),
        (
            'query_parameters',
            {
                'config_text': u"""
                [metadata]
                project_urls =
                    Bug Tracker = https://bugs.launchpad.net/pbr/?query=true
                    Documentation = https://docs.openstack.org/pbr/?foo=bar
                    Source Code = https://git.openstack.org/cgit/openstack-dev/pbr/commit/?id=hash
                """,  # noqa: E501
                'expected_project_urls': {
                    'Bug Tracker': 'https://bugs.launchpad.net/pbr/?query=true',
                    'Documentation': 'https://docs.openstack.org/pbr/?foo=bar',
                    'Source Code': 'https://git.openstack.org/cgit/openstack-dev/pbr/commit/?id=hash',  # noqa: E501
                },
            },
        ),
    ]

    def test_project_url_parsing(self):
        config = config_from_ini(self.config_text)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)

        self.assertEqual(self.expected_project_urls, kwargs['project_urls'])


class TestKeywordsParsingScenarios(base.BaseTestCase):

    scenarios = [
        (
            'keywords_list',
            {
                'config_text': u"""
                [metadata]
                keywords =
                    one
                    two
                    three
                """,  # noqa: E501
                'expected_keywords': ['one', 'two', 'three'],
            },
        ),
        (
            'inline_keywords',
            {
                'config_text': u"""
                [metadata]
                keywords = one, two, three
                """,  # noqa: E501
                'expected_keywords': ['one, two, three'],
            },
        ),
    ]

    def test_keywords_parsing(self):
        config = config_from_ini(self.config_text)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)

        self.assertEqual(self.expected_keywords, kwargs['keywords'])


class TestProvidesExtras(base.BaseTestCase):
    def test_provides_extras(self):
        ini = u"""
        [metadata]
        provides_extras = foo
                          bar
        """
        config = config_from_ini(ini)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertEqual(['foo', 'bar'], kwargs['provides_extras'])


class TestDataFilesParsing(base.BaseTestCase):

    scenarios = [
        (
            'data_files',
            {
                'config_text': u"""
            [files]
            data_files =
                'i like spaces/' =
                    'dir with space/file with spc 2'
                    'dir with space/file with spc 1'
            """,
                'data_files': [
                    (
                        'i like spaces/',
                        [
                            'dir with space/file with spc 2',
                            'dir with space/file with spc 1',
                        ],
                    )
                ],
            },
        )
    ]

    def test_handling_of_whitespace_in_data_files(self):
        config = config_from_ini(self.config_text)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)

        self.assertEqual(self.data_files, kwargs['data_files'])


class TestUTF8DescriptionFile(base.BaseTestCase):
    def test_utf8_description_file(self):
        _, path = tempfile.mkstemp()
        ini_template = u"""
        [metadata]
        description_file = %s
        """
        # Two \n's because pbr strips the file content and adds \n\n
        # This way we can use it directly as the assert comparison
        unicode_description = u'UTF8 description: é"…-ʃŋ\'\n\n'
        ini = ini_template % path
        with io.open(path, 'w', encoding='utf8') as f:
            f.write(unicode_description)
        config = config_from_ini(ini)
        kwargs = setupcfg.setup_cfg_to_setup_kwargs(config)
        self.assertEqual(unicode_description, kwargs['long_description'])
