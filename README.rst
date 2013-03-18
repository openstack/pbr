Introduction
============

pbr provides a set of default python packaging configuration and
behaviors. It is implemented as a setup hook for d2to1 which allows us to
manipulate the setup.cfg information before it is passed to setup.py.

Behaviors
=========

Version strings will be inferred from git. If a given revision is tagged,
that's the version. If it's not, and you don't provide a version, the version
will be very similar to git describe. If you do, then we'll assume that's the
version you are working towards, and will generate alpha version strings
based on commits since last tag and the current git sha.

requirements.txt and test-requirements.txt will be used to populate
install requirements as needed.

Sphinx documentation setups are altered to generate man pages by default. They
also have several pieces of information that are known to setup.py injected
into the sphinx config.

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
