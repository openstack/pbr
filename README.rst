Introduction
============

.. image:: https://img.shields.io/pypi/v/pbr.svg
    :target: https://pypi.python.org/pypi/pbr/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/pbr.svg
    :target: https://pypi.python.org/pypi/pbr/
    :alt: Downloads

PBR is a library that injects some useful and sensible default behaviors
into your setuptools run. It started off life as the chunks of code that
were copied between all of the `OpenStack`_ projects. Around the time that
OpenStack hit 18 different projects each with at least 3 active branches,
it seemed like a good time to make that code into a proper reusable library.

PBR is only mildly configurable. The basic idea is that there's a decent
way to run things and if you do, you should reap the rewards, because then
it's simple and repeatable. If you want to do things differently, cool! But
you've already got the power of Python at your fingertips, so you don't
really need PBR.

PBR also aims to maintain a stable base for packaging. While we occasionally
deprecate features, we do our best to avoid removing them unless absolutely
necessary. This is important since while projects often do a good job of
constraining their runtime dependencies they often don't do so for their
install time dependencies. By limiting feature removals, we ensure the long
tail of older software continues to be installable with recent versions of PBR
automatically installed.

PBR builds on top of the work that `d2to1`_ started to provide for declarative
configuration. `d2to1`_ is itself an implementation of the ideas behind
`distutils2`_. Although `distutils2`_ is long-since abandoned, declarative
config is still a great idea and it has since been adopted elsewhere, starting
with setuptools' own support for ``setup.cfg`` files and extending to the
``pyproject.toml`` file format introduced in `PEP 517`_. PBR attempts to
support these changes as they are introduced.

* License: Apache License, Version 2.0
* Documentation: https://docs.openstack.org/pbr/latest/
* Source: https://opendev.org/openstack/pbr
* Bugs: https://bugs.launchpad.net/pbr
* Release Notes: https://docs.openstack.org/pbr/latest/user/releasenotes.html
* ChangeLog: https://docs.openstack.org/pbr/latest/user/history.html

.. _d2to1: https://pypi.python.org/pypi/d2to1
.. _distutils2: https://pypi.python.org/pypi/Distutils2
.. _OpenStack: https://www.openstack.org/
.. _PEP 517: https://peps.python.org/pep-0517/
