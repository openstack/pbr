# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Most of this code is copied from setuptools ([1], [2]), licensed under the
# MIT license
#
# [1] https://github.com/pypa/setuptools/blob/v67.8.0/setuptools/command/easy_install.py
# [2] https://github.com/pypa/setuptools/blob/v67.8.0/setuptools/_distutils/spawn.py

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import re
import shlex
import subprocess
import sys
import textwrap
import warnings

import pbr._compat.metadata


shebang_pattern = re.compile('^#!.*python[0-9.]*([ \t].*)?$')
"""
Pattern matching a Python interpreter indicated in first line of a script.
"""


def isascii(s):
    try:
        s.encode('ascii')
    except UnicodeError:
        return False
    return True


def find_executable(executable, path=None):
    """Tries to find 'executable' in the directories listed in 'path'.

    A string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH'].  Returns the complete filename or None if not found.
    """
    _, ext = os.path.splitext(executable)
    if (sys.platform == 'win32') and (ext != '.exe'):
        executable = executable + '.exe'

    if os.path.isfile(executable):
        return executable

    if path is None:
        path = os.environ.get('PATH', None)
        if path is None:
            try:
                path = os.confstr("CS_PATH")
            except (AttributeError, ValueError):
                # os.confstr() or CS_PATH is not available
                path = os.defpath
        # bpo-35755: Don't use os.defpath if the PATH environment variable is
        # set to an empty string

    # PATH='' doesn't match, whereas PATH=':' looks in the current directory
    if not path:
        return None

    paths = path.split(os.pathsep)
    for p in paths:
        f = os.path.join(p, executable)
        if os.path.isfile(f):
            # the file exists, we have a shot at spawn working
            return f
    return None


class CommandSpec(list):
    """
    A command spec for a #! header, specified as a list of arguments akin to
    those passed to Popen.
    """

    options = []  # type: list[str]
    split_args = dict()  # type: dict[str, bool]

    @classmethod
    def best(cls):
        """
        Choose the best CommandSpec class based on environmental conditions.
        """
        return cls

    @classmethod
    def _sys_executable(cls):
        _default = os.path.normpath(sys.executable)
        return os.environ.get('__PYVENV_LAUNCHER__', _default)

    @classmethod
    def from_param(cls, param):
        """
        Construct a CommandSpec from a parameter to build_scripts, which may
        be None.
        """
        if isinstance(param, cls):
            return param
        if isinstance(param, list):
            return cls(param)
        if param is None:
            return cls.from_environment()
        # otherwise, assume it's a string.
        return cls.from_string(param)

    @classmethod
    def from_environment(cls):
        return cls([cls._sys_executable()])

    @classmethod
    def from_string(cls, string):
        """
        Construct a command spec from a simple string representing a command
        line parseable by shlex.split.
        """
        items = shlex.split(string, **cls.split_args)
        return cls(items)

    def install_options(self, script_text):
        self.options = shlex.split(self._extract_options(script_text))
        cmdline = subprocess.list2cmdline(self)
        if not isascii(cmdline):
            self.options[:0] = ['-x']

    @staticmethod
    def _extract_options(orig_script):
        """
        Extract any options from the first line of the script.
        """
        first = (orig_script + '\n').splitlines()[0]
        match = shebang_pattern.match(first)
        options = match.group(1) or '' if match else ''
        return options.strip()

    def as_header(self):
        return self._render(self + list(self.options))

    @staticmethod
    def _strip_quotes(item):
        _QUOTES = '"\''
        for q in _QUOTES:
            if item.startswith(q) and item.endswith(q):
                return item[1:-1]
        return item

    @staticmethod
    def _render(items):
        cmdline = subprocess.list2cmdline(
            CommandSpec._strip_quotes(item.strip()) for item in items
        )
        return '#!' + cmdline + '\n'


sys_executable = CommandSpec._sys_executable


class WindowsCommandSpec(CommandSpec):
    split_args = dict(posix=False)


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


class ScriptWriter:
    """
    Encapsulates behavior around writing entry point scripts for console and
    gui apps.
    """

    command_spec_class = CommandSpec

    @classmethod
    def get_script_args(cls, dist, executable=None, wininst=False):
        # NOTE(stephenfin): This was deprecated upstream. We opt not to
        # deprecate it here.
        writer = (WindowsScriptWriter if wininst else ScriptWriter).best()
        header = cls.get_script_header("", executable, wininst)
        return writer.get_args(dist, header)

    @classmethod
    def get_script_header(cls, script_text, executable=None, wininst=False):
        # NOTE(stephenfin): This was deprecated upstream. We opt not to
        # deprecate it here.
        if wininst:
            executable = "python.exe"
        return cls.get_header(script_text, executable)

    @classmethod
    def get_args(cls, dist, header=None):
        """
        Yield write_script() argument tuples for a distribution's
        console_scripts and gui_scripts entry points.
        """
        # NOTE(stephenfin): This is modified from upstream to add support for
        # wsgi-scripts. The Windows version is unchanged.
        if header is None:
            header = cls.get_header()

        for group, template in ENTRY_POINTS_MAP.items():
            for name, ep in pbr._compat.metadata.get_entry_points(dist, group):
                cls._ensure_safe_name(name)
                yield (name, generate_script(group, ep, header, template))

    @staticmethod
    def _ensure_safe_name(name):
        """
        Prevent paths in *_scripts entry point names.
        """
        has_path_sep = re.search(r'[\\/]', name)
        if has_path_sep:
            raise ValueError("Path separators not allowed in script names")

    @classmethod
    def best(cls):
        """
        Select the best ScriptWriter for this environment.
        """
        if sys.platform == 'win32' or (os.name == 'java' and os._name == 'nt'):
            return WindowsScriptWriter.best()
        else:
            return cls

    @classmethod
    def _get_script_args(cls, type_, name, header, script_text):
        # Simply write the stub with no extension.
        yield (name, header + script_text)

    @classmethod
    def get_header(cls, script_text="", executable=None):
        """Create a #! line, getting options (if any) from script_text"""
        cmd = cls.command_spec_class.best().from_param(executable)
        cmd.install_options(script_text)
        return cmd.as_header()


class WindowsScriptWriter(ScriptWriter):
    template = textwrap.dedent(
        r"""
        # EASY-INSTALL-ENTRY-SCRIPT: %(spec)r,%(group)r,%(name)r
        import re
        import sys

        # for compatibility with easy_install; see #2198
        __requires__ = %(spec)r

        try:
            from importlib.metadata import distribution
        except ImportError:
            try:
                from importlib_metadata import distribution
            except ImportError:
                from pkg_resources import load_entry_point


        def importlib_load_entry_point(spec, group, name):
            dist_name, _, _ = spec.partition('==')
            matches = (
                entry_point
                for entry_point in distribution(dist_name).entry_points
                if entry_point.group == group and entry_point.name == name
            )
            return next(matches).load()


        globals().setdefault('load_entry_point', importlib_load_entry_point)


        if __name__ == '__main__':
            sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
            sys.exit(load_entry_point(%(spec)r, %(group)r, %(name)r)())
        """
    ).lstrip()

    command_spec_class = WindowsCommandSpec

    @classmethod
    def get_args(cls, dist, header=None):
        """
        Yield write_script() argument tuples for a distribution's
        console_scripts and gui_scripts entry points.
        """
        if header is None:
            header = cls.get_header()
        spec = str(dist.as_requirement())
        for type_ in 'console', 'gui':
            group = type_ + '_scripts'
            for name, ep in pbr._compat.metadata.get_entry_points(dist, group):
                cls._ensure_safe_name(name)
                script_text = cls.template % {
                    'spec': spec,
                    'group': group,
                    'name': name,
                }
                args = cls._get_script_args(type_, name, header, script_text)
                for res in args:
                    yield res

    @classmethod
    def best(cls):
        """
        Select the best ScriptWriter suitable for Windows
        """
        # NOTE(stephenfin): We don't support the
        # WindowsExecutableLauncherWriter since it has a significant dependency
        # on pkg_resources
        return cls

    @classmethod
    def _get_script_args(cls, type_, name, header, script_text):
        "For Windows, add a .py extension"
        ext = dict(console='.pya', gui='.pyw')[type_]
        if ext not in os.environ['PATHEXT'].lower().split(';'):
            msg = (
                "{ext} not listed in PATHEXT; scripts will not be "
                "recognized as executables."
            ).format(ext=ext)
            warnings.warn(msg, UserWarning)
        old = ['.pya', '.py', '-script.py', '.pyc', '.pyo', '.pyw', '.exe']
        old.remove(ext)
        header = cls._adjust_header(type_, header)
        blockers = [name + x for x in old]
        yield name + ext, header + script_text, 't', blockers

    @classmethod
    def _adjust_header(cls, type_, orig_header):
        """
        Make sure 'pythonw' is used for gui and 'python' is used for
        console (regardless of what sys.executable is).
        """
        pattern = 'pythonw.exe'
        repl = 'python.exe'
        if type_ == 'gui':
            pattern, repl = repl, pattern
        pattern_ob = re.compile(re.escape(pattern), re.IGNORECASE)
        new_header = pattern_ob.sub(string=orig_header, repl=repl)
        return new_header if cls._use_header(new_header) else orig_header

    @staticmethod
    def _use_header(new_header):
        """
        Should _adjust_header use the replaced header?

        On non-windows systems, always use. On
        Windows systems, only use the replaced header if it resolves
        to an executable on the system.
        """
        clean_header = new_header[2:-1].strip('"')
        return sys.platform != 'win32' or find_executable(clean_header)


# for backward-compatibility
get_script_args = ScriptWriter.get_script_args
get_script_header = ScriptWriter.get_script_header
