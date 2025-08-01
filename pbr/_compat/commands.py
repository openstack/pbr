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

from __future__ import unicode_literals

from distutils.command import install as du_install
from distutils import log
import os
import sys

import setuptools
from setuptools.command import develop
from setuptools.command import easy_install
from setuptools.command import egg_info
from setuptools.command import install
from setuptools.command import install_scripts
from setuptools.command import sdist

from pbr import extra_files
from pbr import git
from pbr import options
from pbr import version

_wsgi_text = """#PBR Generated from %(group)r

import threading

from %(module_name)s import %(import_target)s

if __name__ == "__main__":
    import argparse
    import socket
    import sys
    import wsgiref.simple_server as wss

    parser = argparse.ArgumentParser(
        description=%(import_target)s.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage='%%(prog)s [-h] [--port PORT] [--host IP] -- [passed options]')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='TCP port to listen on')
    parser.add_argument('--host', '-b', default='',
                        help='IP to bind the server to')
    parser.add_argument('args',
                        nargs=argparse.REMAINDER,
                        metavar='-- [passed options]',
                        help="'--' is the separator of the arguments used "
                        "to start the WSGI server and the arguments passed "
                        "to the WSGI application.")
    args = parser.parse_args()
    if args.args:
        if args.args[0] == '--':
            args.args.pop(0)
        else:
            parser.error("unrecognized arguments: %%s" %% ' '.join(args.args))
    sys.argv[1:] = args.args
    server = wss.make_server(args.host, args.port, %(invoke_target)s())

    print("*" * 80)
    print("STARTING test server %(module_name)s.%(invoke_target)s")
    url = "http://%%s:%%d/" %% (server.server_name, server.server_port)
    print("Available at %%s" %% url)
    print("DANGER! For testing only, do not use in production")
    print("*" * 80)
    sys.stdout.flush()

    server.serve_forever()
else:
    application = None
    app_lock = threading.Lock()

    with app_lock:
        if application is None:
            application = %(invoke_target)s()

"""

_script_text = """# PBR Generated from %(group)r

import sys

from %(module_name)s import %(import_target)s


if __name__ == "__main__":
    sys.exit(%(invoke_target)s())
"""

# the following allows us to specify different templates per entry
# point group when generating pbr scripts.
ENTRY_POINTS_MAP = {
    'console_scripts': _script_text,
    'gui_scripts': _script_text,
    'wsgi_scripts': _wsgi_text,
}


def generate_script(group, entry_point, header, template):
    """Generate the script based on the template.

    :param str group: The entry-point group name, e.g., "console_scripts".
    :param str header: The first line of the script, e.g.,
        "!#/usr/bin/env python".
    :param str template: The script template.
    :returns: The templated script content
    :rtype: str
    """
    if not entry_point.attrs or len(entry_point.attrs) > 2:
        raise ValueError(
            "Script targets must be of the form "
            "'func' or 'Class.class_method'."
        )

    script_text = template % {
        'group': group,
        'module_name': entry_point.module_name,
        'import_target': entry_point.attrs[0],
        'invoke_target': '.'.join(entry_point.attrs),
    }
    return header + script_text


def override_get_script_args(
    dist, executable=os.path.normpath(sys.executable)
):
    """Override entrypoints console_script."""
    # get_script_header() is deprecated since Setuptools 12.0
    try:
        header = easy_install.ScriptWriter.get_header("", executable)
    except AttributeError:
        header = easy_install.get_script_header("", executable)
    for group, template in ENTRY_POINTS_MAP.items():
        for name, ep in dist.get_entry_map(group).items():
            yield (name, generate_script(group, ep, header, template))


class LocalDevelop(develop.develop):

    command_name = 'develop'

    def install_wrapper_scripts(self, dist):
        if sys.platform == 'win32':
            return develop.develop.install_wrapper_scripts(self, dist)
        if not self.exclude_scripts:
            for args in override_get_script_args(dist):
                self.write_script(*args)


class LocalInstallScripts(install_scripts.install_scripts):
    """Intercepts console scripts entry_points."""

    command_name = 'install_scripts'

    def _make_wsgi_scripts_only(self, dist, executable):
        # get_script_header() is deprecated since Setuptools 12.0
        try:
            header = easy_install.ScriptWriter.get_header("", executable)
        except AttributeError:
            header = easy_install.get_script_header("", executable)
        wsgi_script_template = ENTRY_POINTS_MAP['wsgi_scripts']
        for name, ep in dist.get_entry_map('wsgi_scripts').items():
            content = generate_script(
                'wsgi_scripts', ep, header, wsgi_script_template
            )
            self.write_script(name, content)

    def run(self):
        import distutils.command.install_scripts
        import pkg_resources

        self.run_command("egg_info")
        if self.distribution.scripts:
            # run first to set up self.outfiles
            distutils.command.install_scripts.install_scripts.run(self)
        else:
            self.outfiles = []

        ei_cmd = self.get_finalized_command("egg_info")
        dist = pkg_resources.Distribution(
            ei_cmd.egg_base,
            pkg_resources.PathMetadata(ei_cmd.egg_base, ei_cmd.egg_info),
            ei_cmd.egg_name,
            ei_cmd.egg_version,
        )
        bs_cmd = self.get_finalized_command('build_scripts')
        executable = getattr(bs_cmd, 'executable', easy_install.sys_executable)
        if 'bdist_wheel' in self.distribution.have_run:
            # We're building a wheel which has no way of generating mod_wsgi
            # scripts for us. Let's build them.
            # NOTE(sigmavirus24): This needs to happen here because, as the
            # comment below indicates, no_ep is True when building a wheel.
            self._make_wsgi_scripts_only(dist, executable)

        if self.no_ep:
            # no_ep is True if we're installing into an .egg file or building
            # a .whl file, in those cases, we do not want to build all of the
            # entry-points listed for this package.
            return

        if os.name != 'nt':
            get_script_args = override_get_script_args
        else:
            get_script_args = easy_install.get_script_args
            executable = '"%s"' % executable

        for args in get_script_args(dist, executable):
            self.write_script(*args)


class LocalManifestMaker(egg_info.manifest_maker):
    """Add any files that are in git and some standard sensible files."""

    def _add_pbr_defaults(self):
        for template_line in [
            'include AUTHORS',
            'include ChangeLog',
            'exclude .gitignore',
            'exclude .gitreview',
            'global-exclude *.pyc',
        ]:
            self.filelist.process_template_line(template_line)

    def add_defaults(self):
        """Add all the default files to self.filelist:

        Extends the functionality provided by distutils to also included
        additional sane defaults, such as the ``AUTHORS`` and ``ChangeLog``
        files generated by *pbr*.

        Warns if (``README`` or ``README.txt``) or ``setup.py`` are missing;
        everything else is optional.
        """
        option_dict = self.distribution.get_option_dict('pbr')

        sdist.sdist.add_defaults(self)
        self.filelist.append(self.template)
        self.filelist.append(self.manifest)
        self.filelist.extend(extra_files.get_extra_files())
        should_skip = options.get_boolean_option(
            option_dict, 'skip_git_sdist', 'SKIP_GIT_SDIST'
        )
        if not should_skip:
            rcfiles = git._find_git_files()
            if rcfiles:
                self.filelist.extend(rcfiles)
        elif os.path.exists(self.manifest):
            self.read_manifest()
        ei_cmd = self.get_finalized_command('egg_info')
        self._add_pbr_defaults()
        self.filelist.include_pattern("*", prefix=ei_cmd.egg_info)


class LocalEggInfo(egg_info.egg_info):
    """Override the egg_info command to regenerate SOURCES.txt sensibly."""

    command_name = 'egg_info'

    def find_sources(self):
        """Generate SOURCES.txt only if there isn't one already.

        If we are in an sdist command, then we always want to update
        SOURCES.txt. If we are not in an sdist command, then it doesn't
        matter one flip, and is actually destructive.
        However, if we're in a git context, it's always the right thing to do
        to recreate SOURCES.txt
        """
        manifest_filename = os.path.join(self.egg_info, "SOURCES.txt")
        if (
            not os.path.exists(manifest_filename)
            or os.path.exists('.git')
            or 'sdist' in sys.argv
        ):
            log.info("[pbr] Processing SOURCES.txt")
            mm = LocalManifestMaker(self.distribution)
            mm.manifest = manifest_filename
            mm.run()
            self.filelist = mm.filelist
        else:
            log.info("[pbr] Reusing existing SOURCES.txt")
            self.filelist = egg_info.FileList()
            with open(manifest_filename, 'r') as fil:
                for entry in fil.read().split('\n'):
                    self.filelist.append(entry)


def _from_git(distribution):
    option_dict = distribution.get_option_dict('pbr')
    changelog = git._iter_log_oneline()
    if changelog:
        changelog = git._iter_changelog(changelog)
    git.write_git_changelog(option_dict=option_dict, changelog=changelog)
    git.generate_authors(option_dict=option_dict)


class InstallWithGit(install.install):
    """Extracts ChangeLog and AUTHORS from git then installs.

    This is useful for e.g. readthedocs where the package is
    installed and then docs built.
    """

    command_name = 'install'

    def run(self):
        _from_git(self.distribution)
        return install.install.run(self)


class LocalInstall(install.install):
    """Runs python setup.py install in a sensible manner.

    Force a non-egg installed in the manner of
    single-version-externally-managed, which allows us to install manpages
    and config files.
    """

    command_name = 'install'

    def run(self):
        _from_git(self.distribution)
        return du_install.install.run(self)


class LocalSDist(sdist.sdist):
    """Builds the ChangeLog and Authors files from VC first."""

    command_name = 'sdist'

    def checking_reno(self):
        """Ensure reno is installed and configured.

        We can't run reno-based commands if reno isn't installed/available, and
        don't want to if the user isn't using it.
        """
        if hasattr(self, '_has_reno'):
            return self._has_reno

        option_dict = self.distribution.get_option_dict('pbr')
        should_skip = options.get_boolean_option(
            option_dict, 'skip_reno', 'SKIP_GENERATE_RENO'
        )
        if should_skip:
            self._has_reno = False
            return False

        try:
            # versions of reno witout this module will not have the required
            # feature, hence the import
            from reno import setup_command  # noqa
        except ImportError:
            log.info(
                '[pbr] reno was not found or is too old. Skipping '
                'release notes'
            )
            self._has_reno = False
            return False

        conf, output_file, cache_file = setup_command.load_config(
            self.distribution
        )

        if not os.path.exists(os.path.join(conf.reporoot, conf.notespath)):
            log.info(
                '[pbr] reno does not appear to be configured. Skipping '
                'release notes'
            )
            self._has_reno = False
            return False

        self._files = [output_file, cache_file]

        log.info('[pbr] Generating release notes')
        self._has_reno = True

        return True

    sub_commands = [('build_reno', checking_reno)] + sdist.sdist.sub_commands

    def run(self):
        _from_git(self.distribution)
        # sdist.sdist is an old style class, can't use super()
        sdist.sdist.run(self)

    def make_distribution(self):
        # This is included in make_distribution because setuptools doesn't use
        # 'get_file_list'. As such, this is the only hook point that runs after
        # the commands in 'sub_commands'
        if self.checking_reno():
            self.filelist.extend(self._files)
            self.filelist.sort()
        sdist.sdist.make_distribution(self)


class LocalRPMVersion(setuptools.Command):
    __doc__ = """Output the rpm *compatible* version string of this package"""
    description = __doc__

    user_options = []
    command_name = "rpm_version"

    def run(self):
        log.info("[pbr] Extracting rpm version")
        name = self.distribution.get_name()
        print(version.VersionInfo(name).semantic_version().rpm_string())

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class LocalDebVersion(setuptools.Command):
    __doc__ = """Output the deb *compatible* version string of this package"""
    description = __doc__

    user_options = []
    command_name = "deb_version"

    def run(self):
        log.info("[pbr] Extracting deb version")
        name = self.distribution.get_name()
        print(version.VersionInfo(name).semantic_version().debian_string())

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
