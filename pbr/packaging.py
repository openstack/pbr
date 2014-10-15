# Copyright 2011 OpenStack LLC.
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

from __future__ import unicode_literals

from distutils.command import install as du_install
import distutils.errors
from distutils import log
import email
import io
import os
import re
import subprocess
import sys
try:
    import cStringIO
except ImportError:
    import io as cStringIO

import pkg_resources
from setuptools.command import easy_install
from setuptools.command import egg_info
from setuptools.command import install
from setuptools.command import install_scripts
from setuptools.command import sdist

from pbr import extra_files
from pbr import version

TRUE_VALUES = ('true', '1', 'yes')
REQUIREMENTS_FILES = ('requirements.txt', 'tools/pip-requires')
TEST_REQUIREMENTS_FILES = ('test-requirements.txt', 'tools/test-requires')


def get_requirements_files():
    files = os.environ.get("PBR_REQUIREMENTS_FILES")
    if files:
        return tuple(f.strip() for f in files.split(','))
    # Returns a list composed of:
    # - REQUIREMENTS_FILES with -py2 or -py3 in the name
    #   (e.g. requirements-py3.txt)
    # - REQUIREMENTS_FILES
    return (list(map(('-py' + str(sys.version_info[0])).join,
                     map(os.path.splitext, REQUIREMENTS_FILES)))
            + list(REQUIREMENTS_FILES))


def append_text_list(config, key, text_list):
    """Append a \n separated list to possibly existing value."""
    new_value = []
    current_value = config.get(key, "")
    if current_value:
        new_value.append(current_value)
    new_value.extend(text_list)
    config[key] = '\n'.join(new_value)


def _pip_install(links, requires, root=None, option_dict=dict()):
    if get_boolean_option(
            option_dict, 'skip_pip_install', 'SKIP_PIP_INSTALL'):
        return
    cmd = [sys.executable, '-m', 'pip.__init__', 'install']
    if root:
        cmd.append("--root=%s" % root)
    for link in links:
        cmd.append("-f")
        cmd.append(link)

    # NOTE(ociuhandu): popen on Windows does not accept unicode strings
    _run_shell_command(
        cmd + requires,
        throw_on_error=True, buffer=False, env=dict(PIP_USE_WHEEL=b"true"))


def _any_existing(file_list):
    return [f for f in file_list if os.path.exists(f)]


# Get requirements from the first file that exists
def get_reqs_from_files(requirements_files):
    for requirements_file in _any_existing(requirements_files):
        with open(requirements_file, 'r') as fil:
            return fil.read().split('\n')
    return []


def parse_requirements(requirements_files=None):

    if requirements_files is None:
        requirements_files = get_requirements_files()

    def egg_fragment(match):
        # take a versioned egg fragment and return a
        # versioned package requirement e.g.
        # nova-1.2.3 becomes nova>=1.2.3
        return re.sub(r'([\w.]+)-([\w.-]+)',
                      r'\1>=\2',
                      match.group(1))

    requirements = []
    for line in get_reqs_from_files(requirements_files):
        # Ignore comments
        if (not line.strip()) or line.startswith('#'):
            continue

        # Handle nested requirements files such as:
        # -r other-requirements.txt
        if line.startswith('-r'):
            req_file = line.partition(' ')[2]
            requirements += parse_requirements([req_file])
            continue

        try:
            project_name = pkg_resources.Requirement.parse(line).project_name
        except ValueError:
            project_name = None

        # For the requirements list, we need to inject only the portion
        # after egg= so that distutils knows the package it's looking for
        # such as:
        # -e git://github.com/openstack/nova/master#egg=nova
        # -e git://github.com/openstack/nova/master#egg=nova-1.2.3
        if re.match(r'\s*-e\s+', line):
            line = re.sub(r'\s*-e\s+.*#egg=(.*)$', egg_fragment, line)
        # such as:
        # http://github.com/openstack/nova/zipball/master#egg=nova
        # http://github.com/openstack/nova/zipball/master#egg=nova-1.2.3
        elif re.match(r'\s*https?:', line):
            line = re.sub(r'\s*https?:.*#egg=(.*)$', egg_fragment, line)
        # -f lines are for index locations, and don't get used here
        elif re.match(r'\s*-f\s+', line):
            line = None
            reason = 'Index Location'

        if line is not None:
            requirements.append(line)
        else:
            log.info(
                '[pbr] Excluding %s: %s' % (project_name, reason))

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
        elif re.match(r'\s*https?:', line):
            dependency_links.append(line)
    return dependency_links


def _run_git_command(cmd, git_dir, **kwargs):
    if not isinstance(cmd, (list, tuple)):
        cmd = [cmd]
    return _run_shell_command(
        ['git', '--git-dir=%s' % git_dir] + cmd, **kwargs)


def _run_shell_command(cmd, throw_on_error=False, buffer=True, env=None):
    if buffer:
        out_location = subprocess.PIPE
        err_location = subprocess.PIPE
    else:
        out_location = None
        err_location = None

    newenv = os.environ.copy()
    if env:
        newenv.update(env)

    output = subprocess.Popen(cmd,
                              stdout=out_location,
                              stderr=err_location,
                              env=newenv)
    out = output.communicate()
    if output.returncode and throw_on_error:
        raise distutils.errors.DistutilsError(
            "%s returned %d" % (cmd, output.returncode))
    if len(out) == 0 or not out[0] or not out[0].strip():
        return ''
    return out[0].strip().decode('utf-8')


def _get_git_directory():
    return _run_shell_command(['git', 'rev-parse', '--git-dir'])


def _git_is_installed():
    try:
        # We cannot use 'which git' as it may not be available
        # in some distributions, So just try 'git --version'
        # to see if we run into trouble
        _run_shell_command(['git', '--version'])
    except OSError:
        return False
    return True


def _get_highest_tag(tags):
    """Find the highest tag from a list.

    Pass in a list of tag strings and this will return the highest
    (latest) as sorted by the pkg_resources version parser.
    """
    return max(tags, key=pkg_resources.parse_version)


def get_boolean_option(option_dict, option_name, env_name):
    return ((option_name in option_dict
             and option_dict[option_name][1].lower() in TRUE_VALUES) or
            str(os.getenv(env_name)).lower() in TRUE_VALUES)


def _iter_changelog(changelog):
    """Convert a oneline log iterator to formatted strings.

    :param changelog: An iterator of one line log entries like
        that given by _iter_log_oneline.
    :return: An iterator over (release, formatted changelog) tuples.
    """
    first_line = True
    current_release = None
    yield current_release, "CHANGES\n=======\n\n"
    for hash, tags, msg in changelog:
        if tags:
            current_release = _get_highest_tag(tags)
            underline = len(current_release) * '-'
            if not first_line:
                yield current_release, '\n'
            yield current_release, (
                "%(tag)s\n%(underline)s\n\n" %
                dict(tag=current_release, underline=underline))

        if not msg.startswith("Merge "):
            if msg.endswith("."):
                msg = msg[:-1]
            yield current_release, "* %(msg)s\n" % dict(msg=msg)
        first_line = False


def _iter_log_oneline(git_dir=None, option_dict=None):
    """Iterate over --oneline log entries if possible.

    This parses the output into a structured form but does not apply
    presentation logic to the output - making it suitable for different
    uses.

    :return: An iterator of (hash, tags_set, 1st_line) tuples, or None if
        changelog generation is disabled / not available.
    """
    if not option_dict:
        option_dict = {}
    should_skip = get_boolean_option(option_dict, 'skip_changelog',
                                     'SKIP_WRITE_GIT_CHANGELOG')
    if should_skip:
        return
    if git_dir is None:
        git_dir = _get_git_directory()
    if not git_dir:
        return
    return _iter_log_inner(git_dir)


def _iter_log_inner(git_dir):
    """Iterate over --oneline log entries.

    This parses the output intro a structured form but does not apply
    presentation logic to the output - making it suitable for different
    uses.

    :return: An iterator of (hash, tags_set, 1st_line) tuples.
    """
    log.info('[pbr] Generating ChangeLog')
    log_cmd = ['log', '--oneline', '--decorate']
    changelog = _run_git_command(log_cmd, git_dir)
    for line in changelog.split('\n'):
        line_parts = line.split()
        if len(line_parts) < 2:
            continue
        # Tags are in a list contained in ()'s. If a commit
        # subject that is tagged happens to have ()'s in it
        # this will fail
        if line_parts[1].startswith('(') and ')' in line:
            msg = line.split(')')[1].strip()
        else:
            msg = " ".join(line_parts[1:])

        if "tag:" in line:
            tags = set([
                tag.split(",")[0]
                for tag in line.split(")")[0].split("tag: ")[1:]])
        else:
            tags = set()

        yield line_parts[0], tags, msg


def write_git_changelog(git_dir=None, dest_dir=os.path.curdir,
                        option_dict=dict(), changelog=None):
    """Write a changelog based on the git changelog."""
    if not changelog:
        changelog = _iter_log_oneline(git_dir=git_dir, option_dict=option_dict)
        if changelog:
            changelog = _iter_changelog(changelog)
    if not changelog:
        return
    log.info('[pbr] Writing ChangeLog')
    new_changelog = os.path.join(dest_dir, 'ChangeLog')
    # If there's already a ChangeLog and it's not writable, just use it
    if (os.path.exists(new_changelog)
            and not os.access(new_changelog, os.W_OK)):
        return
    with io.open(new_changelog, "w", encoding="utf-8") as changelog_file:
        for release, content in changelog:
            changelog_file.write(content)


def generate_authors(git_dir=None, dest_dir='.', option_dict=dict()):
    """Create AUTHORS file using git commits."""
    should_skip = get_boolean_option(option_dict, 'skip_authors',
                                     'SKIP_GENERATE_AUTHORS')
    if should_skip:
        return
    old_authors = os.path.join(dest_dir, 'AUTHORS.in')
    new_authors = os.path.join(dest_dir, 'AUTHORS')
    # If there's already an AUTHORS file and it's not writable, just use it
    if (os.path.exists(new_authors)
            and not os.access(new_authors, os.W_OK)):
        return
    log.info('[pbr] Generating AUTHORS')
    ignore_emails = '(jenkins@review|infra@lists|jenkins@openstack)'
    if git_dir is None:
        git_dir = _get_git_directory()
    if git_dir:
        authors = []

        # don't include jenkins email address in AUTHORS file
        git_log_cmd = ['log', '--format=%aN <%aE>']
        authors += _run_git_command(git_log_cmd, git_dir).split('\n')
        authors = [a for a in authors if not re.search(ignore_emails, a)]

        # get all co-authors from commit messages
        co_authors_out = _run_git_command('log', git_dir)
        co_authors = re.findall('Co-authored-by:.+', co_authors_out,
                                re.MULTILINE)
        co_authors = [signed.split(":", 1)[1].strip()
                      for signed in co_authors if signed]

        authors += co_authors
        authors = sorted(set(authors))

        with open(new_authors, 'wb') as new_authors_fh:
            if os.path.exists(old_authors):
                with open(old_authors, "rb") as old_authors_fh:
                    new_authors_fh.write(old_authors_fh.read())
            new_authors_fh.write(('\n'.join(authors) + '\n')
                                 .encode('utf-8'))


def _find_git_files(dirname='', git_dir=None):
    """Behave like a file finder entrypoint plugin.

    We don't actually use the entrypoints system for this because it runs
    at absurd times. We only want to do this when we are building an sdist.
    """
    file_list = []
    if git_dir is None and _git_is_installed():
        git_dir = _get_git_directory()
    if git_dir:
        log.info("[pbr] In git context, generating filelist from git")
        file_list = _run_git_command(['ls-files', '-z'], git_dir)
        file_list = file_list.split(b'\x00'.decode('utf-8'))
    return [f for f in file_list if f]


_rst_template = """%(heading)s
%(underline)s

.. automodule:: %(module)s
  :members:
  :undoc-members:
  :show-inheritance:
"""


def _find_modules(arg, dirname, files):
    for filename in files:
        if filename.endswith('.py') and filename != '__init__.py':
            arg["%s.%s" % (dirname.replace('/', '.'),
                           filename[:-3])] = True


class LocalInstall(install.install):
    """Runs python setup.py install in a sensible manner.

    Force a non-egg installed in the manner of
    single-version-externally-managed, which allows us to install manpages
    and config files.

    Because non-egg installs bypass the depend processing machinery, we
    need to do our own. Because easy_install is evil, just use pip to
    process our requirements files directly, which means we don't have to
    do crazy extra processing.

    Bypass installation if --single-version-externally-managed is given,
    so that behavior for packagers remains the same.
    """

    command_name = 'install'

    def run(self):
        option_dict = self.distribution.get_option_dict('pbr')
        if (not self.single_version_externally_managed
                and self.distribution.install_requires):
            _pip_install(
                self.distribution.dependency_links,
                self.distribution.install_requires, self.root,
                option_dict=option_dict)

        return du_install.install.run(self)


def _newer_requires_files(egg_info_dir):
    """Check to see if any of the requires files are newer than egg-info."""
    for target, sources in (('requires.txt', get_requirements_files()),
                            ('test-requires.txt', TEST_REQUIREMENTS_FILES)):
        target_path = os.path.join(egg_info_dir, target)
        for src in _any_existing(sources):
            if (not os.path.exists(target_path) or
                    os.path.getmtime(target_path)
                    < os.path.getmtime(src)):
                return True
    return False


def _copy_test_requires_to(egg_info_dir):
    """Copy the requirements file to egg-info/test-requires.txt."""
    with open(os.path.join(egg_info_dir, 'test-requires.txt'), 'w') as dest:
        for source in _any_existing(TEST_REQUIREMENTS_FILES):
            dest.write(open(source, 'r').read().rstrip('\n') + '\n')


class _PipInstallTestRequires(object):
    """Mixin class to install test-requirements.txt before running tests."""

    def install_test_requirements(self):

        links = parse_dependency_links(TEST_REQUIREMENTS_FILES)
        if self.distribution.tests_require:
            option_dict = self.distribution.get_option_dict('pbr')
            _pip_install(
                links, self.distribution.tests_require,
                option_dict=option_dict)

    def pre_run(self):
        self.egg_name = pkg_resources.safe_name(self.distribution.get_name())
        self.egg_info = "%s.egg-info" % pkg_resources.to_filename(
            self.egg_name)
        if (not os.path.exists(self.egg_info) or
                _newer_requires_files(self.egg_info)):
            ei_cmd = self.get_finalized_command('egg_info')
            ei_cmd.run()
            self.install_test_requirements()
            _copy_test_requires_to(self.egg_info)

try:
    from pbr import testr_command

    class TestrTest(testr_command.Testr, _PipInstallTestRequires):
        """Make setup.py test do the right thing."""

        command_name = 'test'

        def run(self):
            self.pre_run()
            # Can't use super - base class old-style class
            testr_command.Testr.run(self)

    _have_testr = True

except ImportError:
    _have_testr = False


def have_testr():
    return _have_testr

try:
    from nose import commands

    class NoseTest(commands.nosetests, _PipInstallTestRequires):
        """Fallback test runner if testr is a no-go."""

        command_name = 'test'

        def run(self):
            self.pre_run()
            # Can't use super - base class old-style class
            commands.nosetests.run(self)

    _have_nose = True

except ImportError:
    _have_nose = False


def have_nose():
    return _have_nose


_script_text = """# PBR Generated from %(group)r

import sys

from %(module_name)s import %(import_target)s


if __name__ == "__main__":
    sys.exit(%(invoke_target)s())
"""


def override_get_script_args(
        dist, executable=os.path.normpath(sys.executable), is_wininst=False):
    """Override entrypoints console_script."""
    header = easy_install.get_script_header("", executable, is_wininst)
    for group in 'console_scripts', 'gui_scripts':
        for name, ep in dist.get_entry_map(group).items():
            if not ep.attrs or len(ep.attrs) > 2:
                raise ValueError("Script targets must be of the form "
                                 "'func' or 'Class.class_method'.")
            script_text = _script_text % dict(
                group=group,
                module_name=ep.module_name,
                import_target=ep.attrs[0],
                invoke_target='.'.join(ep.attrs),
            )
            yield (name, header + script_text)


class LocalInstallScripts(install_scripts.install_scripts):
    """Intercepts console scripts entry_points."""
    command_name = 'install_scripts'

    def run(self):
        if os.name != 'nt':
            get_script_args = override_get_script_args
        else:
            get_script_args = easy_install.get_script_args

        import distutils.command.install_scripts

        self.run_command("egg_info")
        if self.distribution.scripts:
            # run first to set up self.outfiles
            distutils.command.install_scripts.install_scripts.run(self)
        else:
            self.outfiles = []
        if self.no_ep:
            # don't install entry point scripts into .egg file!
            return

        ei_cmd = self.get_finalized_command("egg_info")
        dist = pkg_resources.Distribution(
            ei_cmd.egg_base,
            pkg_resources.PathMetadata(ei_cmd.egg_base, ei_cmd.egg_info),
            ei_cmd.egg_name, ei_cmd.egg_version,
        )
        bs_cmd = self.get_finalized_command('build_scripts')
        executable = getattr(
            bs_cmd, 'executable', easy_install.sys_executable)
        is_wininst = getattr(
            self.get_finalized_command("bdist_wininst"), '_is_running', False
        )
        for args in get_script_args(dist, executable, is_wininst):
            self.write_script(*args)


class LocalManifestMaker(egg_info.manifest_maker):
    """Add any files that are in git and some standard sensible files."""

    def _add_pbr_defaults(self):
        for template_line in [
            'include AUTHORS',
            'include ChangeLog',
            'exclude .gitignore',
            'exclude .gitreview',
            'global-exclude *.pyc'
        ]:
            self.filelist.process_template_line(template_line)

    def add_defaults(self):
        option_dict = self.distribution.get_option_dict('pbr')

        sdist.sdist.add_defaults(self)
        self.filelist.append(self.template)
        self.filelist.append(self.manifest)
        self.filelist.extend(extra_files.get_extra_files())
        should_skip = get_boolean_option(option_dict, 'skip_git_sdist',
                                         'SKIP_GIT_SDIST')
        if not should_skip:
            rcfiles = _find_git_files()
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
        """
        manifest_filename = os.path.join(self.egg_info, "SOURCES.txt")
        if not os.path.exists(manifest_filename) or 'sdist' in sys.argv:
            log.info("[pbr] Processing SOURCES.txt")
            mm = LocalManifestMaker(self.distribution)
            mm.manifest = manifest_filename
            mm.run()
            self.filelist = mm.filelist
        else:
            log.info("[pbr] Reusing existing SOURCES.txt")
            self.filelist = egg_info.FileList()
            for entry in open(manifest_filename, 'r').read().split('\n'):
                self.filelist.append(entry)


class LocalSDist(sdist.sdist):
    """Builds the ChangeLog and Authors files from VC first."""

    command_name = 'sdist'

    def run(self):
        option_dict = self.distribution.get_option_dict('pbr')
        changelog = _iter_log_oneline(option_dict=option_dict)
        if changelog:
            changelog = _iter_changelog(changelog)
        write_git_changelog(option_dict=option_dict, changelog=changelog)
        generate_authors(option_dict=option_dict)
        # sdist.sdist is an old style class, can't use super()
        sdist.sdist.run(self)

try:
    from sphinx import apidoc
    from sphinx import application
    from sphinx import config
    from sphinx import setup_command

    class LocalBuildDoc(setup_command.BuildDoc):

        command_name = 'build_sphinx'
        builders = ['html', 'man']

        def _get_source_dir(self):
            option_dict = self.distribution.get_option_dict('build_sphinx')
            if 'source_dir' in option_dict:
                source_dir = os.path.join(option_dict['source_dir'][1], 'api')
            else:
                source_dir = 'doc/source/api'
            if not os.path.exists(source_dir):
                os.makedirs(source_dir)
            return source_dir

        def generate_autoindex(self, excluded_modules=None):
            log.info("[pbr] Autodocumenting from %s"
                     % os.path.abspath(os.curdir))
            modules = {}
            source_dir = self._get_source_dir()
            for pkg in self.distribution.packages:
                if '.' not in pkg:
                    for dirpath, dirnames, files in os.walk(pkg):
                        _find_modules(modules, dirpath, files)
            module_list = set(modules.keys())
            if excluded_modules is not None:
                module_list -= set(excluded_modules)
            module_list = sorted(module_list)
            autoindex_filename = os.path.join(source_dir, 'autoindex.rst')
            with open(autoindex_filename, 'w') as autoindex:
                autoindex.write(""".. toctree::
   :maxdepth: 1

""")
                for module in module_list:
                    output_filename = os.path.join(source_dir,
                                                   "%s.rst" % module)
                    heading = "The :mod:`%s` Module" % module
                    underline = "=" * len(heading)
                    values = dict(module=module, heading=heading,
                                  underline=underline)

                    log.info("[pbr] Generating %s"
                             % output_filename)
                    with open(output_filename, 'w') as output_file:
                        output_file.write(_rst_template % values)
                    autoindex.write("   %s.rst\n" % module)

        def _sphinx_tree(self):
                source_dir = self._get_source_dir()
                cmd = ['apidoc', '.', '-H', 'Modules', '-o', source_dir]
                apidoc.main(cmd + self.autodoc_tree_excludes)

        def _sphinx_run(self):
            if not self.verbose:
                status_stream = cStringIO.StringIO()
            else:
                status_stream = sys.stdout
            confoverrides = {}
            if self.version:
                confoverrides['version'] = self.version
            if self.release:
                confoverrides['release'] = self.release
            if self.today:
                confoverrides['today'] = self.today
            sphinx_config = config.Config(self.config_dir, 'conf.py', {}, [])
            sphinx_config.init_values()
            if self.builder == 'man' and len(sphinx_config.man_pages) == 0:
                return
            app = application.Sphinx(
                self.source_dir, self.config_dir,
                self.builder_target_dir, self.doctree_dir,
                self.builder, confoverrides, status_stream,
                freshenv=self.fresh_env, warningiserror=True)

            try:
                app.build(force_all=self.all_files)
            except Exception as err:
                from docutils import utils
                if isinstance(err, utils.SystemMessage):
                    sys.stder.write('reST markup error:\n')
                    sys.stderr.write(err.args[0].encode('ascii',
                                                        'backslashreplace'))
                    sys.stderr.write('\n')
                else:
                    raise

            if self.link_index:
                src = app.config.master_doc + app.builder.out_suffix
                dst = app.builder.get_outfilename('index')
                os.symlink(src, dst)

        def run(self):
            option_dict = self.distribution.get_option_dict('pbr')
            if _git_is_installed():
                write_git_changelog(option_dict=option_dict)
                generate_authors(option_dict=option_dict)
            tree_index = get_boolean_option(option_dict,
                                            'autodoc_tree_index_modules',
                                            'AUTODOC_TREE_INDEX_MODULES')
            auto_index = get_boolean_option(option_dict,
                                            'autodoc_index_modules',
                                            'AUTODOC_INDEX_MODULES')
            if not os.getenv('SPHINX_DEBUG'):
                # NOTE(afazekas): These options can be used together,
                # but they do a very similar thing in a different way
                if tree_index:
                    self._sphinx_tree()
                if auto_index:
                    self.generate_autoindex(
                        option_dict.get(
                            "autodoc_exclude_modules",
                            [None, ""])[1].split())

            for builder in self.builders:
                self.builder = builder
                self.finalize_options()
                self.project = self.distribution.get_name()
                self.version = self.distribution.get_version()
                self.release = self.distribution.get_version()
                if get_boolean_option(option_dict, 'warnerrors', 'WARNERRORS'):
                    self._sphinx_run()
                else:
                    setup_command.BuildDoc.run(self)

        def initialize_options(self):
            # Not a new style class, super keyword does not work.
            setup_command.BuildDoc.initialize_options(self)

            # NOTE(dstanek): exclude setup.py from the autodoc tree index
            # builds because all projects will have an issue with it
            self.autodoc_tree_excludes = ['setup.py']

        def finalize_options(self):
            # Not a new style class, super keyword does not work.
            setup_command.BuildDoc.finalize_options(self)
            # Allow builders to be configurable - as a comma separated list.
            if not isinstance(self.builders, list) and self.builders:
                self.builders = self.builders.split(',')

            # NOTE(dstanek): check for autodoc tree exclusion overrides
            # in the setup.cfg
            opt = 'autodoc_tree_excludes'
            option_dict = self.distribution.get_option_dict('pbr')
            if opt in option_dict:
                self.autodoc_tree_excludes = option_dict[opt][1]
                self.ensure_string_list(opt)

    class LocalBuildLatex(LocalBuildDoc):
        builders = ['latex']
        command_name = 'build_sphinx_latex'

    _have_sphinx = True

except ImportError:
    _have_sphinx = False


def have_sphinx():
    return _have_sphinx


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
    changelog = _run_git_command(['log', version_spec], git_dir)
    header_len = len('    sem-ver:')
    commands = [line[header_len:].strip() for line in changelog.split('\n')
                if line.lower().startswith('    sem-ver:')]
    symbols = set()
    for command in commands:
        symbols.update([symbol.strip() for symbol in command.split(',')])

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
    changelog = _iter_log_oneline(git_dir=git_dir)
    row_count = 0
    for row_count, (ignored, tag_set, ignored) in enumerate(changelog):
        version_tags = set()
        for tag in list(tag_set):
            try:
                version_tags.add(version.SemanticVersion.from_pip_string(tag))
            except Exception:
                pass
        if version_tags:
            return max(version_tags).release_string(), row_count
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
    sha = _run_git_command(
        ['log', '-n1', '--pretty=format:%h'], git_dir)
    tag, distance = _get_revno_and_last_tag(git_dir)
    last_semver = version.SemanticVersion.from_pip_string(tag or '0')
    if distance == 0:
        new_version = last_semver
    else:
        new_version = last_semver.increment(
            **_get_increment_kwargs(git_dir, tag))
    if target_version is not None and new_version > target_version:
        raise ValueError(
            "git history requires a target version of %(new)s, but target "
            "version is %(target)s" %
            dict(new=new_version, target=target_version))
    if distance == 0:
        return last_semver
    if target_version is not None:
        return target_version.to_dev(distance, sha)
    else:
        return new_version.to_dev(distance, sha)


def _get_version_from_git(pre_version=None):
    """Calculate a version string from git.

    If the revision is tagged, return that. Otherwise calculate a semantic
    version description of the tree.

    The number of revisions since the last tag is included in the dev counter
    in the version for untagged versions.

    :param pre_version: If supplied use this as the target version rather than
        inferring one from the last tag + commit messages.
    """
    git_dir = _get_git_directory()
    if git_dir and _git_is_installed():
        try:
            tagged = _run_git_command(
                ['describe', '--exact-match'], git_dir,
                throw_on_error=True).replace('-', '.')
            target_version = version.SemanticVersion.from_pip_string(tagged)
        except Exception:
            if pre_version:
                # not released yet - use pre_version as the target
                target_version = version.SemanticVersion.from_pip_string(
                    pre_version)
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
            pkg_metadata_file = open(filename, 'r')
        except (IOError, OSError):
            continue
        try:
            pkg_metadata = email.message_from_file(pkg_metadata_file)
        except email.MessageError:
            continue

    # Check to make sure we're in our own dir
    if pkg_metadata.get('Name', None) != package_name:
        return None
    return pkg_metadata.get('Version', None)


def get_version(package_name, pre_version=None):
    """Get the version of the project. First, try getting it from PKG-INFO or
    METADATA, if it exists. If it does, that means we're in a distribution
    tarball or that install has happened. Otherwise, if there is no PKG-INFO
    or METADATA file, pull the version from git.

    We do not support setup.py version sanity in git archive tarballs, nor do
    we support packagers directly sucking our git repo into theirs. We expect
    that a source tarball be made from our git repo - or that if someone wants
    to make a source tarball from a fork of our repo with additional tags in it
    that they understand and desire the results of doing that.

    :param pre_version: The version field from setup.cfg - if set then this
        version will be the next release.
    """
    version = os.environ.get(
        "PBR_VERSION",
        os.environ.get("OSLO_PACKAGE_VERSION", None))
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
    raise Exception("Versioning for this project requires either an sdist"
                    " tarball, or access to an upstream git repository."
                    " Are you sure that git is installed?")
