=======
 Usage
=======

*pbr* is a *setuptools* plugin and so to use it you must use *setuptools* and
call ``setuptools.setup()``. While the normal *setuptools* facilities are
available, *pbr* makes it possible to express them through static data files.

.. _setup_py:

``setup.py``
------------

*pbr* only requires a minimal ``setup.py`` file compared to a standard
*setuptools* project. This is because most configuration is located in static
configuration files. This recommended minimal ``setup.py`` file should look
something like this:

.. code-block:: python

    #!/usr/bin/env python

    from setuptools import setup

    setup(
        setup_requires=['pbr'],
        pbr=True,
    )

.. note::

   It is necessary to specify ``pbr=True`` to enabled *pbr* functionality.

.. note::

   While one can pass any arguments supported by setuptools to ``setup()``,
   any conflicting arguments supplied in ``pyproject.toml`` or ``setup.cfg``
   will take precedence.

Once configured, you can place your configuration into either
``pyproject.toml`` or ``setup.cfg``.

``pyproject.toml``
------------------

*If your project only supports Python 3.7 or newer*, PBR can be configured as a
PEP517 build-system in ``pyproject.toml``. The main benefits are that you can
control the versions of PBR and setuptools that are used avoiding easy_install
invocation. Your ``[build-system]`` block in ``pyproject.toml`` will need to
look like this:

.. code-block:: toml

    [build-system]
    requires = ["pbr>=6.1.1"]
    build-backend = "pbr.build"

Eventually PBR may grow its own direct support for PEP517 build hooks, but
until then it will continue to need setuptools with a minimal ``setup.py`` and
``setup.cfg`` as follows. First, ``setup.py``:

.. code-block:: python

    import setuptools
    setuptools.setup(pbr=True)

Then ``setup.cfg``:

.. code-block:: ini

    [metadata]
    name = my_project

Almost all other metadata can be placed into ``pyproject.toml``. A simple example:

.. code-block:: toml

    [project]
    name = "my_project"
    description = "A brief one-line descriptive title of my project"
    authors = [
        {name = "John Doe", email = "john@example.com"},
    ]
    requires-python = ">=3.10"
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Utilities",
    ]
    keywords = ["commandline", "utility"]
    readme = "README.rst"

    [project.scripts]
    my-project = "my_project.cmd:main"

    [project.urls]
    Homepage = "https://my-project.example.org/"
    "Bug Tracker" = "https://my-project.example.org/bugs/"
    Documentation = "https://my-project.example.org/docs/"
    "Release Notes" = "https://my-project.example.org/releasenotes/"
    "Source Code" = "https://my-project.example.org/code/"

    [tool.setuptools]
    packages = ["my_project"]

.. _setup_cfg:

``setup.cfg``
-------------

The ``setup.cfg`` file is an INI-like file that can mostly replace the
``setup.py`` file. It is similar to the ``setup.cfg`` file found in recent
versions of `setuptools`__. As with setuptools itself, you need to retain a
minimal ``setup.py`` as follows:

.. code-block:: python

    import setuptools
    setuptools.setup(pbr=True)

All other metadata can be placed in your ``setup.cfg``. A simple example:

.. code-block:: ini

    [metadata]
    name = my_project
    description = A brief one-line descriptive title of my project
    author = John Doe
    author_email = john@example.com
    classifiers =
        Development Status :: 5 - Production/Stable
        Environment :: Console
        Intended Audience :: Developers
        Intended Audience :: Information Technology
        License :: OSI Approved :: Apache Software License
        Operating System :: OS Independent
        Programming Language :: Python
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.10
        Programming Language :: Python :: 3.11
        Programming Language :: Python :: 3.12
        Programming Language :: Python :: 3.13
        Topic :: Utilities
    keywords = commandline utility
    long_description = file: README.rst
    long_description_content_type = text/x-rst; charset=UTF-8
    project_urls =
        Homepage = https://my-project.example.org/
        Bug Tracker = https://my-project.example.org/bugs/
        Documentation = https://my-project.example.org/docs/
        Release Notes = https://my-project.example.org/releasenotes/
        Source Code = https://my-project.example.org/code/

    [options]
    python_requires = >=3.10
    packages =
        my_project

    [options.entry_points]
    console_scripts =
        my-project = my_project.cmd:main

Recent versions of `setuptools`_ provide many of the same sections as *pbr*.
*pbr*'s support for setup.cfg predates that of setuptools'. For this reason
*pbr* supports sections and functionality that setuptools never adopted.
These sections are:

- ``files`` (deprecated)
- ``entry_points`` (deprecated)
- ``backwards_compat`` (deprecated)
- ``pbr``

In addition, there are some modifications to other sections:

- ``metadata``

For all other sections, you should refer to either the `setuptools`_
documentation or the documentation of the package that provides the section,
such as the ``extract_messages`` section provided by Babel__.

.. note::

   Comments may be used in ``setup.cfg``, however all comments should start
   with a ``#`` and may be on a single line, or in line, with at least one
   white space character immediately preceding the ``#``. Semicolons are not a
   supported comment delimiter. For instance:

   .. code-block:: ini

       [section]
       # A comment at the start of a dedicated line
       key =
           value1 # An in line comment
           value2
           # A comment on a dedicated line
           value3

.. note::

   On Python 3 ``setup.cfg`` is explicitly read as UTF-8.  On Python 2 the
   encoding is dependent on the terminal encoding.

__ http://setuptools.readthedocs.io/en/latest/setuptools.html#configuring-setup-using-setup-cfg-files
__ http://babel.pocoo.org/en/latest/setup.html

``files``
~~~~~~~~~

The ``files`` section defines the install location of files in the package.

.. deprecated:: 7.0.0

    `setuptools v30.3.0`__ introduced built-in support for configuring the
    below information via the ``[options]`` section in ``setup.cfg``, while
    `setuptools v68.1.0`__ adds support for doing this via ``pyproject.toml``
    using the ``[tool.setuptools]`` section. For example, given the following
    ``setup.cfg`` configuration:

    .. code-block:: ini

        [files]
        packages =
            foo
        namespace_packages =
            fooext
        data_files =
            etc/foo = etc/foo/*
            etc/foo-api =
                etc/api-paste.ini
            etc/init.d = foo.init

    You can represent this in ``setup.cfg`` like so:

    .. code-block:: ini

        [options]
        packages =
            foo
        namespace_packages =
            fooext

        [options.data_files]
        etc/foo = etc/foo/*
        etc/foo-api =
            etc/api-paste.ini
        etc/init.d = foo.init

    Neither namespace packages nor non-package data files are supported in
    ``pyproject.toml`` format so only ``[files] packages`` can be migrated in
    this example:

    .. code-block:: toml

        [tool.setuptools]
        packages = ["foo"]

    For more information, refer to the `Configuring setuptools using setup.cfg
    files`__, `Package Discovery and Namespace Packages`__ and `Data Files
    Support`__ documents in the setuptools docs.

    .. __: https://pypi.org/project/setuptools/30.3.0/
    .. __: https://pypi.org/project/setuptools/68.1.0/
    .. __: https://setuptools.pypa.io/en/latest/userguide/declarative_config.html
    .. __: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html
    .. __: https://setuptools.pypa.io/en/latest/userguide/datafiles.html

The ``files`` section uses three fundamental keys: ``packages``,
``namespace_packages``, and ``data_files``.

``packages``
  A list of top-level packages that should be installed. The behavior of
  packages is similar to ``setuptools.find_packages`` in that it recurses the
  Python package hierarchy below the given top level and installs all of it. If
  ``packages`` is not specified, it defaults to the value of the ``name`` field
  given in the ``[metadata]`` section. For example:

  .. code-block:: ini

      [files]
      packages =
          pbr

``namespace_packages``
  Similar to ``packages``, but is a list of packages that provide namespace
  packages. For example:

  .. code-block:: ini

      [files]
      namespace_packages =
          pbrext

``data_files``
  A list of files to be installed. The format is an indented block that
  contains key value pairs which specify target directory and source file to
  install there. More than one source file for a directory may be indicated
  with a further indented list. Source files are stripped of leading
  directories. Additionally, *pbr* supports a simple file globbing syntax for
  installing entire directory structures. For example:

  .. code-block:: ini

      [files]
      data_files =
          etc/pbr = etc/pbr/*
          etc/neutron =
              etc/api-paste.ini
              etc/dhcp-agent.ini
          etc/init.d = neutron.init

  This will result in ``/etc/neutron`` containing ``api-paste.ini`` and
  ``dhcp-agent.ini``, both of which *pbr* will expect to find in the ``etc``
  directory in the root of the source tree. Additionally, ``neutron.init`` from
  that directory will be installed in ``/etc/init.d``. All of the files and
  directories located under ``etc/pbr`` in the source tree will be installed
  into ``/etc/pbr``.

  Note that this behavior is relative to the effective root of the environment
  into which the packages are installed, so depending on available permissions
  this could be the actual system-wide ``/etc`` directory or just a top-level
  ``etc`` subdirectory of a *virtualenv*.

``entry_points``
~~~~~~~~~~~~~~~~

The ``entry_points`` section defines entry points for generated console scripts
and Python libraries.

.. deprecated:: 7.0.0

    `setuptools v30.3.0`__ introduced built-in support for configuring the
    below information via the ``[options.entry_points]`` section in
    ``setup.cfg``, while `setuptools v68.1.0`__ adds support for doing this via
    ``pyproject.toml`` using the ``[project.scripts]`` section. For example,
    given the following ``setup.cfg`` configuration:

    .. code-block:: ini

        [entry_points]
        console_scripts =
            pbr = pbr.cmd:main
        pbr.config.drivers =
            plain = pbr.cfg.driver:Plain
            fancy = pbr.cfg.driver:Fancy

    You can represent this in ``setup.cfg`` like so:

    .. code-block:: ini

        [options.entry_points]
        console_scripts =
            pbr = pbr.cmd:main
        pbr.config.drivers =
            plain = pbr.cfg.driver:Plain
            fancy = pbr.cfg.driver:Fancy

    Or in ``pyproject.toml`` like so:

    .. code-block:: toml

        [project.scripts]
        pbr = "pbr.cmd:main"

        [project.entry-points."pbr.config.drivers"]
        plain = "pbr.cfg.driver:Plain"
        fancy = "pbr.cfg.driver:Fancy"

    For more information, refer to the `Entry Points`__ document in the
    setuptools docs.

    .. __: https://pypi.org/project/setuptools/30.3.0/
    .. __: https://pypi.org/project/setuptools/68.1.0/
    .. __: https://setuptools.pypa.io/en/latest/userguide/entry_point.html

The general syntax of specifying entry points is a top level name indicating
the entry point group name, followed by one or more key value pairs naming the
entry point to be installed. For example:

.. code-block:: ini

    [entry_points]
    console_scripts =
        pbr = pbr.cmd:main
    pbr.config.drivers =
        plain = pbr.cfg.driver:Plain
        fancy = pbr.cfg.driver:Fancy

Will cause a console script called *pbr* to be installed that executes the
``main`` function found in ``pbr.cmd``. Additionally, two entry points will be
installed for ``pbr.config.drivers``, one called ``plain`` which maps to the
``Plain`` class in ``pbr.cfg.driver`` and one called ``fancy`` which maps to
the ``Fancy`` class in ``pbr.cfg.driver``.

``backwards_compat``
~~~~~~~~~~~~~~~~~~~~~

.. todo:: Describe this section

.. _pbr-setup-cfg:

``pbr``
~~~~~~~

The ``pbr`` section controls *pbr*-specific options and behaviours.

``skip_git_sdist``
  If enabled, *pbr* will not generate a manifest file from *git* commits. If
  this is enabled, you may need to define your own `manifest template`__.

  This can also be configured using the ``SKIP_GIT_SDIST`` environment
  variable, as described :ref:`here <packaging-tarballs>`.

  __ https://packaging.python.org/tutorials/distributing-packages/#manifest-in

``skip_changelog``
  If enabled, *pbr* will not generated a ``ChangeLog`` file from *git* commits.

  This can also be configured using the ``SKIP_WRITE_GIT_CHANGELOG``
  environment variable, as described :ref:`here <packaging-authors-changelog>`

``skip_authors``
  If enabled, *pbr* will not generate an ``AUTHORS`` file from *git* commits.

  This can also be configured using the ``SKIP_GENERATE_AUTHORS`` environment
  variable, as described :ref:`here <packaging-authors-changelog>`

``skip_reno``
  If enabled, *pbr* will not generate a ``RELEASENOTES.txt`` file if `reno`_ is
  present and configured.

  This can also be configured using the ``SKIP_GENERATE_RENO`` environment
  variable, as described :ref:`here <packaging-releasenotes>`.

.. versionchanged:: 6.0

   The ``autodoc_tree_index_modules``, ``autodoc_tree_excludes``,
   ``autodoc_index_modules``, ``autodoc_exclude_modules`` and ``api_doc_dir``
   settings are all removed.

.. versionchanged:: 4.2

   The ``autodoc_tree_index_modules``, ``autodoc_tree_excludes``,
   ``autodoc_index_modules``, ``autodoc_exclude_modules`` and ``api_doc_dir``
   settings are all deprecated.

.. versionchanged:: 2.0

   The ``pbr`` section used to take a ``warnerrors`` option that would enable
   the ``-W`` (Turn warnings into errors.) option when building Sphinx. This
   feature was broken in 1.10 and was removed in pbr 2.0 in favour of the
   ``[build_sphinx] warning-is-error`` provided in Sphinx 1.5+.

``metadata``
~~~~~~~~~~~~

.. todo:: Describe this section

.. _build_sphinx-setup-cfg:

``build_sphinx``
~~~~~~~~~~~~~~~~

.. versionchanged:: 3.0

   The ``build_sphinx`` plugin used to default to building both HTML and man
   page output. This is no longer the case, and you should explicitly set
   ``builders`` to ``html man`` if you wish to retain this behavior.

.. deprecated:: 4.2

   This feature has been superseded by the `sphinxcontrib-apidoc`_ (for
   generation of API documentation) and :ref:`pbr.sphinxext` (for configuration
   of versioning via package metadata) extensions. It has been removed in
   version 6.0.

Requirements
------------

Requirements files are used in place of the ``install_requires`` and
``extras_require`` attributes. Requirement files should be given one of the
below names. This order is also the order that the requirements are tried in:

* ``requirements.txt``
* ``tools/pip-requires``

Only the first file found is used to install the list of packages it contains.

.. versionchanged:: 5.0

   Previously you could specify requirements for a given major version of
   Python using requirements files with a ``-pyN`` suffix. This was deprecated
   in 4.0 and removed in 5.0 in favour of environment markers.

.. _extra-requirements:

Extra requirements
~~~~~~~~~~~~~~~~~~

Groups of optional dependencies, or `"extra" requirements`__, can be described
in your ``setup.cfg``, rather than needing to be added to ``setup.py``. An
example (which also demonstrates the use of environment markers) is shown
below.

__ https://www.python.org/dev/peps/pep-0426/#extras-optional-dependencies

Environment markers
~~~~~~~~~~~~~~~~~~~

Environment markers are `conditional dependencies`__ which can be added to the
requirements (or to a group of extra requirements) automatically, depending on
the environment the installer is running in. They can be added to requirements
in the requirements file, or to extras defined in ``setup.cfg``, but the format
is slightly different for each.

For ``requirements.txt``::

    argparse; python_version=='2.6'

This will result in the package depending on ``argparse`` only if it's being
installed into Python 2.6.

For extras specified in ``setup.cfg``, add an ``extras`` section. For instance,
to create two groups of extra requirements with additional constraints on the
environment, you can use:

.. code-block:: ini

    [extras]
    security =
        aleph
        bet:python_version=='3.2'
        gimel:python_version=='2.7'
    testing =
        quux:python_version=='2.7'

__ https://www.python.org/dev/peps/pep-0426/#environment-markers


Sphinx ``conf.py``
------------------

As described in :doc:`/user/features`, *pbr* provides a Sphinx extension to
automatically configure the version numbers for your documentation using *pbr*
metadata.

To enable this extension, you must add it to the list of extensions in
your ``conf.py`` file:

.. code-block:: python

    extensions = [
        'pbr.sphinxext',
        # ... other extensions
    ]

You should also unset/remove the ``version`` and ``release`` attributes from
this file.

.. _setuptools: http://www.sphinx-doc.org/en/stable/setuptools.html
.. _sphinxcontrib-apidoc: https://pypi.org/project/sphinxcontrib-apidoc/
.. _reno: https://docs.openstack.org/reno/latest/
