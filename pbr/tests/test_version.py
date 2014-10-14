# Copyright 2012 Red Hat, Inc.
# Copyright 2012-2013 Hewlett-Packard Development Company, L.P.
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

import operator

from testtools import matchers

from pbr.tests import base
from pbr import version


from_pip_string = version.SemanticVersion.from_pip_string


class TestSemanticVersion(base.BaseTestCase):

    def test_equality(self):
        base = version.SemanticVersion(1, 2, 3)
        base2 = version.SemanticVersion(1, 2, 3)
        major = version.SemanticVersion(2, 2, 3)
        minor = version.SemanticVersion(1, 3, 3)
        patch = version.SemanticVersion(1, 2, 4)
        pre_base = version.SemanticVersion(1, 2, 3, 'a', 4)
        pre_base2 = version.SemanticVersion(1, 2, 3, 'a', 4)
        pre_type = version.SemanticVersion(1, 2, 3, 'b', 4)
        pre_serial = version.SemanticVersion(1, 2, 3, 'a', 5)
        dev_base = version.SemanticVersion(1, 2, 3, dev_count=6, githash='6')
        dev_base2 = version.SemanticVersion(1, 2, 3, dev_count=6, githash='6')
        dev_count = version.SemanticVersion(1, 2, 3, dev_count=7, githash='6')
        githash = version.SemanticVersion(1, 2, 3, dev_count=6, githash='7')
        self.assertEqual(base, base2)
        self.assertNotEqual(base, major)
        self.assertNotEqual(base, minor)
        self.assertNotEqual(base, patch)
        self.assertNotEqual(base, pre_type)
        self.assertNotEqual(base, pre_serial)
        self.assertNotEqual(base, dev_count)
        self.assertNotEqual(base, githash)
        self.assertEqual(pre_base, pre_base2)
        self.assertNotEqual(pre_base, pre_type)
        self.assertNotEqual(pre_base, pre_serial)
        self.assertNotEqual(pre_base, dev_count)
        self.assertNotEqual(pre_base, githash)
        self.assertEqual(dev_base, dev_base2)
        self.assertNotEqual(dev_base, dev_count)
        self.assertNotEqual(dev_base, githash)
        simple = version.SemanticVersion(1)
        explicit_minor = version.SemanticVersion(1, 0)
        explicit_patch = version.SemanticVersion(1, 0, 0)
        self.assertEqual(simple, explicit_minor)
        self.assertEqual(simple, explicit_patch)
        self.assertEqual(explicit_minor, explicit_patch)

    def test_ordering(self):
        base = version.SemanticVersion(1, 2, 3)
        major = version.SemanticVersion(2, 2, 3)
        minor = version.SemanticVersion(1, 3, 3)
        patch = version.SemanticVersion(1, 2, 4)
        pre_alpha = version.SemanticVersion(1, 2, 3, 'a', 4)
        pre_beta = version.SemanticVersion(1, 2, 3, 'b', 3)
        pre_rc = version.SemanticVersion(1, 2, 3, 'rc', 2)
        pre_serial = version.SemanticVersion(1, 2, 3, 'a', 5)
        dev_base = version.SemanticVersion(1, 2, 3, dev_count=6, githash='6')
        dev_count = version.SemanticVersion(1, 2, 3, dev_count=7, githash='6')
        githash = version.SemanticVersion(1, 2, 3, dev_count=6, githash='7')
        self.assertThat(base, matchers.LessThan(major))
        self.assertThat(major, matchers.GreaterThan(base))
        self.assertThat(base, matchers.LessThan(minor))
        self.assertThat(minor, matchers.GreaterThan(base))
        self.assertThat(base, matchers.LessThan(patch))
        self.assertThat(patch, matchers.GreaterThan(base))
        self.assertThat(pre_alpha, matchers.LessThan(base))
        self.assertThat(base, matchers.GreaterThan(pre_alpha))
        self.assertThat(pre_alpha, matchers.LessThan(pre_beta))
        self.assertThat(pre_beta, matchers.GreaterThan(pre_alpha))
        self.assertThat(pre_beta, matchers.LessThan(pre_rc))
        self.assertThat(pre_rc, matchers.GreaterThan(pre_beta))
        self.assertThat(pre_alpha, matchers.LessThan(pre_serial))
        self.assertThat(pre_serial, matchers.GreaterThan(pre_alpha))
        self.assertThat(pre_serial, matchers.LessThan(pre_beta))
        self.assertThat(pre_beta, matchers.GreaterThan(pre_serial))
        self.assertThat(dev_base, matchers.LessThan(base))
        self.assertThat(base, matchers.GreaterThan(dev_base))
        self.assertRaises(TypeError, operator.lt, pre_alpha, dev_base)
        self.assertRaises(TypeError, operator.lt, dev_base, pre_alpha)
        self.assertThat(dev_base, matchers.LessThan(dev_count))
        self.assertThat(dev_count, matchers.GreaterThan(dev_base))
        self.assertRaises(TypeError, operator.lt, dev_base, githash)

    def test_from_pip_string_legacy_alpha(self):
        expected = version.SemanticVersion(
            1, 2, 0, prerelease_type='rc', prerelease=1)
        parsed = from_pip_string('1.2.0rc1')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_nonzero_lead_in(self):
        # reported in bug 1361251
        expected = version.SemanticVersion(
            0, 0, 1, prerelease_type='a', prerelease=2)
        parsed = from_pip_string('0.0.1a2')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_short_nonzero_lead_in(self):
        expected = version.SemanticVersion(
            0, 1, 0, prerelease_type='a', prerelease=2)
        parsed = from_pip_string('0.1a2')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_no_0_prerelease(self):
        expected = version.SemanticVersion(
            2, 1, 0, prerelease_type='rc', prerelease=1)
        parsed = from_pip_string('2.1.0.rc1')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_no_0_prerelease_2(self):
        expected = version.SemanticVersion(
            2, 0, 0, prerelease_type='rc', prerelease=1)
        parsed = from_pip_string('2.0.0.rc1')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_non_440_beta(self):
        expected = version.SemanticVersion(
            2014, 2, prerelease_type='b', prerelease=2)
        parsed = from_pip_string('2014.2.b2')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_dev(self):
        expected = version.SemanticVersion(
            0, 10, 1, dev_count=3, githash='83bef74')
        parsed = from_pip_string('0.10.1.3.g83bef74')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_corner_case_dev(self):
        # If the last tag is missing, or if the last tag has less than 3
        # components, we need to 0 extend on parsing.
        expected = version.SemanticVersion(
            0, 0, 0, dev_count=1, githash='83bef74')
        parsed = from_pip_string('0.0.g83bef74')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_legacy_short_dev(self):
        # If the last tag is missing, or if the last tag has less than 3
        # components, we need to 0 extend on parsing.
        expected = version.SemanticVersion(
            0, 0, 0, dev_count=1, githash='83bef74')
        parsed = from_pip_string('0.g83bef74')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_dev_missing_patch_version(self):
        expected = version.SemanticVersion(
            2014, 2, dev_count=21, githash='c4c8d0b')
        parsed = from_pip_string('2014.2.dev21.gc4c8d0b')
        self.assertEqual(expected, parsed)

    def test_from_pip_string_pure_git_hash(self):
        self.assertRaises(ValueError, from_pip_string, '6eed5ae')

    def test_final_version(self):
        semver = version.SemanticVersion(1, 2, 3)
        self.assertEqual((1, 2, 3, 'final', 0), semver.version_tuple())
        self.assertEqual("1.2.3", semver.brief_string())
        self.assertEqual("1.2.3", semver.debian_string())
        self.assertEqual("1.2.3", semver.release_string())
        self.assertEqual("1.2.3", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.3"))

    def test_parsing_short_forms(self):
        semver = version.SemanticVersion(1, 0, 0)
        self.assertEqual(semver, from_pip_string("1"))
        self.assertEqual(semver, from_pip_string("1.0"))
        self.assertEqual(semver, from_pip_string("1.0.0"))

    def test_dev_version(self):
        semver = version.SemanticVersion(1, 2, 4, dev_count=5, githash='12')
        self.assertEqual((1, 2, 4, 'dev', 4), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~dev5+g12", semver.debian_string())
        self.assertEqual("1.2.4.dev5.g12", semver.release_string())
        self.assertEqual("1.2.3.dev5+g12", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.dev5.g12"))

    def test_dev_no_git_version(self):
        semver = version.SemanticVersion(1, 2, 4, dev_count=5)
        self.assertEqual((1, 2, 4, 'dev', 4), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~dev5", semver.debian_string())
        self.assertEqual("1.2.4.dev5", semver.release_string())
        self.assertEqual("1.2.3.dev5", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.dev5"))

    def test_dev_zero_version(self):
        semver = version.SemanticVersion(1, 2, 0, dev_count=5)
        self.assertEqual((1, 2, 0, 'dev', 4), semver.version_tuple())
        self.assertEqual("1.2.0", semver.brief_string())
        self.assertEqual("1.2.0~dev5", semver.debian_string())
        self.assertEqual("1.2.0.dev5", semver.release_string())
        self.assertEqual("1.1.9999.dev5", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.0.dev5"))

    def test_alpha_dev_version(self):
        self.assertRaises(
            ValueError, version.SemanticVersion, 1, 2, 4, 'a', 1, 5, '12')

    def test_alpha_version(self):
        semver = version.SemanticVersion(1, 2, 4, 'a', 1)
        self.assertEqual((1, 2, 4, 'alpha', 1), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~a1", semver.debian_string())
        self.assertEqual("1.2.4.0a1", semver.release_string())
        self.assertEqual("1.2.3.a1", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.0a1"))

    def test_alpha_zero_version(self):
        semver = version.SemanticVersion(1, 2, 0, 'a', 1)
        self.assertEqual((1, 2, 0, 'alpha', 1), semver.version_tuple())
        self.assertEqual("1.2.0", semver.brief_string())
        self.assertEqual("1.2.0~a1", semver.debian_string())
        self.assertEqual("1.2.0.0a1", semver.release_string())
        self.assertEqual("1.1.9999.a1", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.0.0a1"))

    def test_alpha_major_zero_version(self):
        semver = version.SemanticVersion(1, 0, 0, 'a', 1)
        self.assertEqual((1, 0, 0, 'alpha', 1), semver.version_tuple())
        self.assertEqual("1.0.0", semver.brief_string())
        self.assertEqual("1.0.0~a1", semver.debian_string())
        self.assertEqual("1.0.0.0a1", semver.release_string())
        self.assertEqual("0.9999.9999.a1", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.0.0.0a1"))

    def test_alpha_default_version(self):
        semver = version.SemanticVersion(1, 2, 4, 'a')
        self.assertEqual((1, 2, 4, 'alpha', 0), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~a0", semver.debian_string())
        self.assertEqual("1.2.4.0a0", semver.release_string())
        self.assertEqual("1.2.3.a0", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.0a0"))

    def test_beta_dev_version(self):
        self.assertRaises(
            ValueError, version.SemanticVersion, 1, 2, 4, 'b', 1, 5, '12')

    def test_beta_version(self):
        semver = version.SemanticVersion(1, 2, 4, 'b', 1)
        self.assertEqual((1, 2, 4, 'beta', 1), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~b1", semver.debian_string())
        self.assertEqual("1.2.4.0b1", semver.release_string())
        self.assertEqual("1.2.3.b1", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.0b1"))

    def test_decrement_nonrelease(self):
        # The prior version of any non-release is a release
        semver = version.SemanticVersion(1, 2, 4, 'b', 1)
        self.assertEqual(
            version.SemanticVersion(1, 2, 3), semver.decrement())

    def test_decrement_nonrelease_zero(self):
        # We set an arbitrary max version of 9999 when decrementing versions
        # - this is part of handling rpm support.
        semver = version.SemanticVersion(1, 0, 0)
        self.assertEqual(
            version.SemanticVersion(0, 9999, 9999), semver.decrement())

    def test_decrement_release(self):
        # The next patch version of a release version requires a change to the
        # patch level.
        semver = version.SemanticVersion(1, 2, 5)
        self.assertEqual(
            version.SemanticVersion(1, 2, 6), semver.increment())
        self.assertEqual(
            version.SemanticVersion(1, 3, 0), semver.increment(minor=True))
        self.assertEqual(
            version.SemanticVersion(2, 0, 0), semver.increment(major=True))

    def test_increment_nonrelease(self):
        # The next patch version of a non-release version is another
        # non-release version as the next release doesn't need to be
        # incremented.
        semver = version.SemanticVersion(1, 2, 4, 'b', 1)
        self.assertEqual(
            version.SemanticVersion(1, 2, 4, 'b', 2), semver.increment())
        # Major and minor increments however need to bump things.
        self.assertEqual(
            version.SemanticVersion(1, 3, 0), semver.increment(minor=True))
        self.assertEqual(
            version.SemanticVersion(2, 0, 0), semver.increment(major=True))

    def test_increment_release(self):
        # The next patch version of a release version requires a change to the
        # patch level.
        semver = version.SemanticVersion(1, 2, 5)
        self.assertEqual(
            version.SemanticVersion(1, 2, 6), semver.increment())
        self.assertEqual(
            version.SemanticVersion(1, 3, 0), semver.increment(minor=True))
        self.assertEqual(
            version.SemanticVersion(2, 0, 0), semver.increment(major=True))

    def test_rc_dev_version(self):
        self.assertRaises(
            ValueError, version.SemanticVersion, 1, 2, 4, 'rc', 1, 5, '12')

    def test_rc_version(self):
        semver = version.SemanticVersion(1, 2, 4, 'rc', 1)
        self.assertEqual((1, 2, 4, 'candidate', 1), semver.version_tuple())
        self.assertEqual("1.2.4", semver.brief_string())
        self.assertEqual("1.2.4~rc1", semver.debian_string())
        self.assertEqual("1.2.4.0rc1", semver.release_string())
        self.assertEqual("1.2.3.rc1", semver.rpm_string())
        self.assertEqual(semver, from_pip_string("1.2.4.0rc1"))

    def test_to_dev(self):
        self.assertEqual(
            version.SemanticVersion(1, 2, 3, dev_count=1, githash='foo'),
            version.SemanticVersion(1, 2, 3).to_dev(1, 'foo'))
        self.assertEqual(
            version.SemanticVersion(1, 2, 3, dev_count=1, githash='foo'),
            version.SemanticVersion(1, 2, 3, 'rc', 1).to_dev(1, 'foo'))

    def test_to_release(self):
        self.assertEqual(
            version.SemanticVersion(1, 2, 3),
            version.SemanticVersion(
                1, 2, 3, dev_count=1, githash='foo').to_release())
        self.assertEqual(
            version.SemanticVersion(1, 2, 3),
            version.SemanticVersion(1, 2, 3, 'rc', 1).to_release())
