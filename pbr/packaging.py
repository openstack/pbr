# Copyright 2011 OpenStack Foundation
# Copyright 2012-2013 Hewlett-Packard Development Company, L.P.
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

"""
Utilities with minimum-depends for use in setup.py
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import email
import email.errors
import os
import re
import sys
import warnings

from distutils import log

from pbr._compat.five import urlparse
import pbr._compat.packaging
from pbr import git
import pbr.pbr_json
from pbr import version

REQUIREMENTS_FILES = ('requirements.txt', 'tools/pip-requires')
PY_REQUIREMENTS_FILES = [
    x % sys.version_info[0]
    for x in ('requirements-py%d.txt', 'tools/pip-requires-py%d')
]
TEST_REQUIREMENTS_FILES = ('test-requirements.txt', 'tools/test-requires')


def get_requirements_files():
    files = os.environ.get("PBR_REQUIREMENTS_FILES")
    if files:
        return tuple(f.strip() for f in files.split(','))
    # Returns a list composed of:
    # - REQUIREMENTS_FILES with -py2 or -py3 in the name
    #   (e.g. requirements-py3.txt)
    # - REQUIREMENTS_FILES

    return PY_REQUIREMENTS_FILES + list(REQUIREMENTS_FILES)


def append_text_list(config, key, text_list):
    """Append a \n separated list to possibly existing value."""
    new_value = []
    current_value = config.get(key, "")
    if current_value:
        new_value.append(current_value)
    new_value.extend(text_list)
    config[key] = '\n'.join(new_value)


def _any_existing(file_list):
    return [f for f in file_list if os.path.exists(f)]


# Get requirements from the first file that exists
def get_reqs_from_files(requirements_files):
    existing = _any_existing(requirements_files)

    # TODO(stephenfin): Remove this in pbr 6.0+
    deprecated = [f for f in existing if f in PY_REQUIREMENTS_FILES]
    if deprecated:
        warnings.warn(
            'Support for \'-pyN\'-suffixed requirements files is '
            'removed in pbr 5.0 and these files are now ignored. '
            'Use environment markers instead. Conflicting files: '
            '%r' % deprecated,
            DeprecationWarning,
        )

    existing = [f for f in existing if f not in PY_REQUIREMENTS_FILES]
    for requirements_file in existing:
        with open(requirements_file, 'r') as fil:
            return fil.read().split('\n')

    return []


def egg_fragment(match):
    return re.sub(
        r'(?P<PackageName>[\w.-]+)-'
        r'(?P<GlobalVersion>'
        r'(?P<VersionTripple>'
        r'(?P<Major>0|[1-9][0-9]*)\.'
        r'(?P<Minor>0|[1-9][0-9]*)\.'
        r'(?P<Patch>0|[1-9][0-9]*)){1}'
        r'(?P<Tags>(?:\-'
        r'(?P<Prerelease>(?:(?=[0]{1}[0-9A-Za-z-]{0})(?:[0]{1})|'
        r'(?=[1-9]{1}[0-9]*[A-Za-z]{0})(?:[0-9]+)|'
        r'(?=[0-9]*[A-Za-z-]+[0-9A-Za-z-]*)(?:[0-9A-Za-z-]+)){1}'
        r'(?:\.(?=[0]{1}[0-9A-Za-z-]{0})(?:[0]{1})|'
        r'\.(?=[1-9]{1}[0-9]*[A-Za-z]{0})(?:[0-9]+)|'
        r'\.(?=[0-9]*[A-Za-z-]+[0-9A-Za-z-]*)'
        r'(?:[0-9A-Za-z-]+))*){1}){0,1}(?:\+'
        r'(?P<Meta>(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))){0,1}))',
        r'\g<PackageName>>=\g<GlobalVersion>',
        match.groups()[-1],
    )


def parse_requirements(requirements_files=None, strip_markers=False):
    if requirements_files is None:
        requirements_files = get_requirements_files()

    requirements = []
    for line in get_reqs_from_files(requirements_files):
        # Ignore comments
        if (not line.strip()) or line.startswith('#'):
            continue

        # Ignore index URL lines
        if re.match(
            r'^\s*(-i|--index-url|--extra-index-url|--find-links).*', line
        ):
            continue

        # Handle nested requirements files such as:
        # -r other-requirements.txt
        if line.startswith('-r'):
            req_file = line.partition(' ')[2]
            requirements += parse_requirements(
                [req_file], strip_markers=strip_markers
            )
            continue

        project_name = pbr._compat.packaging.extract_project_name(line)

        # For the requirements list, we need to inject only the portion
        # after egg= so that distutils knows the package it's looking for
        # such as:
        # -e git://github.com/openstack/nova/master#egg=nova
        # -e git://github.com/openstack/nova/master#egg=nova-1.2.3
        # -e git+https://foo.com/zipball#egg=bar&subdirectory=baz
        # http://github.com/openstack/nova/zipball/master#egg=nova
        # http://github.com/openstack/nova/zipball/master#egg=nova-1.2.3
        # git+https://foo.com/zipball#egg=bar&subdirectory=baz
        # git+[ssh]://github.com/openstack/nova/zipball/master#egg=nova-1.2.3
        # hg+[ssh]://github.com/openstack/nova/zipball/master#egg=nova-1.2.3
        # svn+[proto]://github.com/openstack/nova/zipball/master#egg=nova-1.2.3
        # -f lines are for index locations, and don't get used here
        if re.match(r'\s*-e\s+', line):
            extract = re.match(r'\s*-e\s+(.*)$', line)
            line = extract.group(1)
        egg = urlparse(line)
        if egg.scheme:
            line = re.sub(r'egg=([^&]+).*$', egg_fragment, egg.fragment)
        elif re.match(r'\s*-f\s+', line):
            line = None
            reason = 'Index Location'

        if line is not None:
            line = re.sub('#.*$', '', line)
            if strip_markers:
                semi_pos = line.find(';')
                if semi_pos < 0:
                    semi_pos = None
                line = line[:semi_pos]
            requirements.append(line)
        else:
            log.info('[pbr] Excluding %s: %s' % (project_name, reason))

    return requirements


def parse_dependency_links(requirements_files=None):
    if requirements_files is None:
        requirements_files = get_requirements_files()

    dependency_links = []
    # dependency_links inject alternate locations to find packages listed
    # in requirements
    for line in get_reqs_from_files(requirements_files):
        # skip comments and blank lines
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        # lines with -e or -f need the whole line, minus the flag
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))
        # lines that are only urls can go in unmolested
        elif re.match(r'^\s*(https?|git(\+(https|ssh))?|svn|hg)\S*:', line):
            dependency_links.append(line)
    return dependency_links


def _get_increment_kwargs(git_dir, tag):
    """Calculate the sort of semver increment needed from git history.

    Every commit from HEAD to tag is consider for Sem-Ver metadata lines.
    See the pbr docs for their syntax.

    :return: a dict of kwargs for passing into SemanticVersion.increment.
    """
    result = {}
    if tag:
        version_spec = tag + "..HEAD"
    else:
        version_spec = "HEAD"

    # Get the raw body of the commit messages so that we don't have to
    # parse out any formatting whitespace and to avoid user settings on
    # git log output affecting out ability to have working sem ver headers.
    changelog = git._run_git_command(
        ['log', '--pretty=%B', version_spec], git_dir
    )
    symbols = set()
    header = 'sem-ver:'
    for line in changelog.split("\n"):
        line = line.lower().strip()
        if not line.lower().strip().startswith(header):
            continue
        new_symbols = line[len(header) :].strip().split(",")
        symbols.update([symbol.strip() for symbol in new_symbols])

    def _handle_symbol(symbol, symbols, impact):
        if symbol in symbols:
            result[impact] = True
            symbols.discard(symbol)

    _handle_symbol('bugfix', symbols, 'patch')
    _handle_symbol('feature', symbols, 'minor')
    _handle_symbol('deprecation', symbols, 'minor')
    _handle_symbol('api-break', symbols, 'major')
    for symbol in symbols:
        log.info('[pbr] Unknown Sem-Ver symbol %r' % symbol)
    # We don't want patch in the kwargs since it is not a keyword argument -
    # its the default minimum increment.
    result.pop('patch', None)
    return result


def _get_revno_and_last_tag(git_dir):
    """Return the commit data about the most recent tag.

    We use git-describe to find this out, but if there are no
    tags then we fall back to counting commits since the beginning
    of time.
    """
    changelog = git._iter_log_oneline(git_dir=git_dir)
    row_count = 0
    for row_count, (ignored, tag_set, ignored) in enumerate(changelog):
        version_tags = set()
        semver_to_tag = {}
        for tag in list(tag_set):
            try:
                semver = version.SemanticVersion.from_pip_string(tag)
                semver_to_tag[semver] = tag
                version_tags.add(semver)
            except Exception:
                pass

        if version_tags:
            return semver_to_tag[max(version_tags)], row_count

    return "", row_count


def _get_version_from_git_target(git_dir, target_version):
    """Calculate a version from a target version in git_dir.

    This is used for untagged versions only. A new version is calculated as
    necessary based on git metadata - distance to tags, current hash, contents
    of commit messages.

    :param git_dir: The git directory we're working from.
    :param target_version: If None, the last tagged version (or 0 if there are
        no tags yet) is incremented as needed to produce an appropriate target
        version following semver rules. Otherwise target_version is used as a
        constraint - if semver rules would result in a newer version then an
        exception is raised.
    :return: A semver version object.
    """
    tag, distance = _get_revno_and_last_tag(git_dir)
    last_semver = version.SemanticVersion.from_pip_string(tag or '0')
    if distance == 0:
        new_version = last_semver
    else:
        new_version = last_semver.increment(
            **_get_increment_kwargs(git_dir, tag)
        )
    if target_version is not None and new_version > target_version:
        raise ValueError(
            "git history requires a target version of %(new)s, but target "
            "version is %(target)s"
            % {'new': new_version, 'target': target_version}
        )
    if distance == 0:
        return last_semver
    new_dev = new_version.to_dev(distance)
    if target_version is not None:
        target_dev = target_version.to_dev(distance)
        if target_dev > new_dev:
            return target_dev
    return new_dev


def _get_version_from_git(pre_version=None):
    """Calculate a version string from git.

    If the revision is tagged, return that. Otherwise calculate a semantic
    version description of the tree.

    The number of revisions since the last tag is included in the dev counter
    in the version for untagged versions.

    :param pre_version: If supplied use this as the target version rather than
        inferring one from the last tag + commit messages.
    """
    git_dir = git._run_git_functions()
    if git_dir:
        try:
            tagged = git._run_git_command(
                ['describe', '--exact-match'], git_dir, throw_on_error=True
            ).replace('-', '.')
            target_version = version.SemanticVersion.from_pip_string(tagged)
        except Exception:
            if pre_version:
                # not released yet - use pre_version as the target
                target_version = version.SemanticVersion.from_pip_string(
                    pre_version
                )
            else:
                # not released yet - just calculate from git history
                target_version = None
        result = _get_version_from_git_target(git_dir, target_version)
        return result.release_string()
    # If we don't know the version, return an empty string so at least
    # the downstream users of the value always have the same type of
    # object to work with.
    try:
        return unicode()
    except NameError:
        return ''


def _get_version_from_pkg_metadata(package_name):
    """Get the version from package metadata if present.

    This looks for PKG-INFO if present (for sdists), and if not looks
    for METADATA (for wheels) and failing that will return None.
    """
    pkg_metadata_filenames = ['PKG-INFO', 'METADATA']
    pkg_metadata = {}
    for filename in pkg_metadata_filenames:
        try:
            with open(filename, 'r') as pkg_metadata_file:
                pkg_metadata = email.message_from_file(pkg_metadata_file)
        except (IOError, OSError, email.errors.MessageError):
            continue

    # Check to make sure we're in our own dir
    if pkg_metadata.get('Name', None) != package_name:
        return None
    return pkg_metadata.get('Version', None)


def get_version(package_name, pre_version=None):
    """Get the version of the project.

    First, try getting it from PKG-INFO or METADATA, if it exists. If it does,
    that means we're in a distribution tarball or that install has happened.
    Otherwise, if there is no PKG-INFO or METADATA file, pull the version
    from git.

    We do not support setup.py version sanity in git archive tarballs, nor do
    we support packagers directly sucking our git repo into theirs. We expect
    that a source tarball be made from our git repo - or that if someone wants
    to make a source tarball from a fork of our repo with additional tags in it
    that they understand and desire the results of doing that.

    :param pre_version: The version field from setup.cfg - if set then this
        version will be the next release.
    """
    version = os.environ.get(
        "PBR_VERSION", os.environ.get("OSLO_PACKAGE_VERSION", None)
    )
    if version:
        return version
    version = _get_version_from_pkg_metadata(package_name)
    if version:
        return version
    version = _get_version_from_git(pre_version)
    # Handle http://bugs.python.org/issue11638
    # version will either be an empty unicode string or a valid
    # unicode version string, but either way it's unicode and needs to
    # be encoded.
    if sys.version_info[0] == 2:
        version = version.encode('utf-8')
    if version:
        return version
    raise Exception(
        "Versioning for this project requires either an sdist "
        "tarball, or access to an upstream git repository. "
        "It's also possible that there is a mismatch between "
        "the package name in setup.cfg and the argument given "
        "to pbr.version.VersionInfo. Project name {name} was "
        "given, but was not able to be found.".format(name=package_name)
    )


# This is added because pbr uses pbr to install itself. That means that
# any changes to the egg info writer entrypoints must be forward and
# backward compatible. This maintains the pbr.packaging.write_pbr_json
# path.
write_pbr_json = pbr.pbr_json.write_pbr_json
