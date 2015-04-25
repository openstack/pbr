=================================
pbr - Python Build Reasonableness
=================================

A library for managing setuptools packaging needs in a consistent manner.

`pbr` reads and then filters the `setup.cfg` data through a setup hook to
fill in default values and provide more sensible behaviors, and then feeds
the results in as the arguments to a call to `setup.py` - so the heavy
lifting of handling python packaging needs is still being done by
`setuptools`.

Note that we don't support the `easy_install` aspects of setuptools: while
we depend on setup_requires, for any install_requires we recommend that they
be installed prior to running `setup.py install` - either by hand, or by using
an install tool such as `pip`.

What It Does
============

PBR can and does do a bunch of things for you:

 * **Version**: Manage version number based on git revisions and tags
 * **AUTHORS**: Generate AUTHORS file from git log
 * **ChangeLog**: Generate ChangeLog from git log
 * **Sphinx Autodoc**: Generate autodoc stub files for your whole module
 * **Requirements**: Store your dependencies in a pip requirements file
 * **long_description**: Use your README file as a long_description
 * **Smart find_packages**: Smartly find packages under your root package

Version
-------

Versions can be managed two ways - postversioning and preversioning.
Postversioning is the default, and preversioning is enabeld by setting
``version`` in the setup.cfg ``metadata`` section. In both cases
version strings are inferred from git.

If a given revision is tagged, that's the version.

If it's not, then we take the last tagged version number and increment it to
get a minimum target version.

We then walk git history back to the last release. Within each commit we look
for a Sem-Ver: pseudo header, and if found parse it looking for keywords.
Unknown symbols are not an error (so that folk can't wedge pbr or break their
tree), but we will emit an info level warning message.  Known symbols:
``feature``, ``api-break``, ``deprecation``, ``bugfix``. A missing
Sem-Ver line is equivalent to ``Sem-Ver: bugfix``. The ``bugfix`` symbol causes
a patch level increment to the version. The ``feature`` and ``deprecation``
symbols cause a minor version increment. The ``api-break`` symbol causes a
major version increment.

If postversioning is in use, we use the resulting version number as the target
version.

If preversioning is in use - that is if there is a version set in setup.cfg
metadata - then we check that that version is higher than the target version
we inferred above. If it is not, we raise an error, otherwise we use the
version from setup.cfg as the target.

We then generate dev version strings based on the commits since the last
release and include the current git sha to disambiguate multiple dev versions
with the same number of commits since the release.

.. note::

   Note that `pbr` expects git tags to be signed, for using it to
   calculate version.

The versions are expected to be compliant with :doc:`semver`.

The ``version.SemanticVersion`` class can be used to query versions of a
package and present it in various forms - ``debian_version()``,
``release_string()``, ``rpm_string()``, ``version_string()``, or
``version_tuple()``.

AUTHORS and ChangeLog
---------------------

Why keep an AUTHORS or a ChangeLog file, when git already has all of the
information you need. AUTHORS generation supports filtering/combining based
on a standard .mailmap file.

Sphinx Autodoc
--------------

Sphinx can produce auto documentation indexes based on signatures and
docstrings of your project- but you have to give it index files to tell it
to autodoc each module. That's kind of repetitive and boring. PBR will
scan your project, find all of your modules, and generate all of the stub
files for you.

Sphinx documentation setups are altered to generate man pages by default. They
also have several pieces of information that are known to setup.py injected
into the sphinx config.

Requirements
------------

You may not have noticed, but there are differences in how pip
requirements.txt files work and how distutils wants to be told about
requirements. The pip way is nicer, because it sure does make it easier to
populate a virtualenv for testing, or to just install everything you need.
Duplicating the information, though, is super lame. So PBR will let you
keep requirements.txt format files around describing the requirements for
your project, will parse them and split them up appropriately, and inject
them into the install_requires and/or tests_require and/or dependency_links
arguments to setup. Voila!

You can also have a requirement file for each specific major version of
Python. If you want to have a different package list for Python 3, just drop
a requirements-py3.txt, and it will be used instead.

The requirement files are tried in that order (N being the Python major
version number used to install the package):

* requirements-pyN.txt
* tools/pip-requires-py3
* requirements.txt
* tools/pip-requires

Only the first file found is used to install the list of packages it
contains.

long_description
----------------

There is no need to maintain two long descriptions- and your README file is
probably a good long_description. So we'll just inject the contents of your
README.rst, README.txt or README file into your empty long_description. Yay
for you.

Usage
=====
pbr requires a distribution to use distribute.  Your distribution
must include a distutils2-like setup.cfg file, and a minimal setup.py script.

A simple sample can be found in pbr's own setup.cfg
(it uses its own machinery to install itself)::

 [metadata]
 name = pbr
 author = OpenStack Foundation
 author-email = openstack-dev@lists.openstack.org
 summary = OpenStack's setup automation in a reusable form
 description-file = README
 license = Apache-2
 classifier =
     Development Status :: 4 - Beta
         Environment :: Console
         Environment :: OpenStack
         Intended Audience :: Developers
         Intended Audience :: Information Technology
         License :: OSI Approved :: Apache Software License
         Operating System :: OS Independent
         Programming Language :: Python
 keywords =
     setup
     distutils
 [files]
 packages =
     pbr
 data_files =
     etc/pbr = etc/*
     etc/init =
         pbr.packaging.conf
         pbr.version.conf
 [entry_points]
 console_scripts =
     pbr = pbr.cmd:main
 pbr.config.drivers =
     plain = pbr.cfg.driver:Plain

The minimal setup.py should look something like this::

 #!/usr/bin/env python

 from setuptools import setup

 setup(
     setup_requires=['pbr'],
     pbr=True,
 )

Note that it's important to specify `pbr=True` or else the pbr functionality
will not be enabled.

It should also work fine if additional arguments are passed to `setup()`,
but it should be noted that they will be clobbered by any options in the
setup.cfg file.

files
-----

The format of the files section is worth explaining. There are three
fundamental keys one is likely to care about, `packages`,
`namespace_packages`, and `data_files`.

`packages` is a list of top-level packages that should be installed. The
behavior of packages is similar to `setuptools.find_packages` in that it
recurses the python package hierarchy below the given top level and installs
all of it. If `packages` is not specified, it defaults to the name given
in the `[metadata]` section.

`namespace_packages` is the same, but is a list of packages that provide
namespace packages.

`data_files` lists files to be installed. The format is an indented block
that contains key value pairs which specify target directory and source
file to install there. More than one source file for a directory may be
indicated with a further indented list. Source files are stripped of leading
directories. Additionally, `pbr` supports a simple file globbing syntax
for installing entire directory structures, so::

 [files]
 data_files =
     etc/pbr = etc/pbr/*
     etc/neutron =
         etc/api-paste.ini
         etc/dhcp-agent.ini
     etc/init.d = neutron.init

Will result in `/etc/neutron` containing `api-paste.ini` and `dhcp-agent.ini`,
both of which pbr will expect to find in the `etc` directory in the root of
the source tree. Additionally, `neutron.init` from that dir will be installed
in `/etc/init.d`.

All of the files and directories located under `etc/pbr` in the source tree
will be installed into `/etc/pbr`.

entry_points
------------

The general syntax of specifying entry points is a top level name indicating
the entry point group name, followed by one or more key value pairs naming
the entry point to be installed. For instance::

 [entry_points]
 console_scripts =
     pbr = pbr.cmd:main
 pbr.config.drivers =
     plain = pbr.cfg.driver:Plain
     fancy = pbr.cfg.driver:Fancy

Will cause a console script called `pbr` to be installed that executes the
`main` function found in `pbr.cmd`. Additionally, two entry points will be
installed for `pbr.config.drivers`, one called `plain` which maps to the
`Plain` class in `pbr.cfg.driver` and one called `fancy` which maps to the
`Fancy` class in `pbr.cfg.driver`.

Additional Docs
===============

.. toctree::
   :maxdepth: 1

   packagers
   semver
   testing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
