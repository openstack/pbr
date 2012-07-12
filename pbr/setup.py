# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import datetime
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
