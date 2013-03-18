Introduction
============

PBR is a library that injects some useful and sensible default behaviors
into your setuptools run. It started off life as the chunks of code that
were copied between all of the OpenStack projects. Around the time that
OpenStack hit 18 different projects each with at least 3 active branches,
it seems like a good time to make that code into a proper re-usable library.

PBR is only mildly configurable. The basic idea is that there's a decent
way to run things and if you do, you should reap the rewards, because then
it's simple and repeatable. If you want to do things differently, cool! But
you've already got the power of python at your fingertips, so you don't
really need PBR.

PBR builds on top of `d2to1` to provide for declarative configuration. It
then filters the `setup.cfg` data through a setup hook to fill in default
values and provide more sensible behaviors.

Behaviors
=========

What It Does
------------

PBR can and does do a bunch of things for you:

 * **Version**: Manage version number bad on git revisions and tags
 * **AUTHORS**: Generate AUTHORS file from git log
 * **ChangeLog**: Generate ChangeLog from git log
 * **Sphinx Autodoc**: Generate autodoc stub files for your whole module
 * **Requirements**: Store your dependencies in a pip requirements file
 * **long_description**: Use your README file as a long_description
 * **Smart find_packages**: Smartly find packages under your root package

Version
^^^^^^^

Version strings will be inferred from git. If a given revision is tagged,
that's the version. If it's not, and you don't provide a version, the version
will be very similar to git describe. If you do, then we'll assume that's the
version you are working towards, and will generate alpha version strings
based on commits since last tag and the current git sha.

AUTHORS and ChangeLog
^^^^^^^^^^^^^^^^^^^^^

Why keep an AUTHORS or a ChangeLog file, when git already has all of the
information you need. AUTHORS generation supports filtering/combining based
on a standard .mailmap file.

Sphinx Autodoc
^^^^^^^^^^^^^^

Sphinx can produce auto documentation indexes based on signatures and
docstrings of your project- but you have to give it index files to tell it
to autodoc each module. That's kind of repetitive and boring. PBR will
scan your project, find all of your modules, and generate all of the stub
files for you.

Sphinx documentation setups are altered to generate man pages by default. They
also have several pieces of information that are known to setup.py injected
into the sphinx config.

Requirements
^^^^^^^^^^^^

You may not have noticed, but there are differences in how pip
requirements.txt files work and how distutils wants to be told about
requirements. The pip way is nicer, because it sure does make it easier to
popuplate a virtualenv for testing, or to just install everything you need.
Duplicating the information, though, is super lame. So PBR will let you
keep requirements.txt format files around describing the requirements for
your project, will parse them and split them up approprirately, and inject
them into the install_requires and/or tests_require and/or dependency_links
arguments to setup. Voila!

long_description
^^^^^^^^^^^^^^^^

There is no need to maintain two long descriptions- and your README file is
probably a good long_description. So we'll just inject the contents of your
README.rst, README.txt or README file into your empty long_description. Yay
for you.

Usage
=====
pbr requires a distribution to use distribute.  Your distribution
must include a distutils2-like setup.cfg file, and a minimal setup.py script.

A simple sample can be found in pbr s own setup.cfg
(it uses its own machinery to install itself)::

 [metadata]
 name = pbr
 author = OpenStack Foundation
 author-email = openstack-dev@lists.openstack.org
 summary = OpenStack's setup automation in a reuable form
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
     oslo
 [hooks]
 setup-hooks =
     pbr.hooks.setup_hook

The minimal setup.py should look something like this::

 #!/usr/bin/env python

 from setuptools import setup

 setup(
     setup_requires=['d2to1', 'pbr'],
     d2to1=True,
 )

Note that it's important to specify `d2to1=True` or else the pbr functionality
will not be enabled.

It should also work fine if additional arguments are passed to `setup()`,
but it should be noted that they will be clobbered by any options in the
setup.cfg file.

Running Tests
=============
The testing system is based on a combination of tox and testr. The canonical
approach to running tests is to simply run the command `tox`. This will
create virtual environments, populate them with depenedencies and run all of
the tests that OpenStack CI systems run. Behind the scenes, tox is running
`testr run --parallel`, but is set up such that you can supply any additional
testr arguments that are needed to tox. For example, you can run:
`tox -- --analyze-isolation` to cause tox to tell testr to add
--analyze-isolation to its argument list.

It is also possible to run the tests inside of a virtual environment
you have created, or it is possible that you have all of the dependencies
installed locally already. If you'd like to go this route, the requirements
are listed in requirements.txt and the requirements for testing are in
test-requirements.txt. Installing them via pip, for instance, is simply::

  pip install -r requirements.txt -r test-requirements.txt

In you go this route, you can interact with the testr command directly.
Running `testr run` will run the entire test suite. `testr run --parallel`
will run it in parallel (this is the default incantation tox uses.) More
information about testr can be found at: http://wiki.openstack.org/testr
