# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from __future__ import absolute_import
from __future__ import print_function

import argparse
import sys

import pbr._compat.metadata
import pbr.version


def get_sha(args):
    sha = _get_info(args.name)['sha']
    if sha:
        print(sha)


def get_info(args):
    if args.short:
        print("{version}".format(**_get_info(args.name)))
    else:
        print(
            "{name}\t{version}\t{released}\t{sha}".format(
                **_get_info(args.name)
            )
        )


def _get_info(package_name):
    metadata = pbr._compat.metadata.get_metadata(package_name)
    version = pbr._compat.metadata.get_version(package_name)

    if metadata:
        if metadata['is_release']:
            released = 'released'
        else:
            released = 'pre-release'
        sha = metadata['git_version']
    else:
        version_parts = version.split('.')
        if version_parts[-1].startswith('g'):
            sha = version_parts[-1][1:]
            released = 'pre-release'
        else:
            sha = ""
            released = "released"
            for part in version_parts:
                if not part.isdigit():
                    released = "pre-release"

    return {
        'name': package_name,
        'version': version,
        'sha': sha,
        'released': released,
    }


def freeze(args):
    for dist in pbr._compat.metadata.get_distributions():
        info = _get_info(dist.project_name)
        output = "{name}=={version}".format(**info)
        if info['sha']:
            output += "  # git sha {sha}".format(**info)
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description='pbr: Python Build Reasonableness'
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=str(pbr.version.VersionInfo('pbr')),
    )

    subparsers = parser.add_subparsers(
        title='commands',
        description='valid commands',
        help='additional help',
        dest='cmd',
    )
    subparsers.required = True

    cmd_sha = subparsers.add_parser('sha', help='print sha of package')
    cmd_sha.set_defaults(func=get_sha)
    cmd_sha.add_argument('name', help='package to print sha of')

    cmd_info = subparsers.add_parser(
        'info', help='print version info for package'
    )
    cmd_info.set_defaults(func=get_info)
    cmd_info.add_argument('name', help='package to print info of')
    cmd_info.add_argument(
        '-s',
        '--short',
        action="store_true",
        help='only display package version',
    )

    cmd_freeze = subparsers.add_parser(
        'freeze', help='print version info for all installed packages'
    )
    cmd_freeze.set_defaults(func=freeze)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    sys.exit(main())
