# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

# The code in this module is mostly copy/pasted out of the distutils2 source
# code, as recommended by Tarek Ziade.

from __future__ import absolute_import
from __future__ import print_function

# These first two imports are not used, but are needed to get around an
# irritating Python bug that can crop up when using ./setup.py test.
# See: http://www.eby-sarna.com/pipermail/peak/2010-May/003355.html
try:
    import multiprocessing  # noqa
except ImportError:
    pass
import logging  # noqa

import io
import os
import re
import shlex
import sys
import traceback
import warnings

from distutils import errors
from distutils import log
import setuptools
from setuptools import dist as st_dist
from setuptools import extension

from pbr._compat.five import ConfigParser
from pbr._compat.five import integer_types
from pbr._compat.five import string_type
from pbr._compat import packaging as packaging_compat
from pbr import extra_files
from pbr import hooks

"""Implementation of setup.cfg support."""

# A simplified RE for this; just checks that the line ends with version
# predicates in ()
_VERSION_SPEC_RE = re.compile(r'\s*(.*?)\s*\((.*)\)\s*$')

# Mappings from setup.cfg options, in (section, option) form, to setup()
# keyword arguments
CFG_TO_PY_SETUP_ARGS = (
    (('metadata', 'name'), 'name'),
    (('metadata', 'version'), 'version'),
    (('metadata', 'author'), 'author'),
    (('metadata', 'author_email'), 'author_email'),
    (('metadata', 'maintainer'), 'maintainer'),
    (('metadata', 'maintainer_email'), 'maintainer_email'),
    (('metadata', 'home_page'), 'url'),
    (('metadata', 'project_urls'), 'project_urls'),
    (('metadata', 'summary'), 'description'),
    (('metadata', 'keywords'), 'keywords'),
    (('metadata', 'description'), 'long_description'),
    (
        ('metadata', 'description_content_type'),
        'long_description_content_type',
    ),
    (('metadata', 'download_url'), 'download_url'),
    (('metadata', 'classifier'), 'classifiers'),
    (('metadata', 'platform'), 'platforms'),  # **
    (('metadata', 'license'), 'license'),
    # Use setuptools install_requires, not
    # broken distutils requires
    (('metadata', 'requires_dist'), 'install_requires'),
    (('metadata', 'setup_requires_dist'), 'setup_requires'),
    (('metadata', 'python_requires'), 'python_requires'),
    (('metadata', 'requires_python'), 'python_requires'),
    (('metadata', 'provides_dist'), 'provides'),  # **
    (('metadata', 'provides_extras'), 'provides_extras'),
    (('metadata', 'obsoletes_dist'), 'obsoletes'),  # **
    (('files', 'packages_root'), 'package_dir'),
    (('files', 'packages'), 'packages'),
    (('files', 'package_data'), 'package_data'),
    (('files', 'namespace_packages'), 'namespace_packages'),
    (('files', 'data_files'), 'data_files'),
    (('files', 'scripts'), 'scripts'),
    (('files', 'modules'), 'py_modules'),  # **
    (('global', 'commands'), 'cmdclass'),
    # Not supported in distutils2, but provided for
    # backwards compatibility with setuptools
    (('backwards_compat', 'zip_safe'), 'zip_safe'),
    (('backwards_compat', 'tests_require'), 'tests_require'),
    (('backwards_compat', 'dependency_links'), 'dependency_links'),
    (('backwards_compat', 'include_package_data'), 'include_package_data'),
)

DEPRECATED_CFG = {
    ('metadata', 'home_page'): (
        "Use '[metadata] url' (setup.cfg) or '[project.urls]' "
        "(pyproject.toml) instead"
    ),
    ('metadata', 'summary'): (
        "Use '[metadata] description' (setup.cfg) or '[project] description' "
        "(pyproject.toml) instead"
    ),
    ('metadata', 'description_file'): (
        "Use '[metadata] long_description' (setup.cfg) or '[project] readme' "
        "(pyproject.toml) instead"
    ),
    ('metadata', 'classifier'): (
        "Use '[metadata] classifiers' (setup.cfg) or '[project] classifiers' "
        "(pyproject.toml) instead"
    ),
    ('metadata', 'platform'): (
        "Use '[metadata] platforms' (setup.cfg) or "
        "'[tool.setuptools] platforms' (pyproject.toml) instead"
    ),
    ('metadata', 'requires_dist'): (
        "Use '[options] install_requires' (setup.cfg) or "
        "'[project] dependencies' (pyproject.toml) instead"
    ),
    ('metadata', 'setup_requires_dist'): (
        "Use '[options] setup_requires' (setup.cfg) or "
        "'[build-system] requires' (pyproject.toml) instead"
    ),
    ('metadata', 'python_requires'): (
        "Use '[options] python_requires' (setup.cfg) or "
        "'[project] requires-python' (pyproject.toml) instead"
    ),
    ('metadata', 'requires_python'): (
        "Use '[options] python_requires' (setup.cfg) or "
        "'[project] requires-python' (pyproject.toml) instead"
    ),
    ('metadata', 'provides_dist'): "This option is ignored by pip",
    ('metadata', 'provides_extras'): "This option is ignored by pip",
    ('metadata', 'obsoletes_dist'): "This option is ignored by pip",
    ('files', 'packages_root'): (
        "Use '[options] package_dir' (setup.cfg) or '[tools.setuptools] "
        "package_dir' (pyproject.toml) instead"
    ),
    ('files', 'packages'): (
        "Use '[options] packages' (setup.cfg) or '[tools.setuptools] "
        "packages' (pyproject.toml) instead"
    ),
    ('files', 'package_data'): (
        "Use '[options.package_data]' (setup.cfg) or "
        "'[tool.setuptools.package-data]' (pyproject.toml) instead"
    ),
    ('files', 'namespace_packages'): (
        "Use '[options] namespace_packages' (setup.cfg) or migrate to PEP "
        "420-style namespace packages instead"
    ),
    ('files', 'data_files'): (
        "For package data files, use '[options] package_data' (setup.cfg) "
        "or '[tools.setuptools] package_data' (pyproject.toml) instead. "
        "Support for non-package data files is deprecated in setuptools "
        "and their use is discouraged. If necessary, use "
        "'[options] data_files' (setup.cfg) or '[tools.setuptools] data-files'"
        "(pyproject.toml) instead."
    ),
    ('files', 'scripts'): (
        "Migrate to using the console_scripts entrypoint and use "
        "'[options.entry_points]' (setup.cfg) or '[project.scripts]' "
        "(pyproject.toml) instead"
    ),
    ('files', 'modules'): (
        "Use '[options] py_modules' (setup.cfg) or '[tools.setuptools] "
        "py-modules' (pyproject.toml) instead"
    ),
    ('backwards_compat', 'zip_safe'): (
        "This option is obsolete as it was only relevant in the context of "
        "eggs"
    ),
    ('backwards_compat', 'dependency_links'): (
        "This option is ignored by pip starting from pip 19.0"
    ),
    ('backwards_compat', 'tests_require'): (
        "This option is ignored by pip starting from pip 19.0"
    ),
    ('backwards_compat', 'include_package_data'): (
        "Use '[options] include_package_data' (setup.cfg) or "
        "'[tools.setuptools] include-package-data' (pyproject.toml) instead"
    ),
}

# setup() arguments that can have multiple values in setup.cfg
MULTI_FIELDS = (
    "classifiers",
    "platforms",
    "install_requires",
    "provides",
    "obsoletes",
    "namespace_packages",
    "packages",
    "package_data",
    "data_files",
    "scripts",
    "py_modules",
    "dependency_links",
    "setup_requires",
    "tests_require",
    "keywords",
    "cmdclass",
    "provides_extras",
)

# a mapping of removed keywords to the version of setuptools that they were deprecated in
REMOVED_KEYWORDS = {
    # https://setuptools.pypa.io/en/stable/history.html#v72-0-0
    'tests_requires': '72.0.0',
}

# setup() arguments that can have mapping values in setup.cfg
MAP_FIELDS = ("project_urls",)

# setup() arguments that contain boolean values
BOOL_FIELDS = ("zip_safe", "include_package_data")


def shlex_split(path):
    if os.name == 'nt':
        # shlex cannot handle paths that contain backslashes, treating those
        # as escape characters.
        path = path.replace("\\", "/")
        return [x.replace("/", "\\") for x in shlex.split(path)]

    return shlex.split(path)


def resolve_name(name):
    """Resolve a name like ``module.object`` to an object and return it.

    Raise ImportError if the module or name is not found.
    """
    parts = name.split('.')
    cursor = len(parts) - 1
    module_name = parts[:cursor]
    attr_name = parts[-1]

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name), fromlist=[attr_name])
            break
        except ImportError:
            if cursor == 0:
                raise
            cursor -= 1
            module_name = parts[:cursor]
            attr_name = parts[cursor]
            ret = ''

    for part in parts[cursor:]:
        try:
            ret = getattr(ret, part)
        except AttributeError:
            raise ImportError(name)

    return ret


def setup_cfg_to_args(path='setup.cfg', script_args=None):
    """Parse setup.cfg file.

    Parse a setup.cfg file and tranform pbr-specific options to the underlying
    setuptools opts.

    :param path: The setup.cfg path.
    :param script_args: List of commands setup.py was called with.
    :returns: A dictionary of kwargs to set on the underlying Distribution
        object.
    :raises DistutilsFileError: When the setup.cfg file is not found.
    """
    if script_args is None:
        script_args = ()

    # The method source code really starts here.
    parser = ConfigParser()

    if not os.path.exists(path):
        raise errors.DistutilsFileError(
            "file '%s' does not exist" % os.path.abspath(path)
        )

    try:
        parser.read(path, encoding='utf-8')
    except TypeError:
        # Python 2 doesn't accept the encoding kwarg
        parser.read(path)

    config = {}
    for section in parser.sections():
        config[section] = {}
        for k, value in parser.items(section):
            config[section][k.replace('-', '_')] = value

    # Run setup_hooks, if configured
    setup_hooks = has_get_option(config, 'global', 'setup_hooks')
    package_dir = has_get_option(config, 'files', 'packages_root')

    # Add the source package directory to sys.path in case it contains
    # additional hooks, and to make sure it's on the path before any existing
    # installations of the package
    if package_dir:
        package_dir = os.path.abspath(package_dir)
        sys.path.insert(0, package_dir)

    try:
        if setup_hooks:
            setup_hooks = [
                hook
                for hook in split_multiline(setup_hooks)
                if hook != 'pbr.hooks.setup_hook'
            ]
            for hook in setup_hooks:
                hook_fn = resolve_name(hook)
                try:
                    hook_fn(config)
                except SystemExit:
                    log.error('setup hook %s terminated the installation')
                except Exception:
                    e = sys.exc_info()[1]
                    log.error(
                        'setup hook %s raised exception: %s\n' % (hook, e)
                    )
                    log.error(traceback.format_exc())
                    sys.exit(1)

        # Run the pbr hook
        hooks.setup_hook(config)

        kwargs = setup_cfg_to_setup_kwargs(config, script_args)

        # Set default config overrides
        kwargs['include_package_data'] = True
        kwargs['zip_safe'] = False

        if has_get_option(config, 'global', 'compilers'):
            warnings.warn(
                'Support for custom compilers was removed in pbr 7.0 and the '
                '\'[global] compilers\' option is now ignored.',
                DeprecationWarning,
            )

        ext_modules = get_extension_modules(config)
        if ext_modules:
            kwargs['ext_modules'] = ext_modules

        entry_points = get_entry_points(config)
        if entry_points:
            kwargs['entry_points'] = entry_points

        # Handle the [files]/extra_files option
        files_extra_files = has_get_option(config, 'files', 'extra_files')
        if files_extra_files:
            extra_files.set_extra_files(split_multiline(files_extra_files))

    finally:
        # Perform cleanup if any paths were added to sys.path
        if package_dir:
            sys.path.pop(0)

    return kwargs


def _read_description_file(config):
    """Handle the legacy 'description_file' option."""
    long_description = has_get_option(config, 'metadata', 'long_description')
    if long_description:
        # if we have a long_description then do nothing: setuptools will take
        # care of this for us
        return None

    description_files = has_get_option(config, 'metadata', 'description_file')
    if not description_files:
        return None

    description_files = split_multiline(description_files)

    data = ''
    for filename in description_files:
        description_file = io.open(filename, encoding='utf-8')
        try:
            data += description_file.read().strip() + '\n\n'
        finally:
            description_file.close()

    return data


def setup_cfg_to_setup_kwargs(config, script_args=None):
    """Convert config options to kwargs.

    Processes the setup.cfg options and converts them to arguments accepted
    by setuptools' setup() function.
    """
    if script_args is None:
        script_args = ()

    kwargs = {}

    # Temporarily holds install_requires and extra_requires while we
    # parse env_markers.
    all_requirements = {}

    # We want people to use description and long_description over summary and
    # description but there is obvious overlap. If we see the both of the
    # former being used, don't normalize
    skip_description_normalization = False
    if has_get_option(config, 'metadata', 'description') and (
        has_get_option(config, 'metadata', 'long_description')
        or has_get_option(config, 'metadata', 'description_file')
    ):
        kwargs['description'] = has_get_option(
            config, 'metadata', 'description'
        )
        long_description = _read_description_file(config)
        if long_description:
            kwargs['long_description'] = long_description

        skip_description_normalization = True

    for alias, arg in CFG_TO_PY_SETUP_ARGS:
        section, option = alias

        if skip_description_normalization and alias in (
            ('metadata', 'summary'),
            ('metadata', 'description'),
        ):
            continue

        in_cfg_value = has_get_option(config, section, option)

        if alias == ('metadata', 'description') and not in_cfg_value:
            in_cfg_value = _read_description_file(config)

        if not in_cfg_value:
            continue

        if alias in DEPRECATED_CFG:
            warnings.warn(
                "The '[%s] %s' option is deprecated: %s"
                % (alias[0], alias[1], DEPRECATED_CFG[alias]),
                DeprecationWarning,
            )

        if arg in MULTI_FIELDS:
            in_cfg_value = split_multiline(in_cfg_value)
        elif arg in MAP_FIELDS:
            in_cfg_map = {}
            for i in split_multiline(in_cfg_value):
                k, v = i.split('=', 1)
                in_cfg_map[k.strip()] = v.strip()
            in_cfg_value = in_cfg_map
        elif arg in BOOL_FIELDS:
            # Provide some flexibility here...
            if in_cfg_value.lower() in ('true', 't', '1', 'yes', 'y'):
                in_cfg_value = True
            else:
                in_cfg_value = False

        if in_cfg_value:
            if arg in REMOVED_KEYWORDS and (
                packaging_compat.parse_version(setuptools.__version__)
                >= packaging_compat.parse_version(REMOVED_KEYWORDS[arg])
            ):
                # deprecation warnings, if any, will already have been logged,
                # so simply skip this
                continue

            if arg in ('install_requires', 'tests_require'):
                # Replaces PEP345-style version specs with the sort expected by
                # setuptools
                in_cfg_value = [
                    _VERSION_SPEC_RE.sub(r'\1\2', pred)
                    for pred in in_cfg_value
                ]

            if arg == 'install_requires':
                # Split install_requires into package,env_marker tuples
                # These will be re-assembled later
                install_requires = []
                requirement_pattern = (
                    r'(?P<package>[^;]*);?(?P<env_marker>[^#]*?)(?:\s*#.*)?$'
                )
                for requirement in in_cfg_value:
                    m = re.match(requirement_pattern, requirement)
                    requirement_package = m.group('package').strip()
                    env_marker = m.group('env_marker').strip()
                    install_requires.append((requirement_package, env_marker))
                all_requirements[''] = install_requires
            elif arg == 'package_dir':
                in_cfg_value = {'': in_cfg_value}
            elif arg in ('package_data', 'data_files'):
                data_files = {}
                firstline = True
                prev = None
                for line in in_cfg_value:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key_unquoted = shlex_split(key.strip())[0]
                        key, value = (key_unquoted, value.strip())
                        if key in data_files:
                            # Multiple duplicates of the same package name;
                            # this is for backwards compatibility of the old
                            # format prior to d2to1 0.2.6.
                            prev = data_files[key]
                            prev.extend(shlex_split(value))
                        else:
                            prev = data_files[key.strip()] = shlex_split(value)
                    elif firstline:
                        raise errors.DistutilsOptionError(
                            'malformed package_data first line %r (misses '
                            '"=")' % line
                        )
                    else:
                        prev.extend(shlex_split(line.strip()))
                    firstline = False
                if arg == 'data_files':
                    # the data_files value is a pointlessly different structure
                    # from the package_data value
                    data_files = sorted(data_files.items())
                in_cfg_value = data_files
            elif arg == 'cmdclass':
                cmdclass = {}
                dist = st_dist.Distribution()
                for cls_name in in_cfg_value:
                    cls = resolve_name(cls_name)
                    cmd = cls(dist)
                    cmdclass[cmd.get_command_name()] = cls
                in_cfg_value = cmdclass

        kwargs[arg] = in_cfg_value

    # Transform requirements with embedded environment markers to
    # setuptools' supported marker-per-requirement format.
    #
    # install_requires are treated as a special case of extras, before
    # being put back in the expected place
    #
    # fred =
    #     foo:marker
    #     bar
    # -> {'fred': ['bar'], 'fred:marker':['foo']}

    if 'extras' in config:
        requirement_pattern = (
            r'(?P<package>[^:]*):?(?P<env_marker>[^#]*?)(?:\s*#.*)?$'
        )
        extras = config['extras']
        # Add contents of test-requirements, if any, into an extra named
        # 'test' if one does not already exist.
        if 'test' not in extras:
            from pbr import packaging

            extras['test'] = "\n".join(
                packaging.parse_requirements(packaging.TEST_REQUIREMENTS_FILES)
            ).replace(';', ':')

        for extra in extras:
            extra_requirements = []
            requirements = split_multiline(extras[extra])
            for requirement in requirements:
                m = re.match(requirement_pattern, requirement)
                extras_value = m.group('package').strip()
                env_marker = m.group('env_marker')
                extra_requirements.append((extras_value, env_marker))
            all_requirements[extra] = extra_requirements

    # Transform the full list of requirements into:
    # - install_requires, for those that have no extra and no
    #   env_marker
    # - named extras, for those with an extra name (which may include
    #   an env_marker)
    # - and as a special case, install_requires with an env_marker are
    #   treated as named extras where the name is the empty string

    extras_require = {}
    for req_group in all_requirements:
        for requirement, env_marker in all_requirements[req_group]:
            if env_marker:
                extras_key = '%s:(%s)' % (req_group, env_marker)
                # We do not want to poison wheel creation with locally
                # evaluated markers.  sdists always re-create the egg_info
                # and as such do not need guarded, and pip will never call
                # multiple setup.py commands at once.
                if 'bdist_wheel' not in script_args:
                    try:
                        if packaging_compat.evaluate_marker(
                            '(%s)' % env_marker
                        ):
                            extras_key = req_group
                    except SyntaxError:
                        log.error(
                            "Marker evaluation failed, see the following "
                            "error.  For more information see: "
                            "http://docs.openstack.org/"
                            "pbr/latest/user/using.html#environment-markers"
                        )
                        raise
            else:
                extras_key = req_group
            extras_require.setdefault(extras_key, []).append(requirement)

    kwargs['install_requires'] = extras_require.pop('', [])
    kwargs['extras_require'] = extras_require

    return kwargs


def get_extension_modules(config):
    """Handle extension modules"""

    EXTENSION_FIELDS = (
        "sources",
        "include_dirs",
        "define_macros",
        "undef_macros",
        "library_dirs",
        "libraries",
        "runtime_library_dirs",
        "extra_objects",
        "extra_compile_args",
        "extra_link_args",
        "export_symbols",
        "swig_opts",
        "depends",
    )

    ext_modules = []
    for section in config:
        if ':' in section:
            labels = section.split(':', 1)
        else:
            # Backwards compatibility for old syntax; don't use this though
            labels = section.split('=', 1)
        labels = [label.strip() for label in labels]
        if (len(labels) == 2) and (labels[0] == 'extension'):
            ext_args = {}
            for field in EXTENSION_FIELDS:
                value = has_get_option(config, section, field)
                # All extension module options besides name can have multiple
                # values
                if not value:
                    continue
                value = split_multiline(value)
                if field == 'define_macros':
                    macros = []
                    for macro in value:
                        macro = macro.split('=', 1)
                        if len(macro) == 1:
                            macro = (macro[0].strip(), None)
                        else:
                            macro = (macro[0].strip(), macro[1].strip())
                        macros.append(macro)
                    value = macros
                ext_args[field] = value
            if ext_args:
                if 'name' not in ext_args:
                    ext_args['name'] = labels[1]
                ext_modules.append(
                    extension.Extension(ext_args.pop('name'), **ext_args)
                )
    return ext_modules


def get_entry_points(config):
    """Process the [entry_points] section of setup.cfg."""

    if 'entry_points' not in config:
        return {}

    warnings.warn(
        "The 'entry_points' section has been deprecated in favour of the "
        "'[options.entry_points]' section (if using 'setup.cfg') or the "
        "'[project.scripts]' and/or '[project.entry-points.{name}]' sections "
        "(if using 'pyproject.toml')",
        DeprecationWarning,
    )

    return {
        option: split_multiline(value)
        for option, value in config['entry_points'].items()
    }


def has_get_option(config, section, option):
    if section in config and option in config[section]:
        return config[section][option]
    else:
        return False


def split_multiline(value):
    """Special behaviour when we have a multi line options"""
    value = [
        element
        for element in (line.strip() for line in value.split('\n'))
        if element and not element.startswith('#')
    ]
    return value


def split_csv(value):
    """Special behaviour when we have a comma separated options"""
    value = [
        element
        for element in (chunk.strip() for chunk in value.split(','))
        if element
    ]
    return value


def pbr(dist, attr, value):
    """Implements the pbr setup() keyword.

    When used, this should be the only keyword in your setup() aside from
    `setup_requires`.

    If given as a string, the value of pbr is assumed to be the relative path
    to the setup.cfg file to use.  Otherwise, if it evaluates to true, it
    simply assumes that pbr should be used, and the default 'setup.cfg' is
    used.

    This works by reading the setup.cfg file, parsing out the supported
    metadata and command options, and using them to rebuild the
    `DistributionMetadata` object and set the newly added command options.

    The reason for doing things this way is that a custom `Distribution` class
    will not play nicely with setup_requires; however, this implementation may
    not work well with distributions that do use a `Distribution` subclass.
    """

    # Distribution.finalize_options() is what calls this method. That means
    # there is potential for recursion here. Recursion seems to be an issue
    # particularly when using PEP517 build-system configs without
    # setup_requires in setup.py. We can avoid the recursion by setting
    # this canary so we don't repeat ourselves.
    if hasattr(dist, '_pbr_initialized'):
        return
    dist._pbr_initialized = True

    if not value:
        return

    if isinstance(value, string_type):
        path = os.path.abspath(value)
    else:
        path = os.path.abspath('setup.cfg')

    if not os.path.exists(path):
        raise errors.DistutilsFileError(
            'The setup.cfg file %s does not exist.' % path
        )

    # Converts the setup.cfg file to setup() arguments
    try:
        attrs = setup_cfg_to_args(path, dist.script_args)
    except Exception:
        e = sys.exc_info()[1]
        # NB: This will output to the console if no explicit logging has
        # been setup - but thats fine, this is a fatal distutils error, so
        # being pretty isn't the #1 goal.. being diagnosable is.
        logging.exception('Error parsing')
        raise errors.DistutilsSetupError(
            'Error parsing %s: %s: %s' % (path, e.__class__.__name__, e)
        )

    # There are some metadata fields that are only supported by
    # setuptools and not distutils, and hence are not in
    # dist.metadata.  We are OK to write these in.  For gory details
    # see
    #  https://github.com/pypa/setuptools/pull/1343
    _DISTUTILS_UNSUPPORTED_METADATA = (
        'long_description_content_type',
        'project_urls',
        'provides_extras',
    )

    # Repeat some of the Distribution initialization code with the newly
    # provided attrs
    if attrs:
        # Skips 'options' and 'licence' support which are rarely used; may
        # add back in later if demanded
        for key, val in attrs.items():
            if hasattr(dist.metadata, 'set_' + key):
                getattr(dist.metadata, 'set_' + key)(val)
            elif hasattr(dist.metadata, key):
                setattr(dist.metadata, key, val)
            elif hasattr(dist, key):
                setattr(dist, key, val)
            elif key in _DISTUTILS_UNSUPPORTED_METADATA:
                setattr(dist.metadata, key, val)
            else:
                msg = 'Unknown distribution option: %s' % repr(key)
                warnings.warn(msg)

    # Re-finalize the underlying Distribution
    try:
        super(dist.__class__, dist).finalize_options()
    except TypeError:
        # If dist is not declared as a new-style class (with object as
        # a subclass) then super() will not work on it. This is the case
        # for Python 2. In that case, fall back to doing this the ugly way
        dist.__class__.__bases__[-1].finalize_options(dist)

    # This bit comes out of distribute/setuptools
    if isinstance(dist.metadata.version, integer_types + (float,)):
        # Some people apparently take "version number" too literally :)
        dist.metadata.version = str(dist.metadata.version)
