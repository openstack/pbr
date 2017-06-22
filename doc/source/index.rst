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

PBR can and does do a bunch of things for you:

* **Version**: Manage version number based on git revisions and tags
* **AUTHORS**: Generate AUTHORS file from git log
* **ChangeLog**: Generate ChangeLog from git log
* **Manifest**: Generate a sensible manifest from git files and some standard
  files
* **Sphinx Autodoc**: Generate autodoc stub files for your whole module
* **Requirements**: Store your dependencies in a pip requirements file
* **long_description**: Use your README file as a long_description
* **Smart find_packages**: Smartly find packages under your root package

Contents:

.. toctree::
   :maxdepth: 2

   user/index
   reference/index
   contributor/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _"extra" requirements:
 https://www.python.org/dev/peps/pep-0426/#extras-optional-dependencies
.. _conditional dependencies:
 https://www.python.org/dev/peps/pep-0426/#environment-markers
.. _distutils2: http://alexis.notmyidea.org/distutils2/setupcfg.html
.. _sphinx-apidoc man page: http://sphinx-doc.org/man/sphinx-apidoc.html
.. _Sphinx build configuration file: http://sphinx-doc.org/config.html
