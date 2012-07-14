# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2012 OpenStack LLC
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
Generation and consumption of versions based on git revisions and tags.
Versions are cached into a versioninfo file that is installed along with
package data.
"""

import datetime
import pkg_resources
import os

from pbr.util import run_shell_command


def _get_git_branchname():
    branch_ref = run_shell_command("git symbolic-ref -q HEAD")
    if branch_ref == "":
        _branch_name = "HEAD"
    else:
        _branch_name = branch_ref[len("refs/heads/"):]
    return _branch_name


def _get_git_current_tag():
    return run_shell_command("git tag --contains HEAD")


def _get_git_tag_info():
    return run_shell_command("git describe --tags")


def _get_git_next_version_suffix(branch_name):
    datestamp = datetime.datetime.now().strftime('%Y%m%d')
    if branch_name == 'milestone-proposed':
        revno_prefix = "r"
    else:
        revno_prefix = ""
    run_shell_command("git fetch origin +refs/meta/*:refs/remotes/meta/*")
    milestone_cmd = "git show meta/openstack/release:%s" % branch_name
    milestonever = run_shell_command(milestone_cmd)
    if not milestonever:
        milestonever = ""
    post_version = _get_git_post_version()
    # post version should look like:
    # 0.1.1.4.gcc9e28a
    # where the bit after the last . is the short sha, and the bit between
    # the last and second to last is the revno count
    (revno, sha) = post_version.split(".")[-2:]
    first_half = "%(milestonever)s~%(datestamp)s" % locals()
    second_half = "%(revno_prefix)s%(revno)s.%(sha)s" % locals()
    return ".".join((first_half, second_half))


def _get_git_post_version():
    current_tag = _get_git_current_tag()
    if current_tag is not None:
        return current_tag
    else:
        tag_info = _get_git_tag_info()
        if tag_info is None:
            base_version = "0.0"
            cmd = "git --no-pager log --oneline"
            out = run_shell_command(cmd)
            revno = len(out.split("\n"))
            sha = run_shell_command("git describe --always")
        else:
            tag_infos = tag_info.split("-")
            base_version = "-".join(tag_infos[:-2])
            (revno, sha) = tag_infos[-2:]
        return "%s.%s.%s" % (base_version, revno, sha)


def read_versioninfo(project):
    """Read the versioninfo file. If it doesn't exist, we're in a github
       zipball, and there's really no way to know what version we really
       are, but that should be ok, because the utility of that should be
       just about nil if this code path is in use in the first place."""
    versioninfo_path = os.path.join(project, 'versioninfo')
    if os.path.exists(versioninfo_path):
        with open(versioninfo_path, 'r') as vinfo:
            version = vinfo.read().strip()
    else:
        version = "0.0.0"
    return version


def write_versioninfo(project, version):
    """Write a simple file containing the version of the package."""
    open(os.path.join(project, 'versioninfo'), 'w').write("%s\n" % version)


def get_pre_version(projectname, base_version):
    """Return a version which is leading up to a version that will
       be released in the future."""
    if os.path.isdir('.git'):
        current_tag = _get_git_current_tag()
        if current_tag is not None:
            version = current_tag
        else:
            branch_name = os.getenv('BRANCHNAME',
                                    os.getenv('GERRIT_REFNAME',
                                              _get_git_branchname()))
            version_suffix = _get_git_next_version_suffix(branch_name)
            version = "%s~%s" % (base_version, version_suffix)
        write_versioninfo(projectname, version)
        return version
    else:
        version = read_versioninfo(projectname)
    return version


def get_post_version(projectname):
    """Return a version which is equal to the tag that's on the current
    revision if there is one, or tag plus number of additional revisions
    if the current revision has no tag."""

    if os.path.isdir('.git'):
        version = _get_git_post_version()
        write_versioninfo(projectname, version)
        return version
    return read_versioninfo(projectname)


class _deferred_version_string(object):
    """Internal helper class which provides delayed version calculation."""
    def __init__(self, version_info, prefix):
        self.version_info = version_info
        self.prefix = prefix

    def __str__(self):
        return "%s%s" % (self.prefix, self.version_info.version_string())

    def __repr__(self):
        return "%s%s" % (self.prefix, self.version_info.version_string())


class VersionInfo(object):

    def __init__(self, package, python_package=None, pre_version=None):
        """Object that understands versioning for a package
        :param package: name of the top level python namespace. For glance,
                        this would be "glance" for python-glanceclient, it
                        would be "glanceclient"
        :param python_package: optional name of the project name. For
                               glance this can be left unset. For
                               python-glanceclient, this would be
                               "python-glanceclient"
        :param pre_version: optional version that the project is working to
        """
        self.package = package
        if python_package is None:
            self.python_package = package
        else:
            self.python_package = python_package
        self.pre_version = pre_version
        self.version = None

    def _generate_version(self):
        """Defer to the setup routines for making a
        version from git."""
        if self.pre_version is None:
            return get_post_version(self.python_package)
        else:
            return get_pre_version(self.python_package, self.pre_version)

    def _newer_version(self, pending_version):
        """Check to see if we're working with a stale version or not.
        We expect a version string that either looks like:
          2012.2~f3~20120708.10.4426392
        which is an unreleased version of a pre-version, or:
          0.1.1.4.gcc9e28a
        which is an unreleased version of a post-version, or:
          0.1.1
        Which is a release and which should match tag.
        For now, if we have a date-embedded version, check to see if it's
        old, and if so re-generate. Otherwise, just deal with it.
        """
        try:
            version_date = int(self.version.split("~")[-1].split('.')[0])
            if version_date < int(datetime.date.today().strftime('%Y%m%d')):
                return self._generate_version()
            else:
                return pending_version
        except Exception:
            return pending_version

    def version_string_with_vcs(self, always=False):
        """Return the full version of the package including suffixes indicating
        VCS status.

        For instance, if we are working towards the 2012.2 release,
        canonical_version_string should return 2012.2 if this is a final
        release, or else something like 2012.2~f1~20120705.20 if it's not.

        :param always: if true, skip all version caching
        """
        if always:
            self.version = self._generate_version()

        if self.version is None:

            requirement = pkg_resources.Requirement.parse(self.python_package)
            versioninfo = "%s/versioninfo" % self.package
            try:
                raw_version = pkg_resources.resource_string(requirement,
                                                            versioninfo)
                self.version = self._newer_version(raw_version.strip())
            except (IOError, pkg_resources.DistributionNotFound):
                self.version = self._generate_version()

        return self.version

    def canonical_version_string(self, always=False):
        """Return the simple version of the package excluding any suffixes.

        For instance, if we are working towards the 2012.2 release,
        canonical_version_string should return 2012.2 in all cases.

        :param always: if true, skip all version caching
        """
        return self.version_string_with_vcs(always).split('~')[0]

    def version_string(self, always=False):
        """Return the base version of the package.

        For instance, if we are working towards the 2012.2 release,
        version_string should return 2012.2 if this is a final release, or
        2012.2-dev if it is not.

        :param always: if true, skip all version caching
        """
        version_parts = self.version_string_with_vcs(always).split('~')
        if len(version_parts) == 1:
            return version_parts[0]
        else:
            return '%s-dev' % (version_parts[0],)

    def deferred_version_string(self, prefix=""):
        """Generate an object which will expand in a string context to
        the results of version_string(). We do this so that don't
        call into pkg_resources every time we start up a program when
        passing version information into the CONF constructor, but
        rather only do the calculation when and if a version is requested
        """
        return _deferred_version_string(self, prefix)
