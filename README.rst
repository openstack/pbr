Introduction
============

oslo.packaging provides a set of default python packaging configuration and
behaviors. It started off as a combination of an invasive fork of d2to1
and the openstack.common.setup module.

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
oslo.packaging requires a distribution to use distribute.  Your distribution
must include a distutils2-like setup.cfg file, and a minimal
setup.py script. The purpose is not to actually support distutils2, that's
turned in to a boondoggle. However, having declarative setup is a great idea,
and we can have that now if we don't care about distutils2 ever being finished.

A simple sample can be found in oslo.packaging s own setup.cfg
(it uses its own machinery to install itself)::

 [metadata]
 name = oslo.packaging
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
     oslo.packaging

The minimal setup.py should look something like this::

 #!/usr/bin/env python

 from setuptools import setup

 setup(
     setup_requires=['oslo.packaging'],
     oslo_packaging=True
 )

Note that it's important to specify oslo_packaging=True or else the
oslo.packaging functionality will not be enabled.

It should also work fine if additional arguments are passed to `setup()`,
but it should be noted that they will be clobbered by any options in the
setup.cfg file.
