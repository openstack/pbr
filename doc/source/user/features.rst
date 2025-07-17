==========
 Features
==========

To understand what *pbr* can do for you, it's probably best to look at two
projects: one using pure *setuptools*, and another using *pbr*. First, let's
look at the *setuptools* project.

.. code-block:: none

   $ tree -L 1
   .
   ├── AUTHORS
   ├── CHANGES
   ├── LICENSE
   ├── MANIFEST.in
   ├── README.rst
   ├── requirements.txt
   ├── setup.cfg
   ├── setup.py
   └── somepackage

   $ cat setup.py
   setuptools.setup(
       name='mypackage',
       version='1.0.0',
       description='A short description',
       long_description="""A much longer description...""",
       author="John Doe",
       author_email='john.doe@example.com',
       license='BSD',
   )

Here's a similar package using *pbr*:

.. code-block:: none

   $ tree -L 1
   .
   ├── LICENSE
   ├── README.rst
   ├── setup.cfg
   ├── setup.py
   └── somepackage

   $ cat setup.py
   setuptools.setup(
       pbr=True
   )

   $ cat setup.cfg
   [metadata]
   name = mypackage
   description = A short description
   description_file = README.rst
   author = John Doe
   author_email = john.doe@example.com
   license = BSD

From this, we note a couple of the main features of *pbr*:

- Extensive use of ``setup.cfg`` for configuration
- Automatic package metadata generation (``version``)
- Automatic metadata file generation (``AUTHOR``, ``ChangeLog``,
  ``MANIFEST.in``, ``RELEASENOTES.txt``)

In addition, there are other things that you don't see here but which *pbr*
will do for you:

- Helpful extensions to *setuptools* commands

setup.cfg
---------

.. admonition:: Summary

    *pbr* uses ``setup.cfg`` for all configuration, though ``setup.py`` is
    still required.

One of the main features of *distutils2* was the use of a ``setup.cfg``
INI-style configuration file. This was used to define a package's metadata and
other options that were normally supplied to the ``setup()`` function.

Recent versions of `setuptools`__ have implemented some of this support, but
*pbr* still allows for the definition of the following sections in
``setup.cfg``:

- ``files``
- ``entry_points``
- ``backwards_compat``

For more information on these sections, refer to :doc:`/user/using`.

__ https://setuptools.readthedocs.io/en/latest/setuptools.html#configuring-setup-using-setup-cfg-files

Package Metadata
----------------

.. admonition:: Summary

    *pbr* removes the need to define a lot of configuration in either
    ``setup.py`` or ``setup.cfg`` by extracting this information from Git.

Version
~~~~~~~

.. admonition:: Summary

    *pbr* will automatically configure your version for you by parsing
    semantically-versioned Git tags.

Versions can be managed two ways - *post-versioning* and *pre-versioning*.
*Post-versioning* is the default while *pre-versioning* is enabled by setting
``version`` in the ``setup.cfg`` ``metadata`` section. In both cases the actual
version strings are inferred from Git.

If the currently checked out revision is tagged, that tag is used as
the version.

If the currently checked out revision is not tagged, then we take the
last tagged version number and increment it to get a minimum target
version.

.. note::

   *pbr* supports both bare version tag (e.g. ``0.1.0``) and version prefixed
   with ``v`` or ``V`` (e.g. ``v0.1.0``)

We then walk Git history back to the last release. Within each commit we look
for a ``Sem-Ver:`` pseudo header and, if found, parse it looking for keywords.
Unknown symbols are not an error (so that folk can't wedge *pbr* or break their
tree), but we will emit an info-level warning message. The following symbols
are recognized:

- ``feature``
- ``api-break``
- ``deprecation``
- ``bugfix``

A missing ``Sem-Ver`` line is equivalent to ``Sem-Ver: bugfix``. The ``bugfix``
symbol causes a patch level increment to the version. The ``feature`` and
``deprecation`` symbols cause a minor version increment. The ``api-break``
symbol causes a major version increment.

If *post-versioning* is in use, we use the resulting version number as the target
version.

If *pre-versioning* is in use, we check that the version set in the metadata
section of ``setup.cfg`` is greater than the version we infer using the above
method. If the inferred version is greater than the *pre-versioning* value we
raise an error, otherwise we use the version from ``setup.cfg`` as the target.

We then generate dev version strings based on the commits since the last
release and include the current Git SHA to disambiguate multiple dev versions
with the same number of commits since the release.

.. note::

   *pbr* expects Git tags to be signed for use in calculating versions.

The versions are expected to be compliant with :doc:`semver`.

The ``version.SemanticVersion`` class can be used to query versions of a
package and present it in various forms - ``debian_version()``,
``release_string()``, ``rpm_string()``, ``version_string()``, or
``version_tuple()``.

Long Description
~~~~~~~~~~~~~~~~

.. admonition:: Summary

    *pbr* can extract the contents of a ``README`` and use this as your long
    description

There is no need to maintain two long descriptions and your ``README`` file is
probably a good long_description. So we'll just inject the contents of your
``README.rst``, ``README.txt`` or ``README`` file into your empty
``long_description``.

You can also specify the exact file you want to use using the
``description_file`` parameter.

You can set the ``description_content_type`` to a MIME type that may
help rendering of the description; for example ``text/markdown`` or
``text/x-rst; charset=UTF-8``.

Requirements
~~~~~~~~~~~~

.. admonition:: Summary

    *pbr* will extract requirements from ``requirements.txt`` files and
    automatically populate the ``install_requires`` argument to ``setup`` with
    them.

You may not have noticed, but there are differences in how pip
``requirements.txt`` files work and how *setuptools* wants to be told about
requirements. The *pip* way is nicer because it sure does make it easier to
populate a *virtualenv* for testing or to just install everything you need.
Duplicating the information, though, is super lame. To solve this issue, *pbr*
will let you use ``requirements.txt``-format files to describe the requirements
for your project and will then parse these files, split them up appropriately,
and inject them into the ``install_requires`` argument to ``setup``. Voila!

Finally, it is possible to specify groups of optional dependencies, or
:ref:`"extra" requirements <extra-requirements>`, in your ``setup.cfg`` rather
than ``setup.py``.

.. versionchanged:: 7.0

   Previously, the ``tests_require`` and ``dependency_links`` setup arguments
   were also populated by *pbr*. The ``tests_require`` argument is no longer
   supported as of `setuptools v72.0.0`__, while the ``dependency_links``
   argument is deprecated and ignored by `pip 19.0 or later`__.

   .. __: https://setuptools.pypa.io/en/stable/history.html#v72-0-0
   .. __: https://github.com/pypa/pip/pull/6060

.. versionchanged:: 5.0

   Previously, you could specify requirements for a given major version of
   Python using requirments files with a ``-pyN`` suffix. This was deprecated
   in 4.0 and removed in 5.0 in favour of environment markers.

Automatic File Generation
-------------------------

.. admonition:: Summary

    *pbr* can automatically generate a couple of files, which would normally
    have to be maintained manually, by using Git data.

AUTHORS, ChangeLog
~~~~~~~~~~~~~~~~~~

.. admonition:: Summary

    *pbr* will automatically generate an ``AUTHORS`` and a ``ChangeLog`` file
    using Git logs.

Why keep an ``AUTHORS`` or a ``ChangeLog`` file when Git already has all of the
information you need? ``AUTHORS`` generation supports filtering/combining based
on a standard ``.mailmap`` file.

Manifest
~~~~~~~~

.. admonition:: Summary

    *pbr* will automatically generate a ``MANIFEST.in`` file based on the files
    Git is tracking.

Just like ``AUTHORS`` and ``ChangeLog``, why keep a list of files you wish to
include when you can find many of these in Git. ``MANIFEST.in`` generation
ensures almost all files stored in Git, with the exception of ``.gitignore``,
``.gitreview`` and ``.pyc`` files, are automatically included in your
distribution. In addition, the generated ``AUTHORS`` and ``ChangeLog`` files
are also included. In many cases, this removes the need for an explicit
``MANIFEST.in`` file, though one can be provided to exclude files that are
tracked via Git but which should not be included in the final release, such as
test files.

.. note::

   ``MANIFEST.in`` files have no effect on binary distributions such as wheels.
   Refer to the `Python packaging tutorial`__ for more information.

__ https://packaging.python.org/tutorials/distributing-packages/#manifest-in

Release Notes
~~~~~~~~~~~~~

.. admonition:: Summary

    *pbr* will automatically use *reno* \'s ``build_reno`` setuptools command
    to generate a release notes file, if reno is available and configured.

If using *reno*, you may wish to include a copy of the release notes in your
packages. *reno* provides a ``build_reno`` `setuptools command`__ and, if reno
is present and configured, *pbr* will automatically call this to generate a
release notes file for inclusion in your package.

__ https://docs.openstack.org/reno/latest/user/setuptools.html

Setup Commands
--------------

.. _build_sphinx:

``build_sphinx``
~~~~~~~~~~~~~~~~

.. versionremoved:: 6.0

    *Sphinx* deprecated the ``build_sphinx`` distutils commands in *Sphinx*
    v5.0.0 and removed it in *Sphinx* v7.0.0. *pbr* deprecated its override of
    this command in *pbr* v4.2.0 and removed it in *pbr* v6.0.0.

    For automated generation of API documentation, consider either the
    `sphinx.ext.apidoc`__ extension, provided in Sphinx since v8.2.0, or the
    `sphinxcontrib-apidoc`__ extension if you are stuck with older versions of
    Sphinx.

    For configuration of versioning via package metadata, consider the
    :ref:`pbr.sphinxext` extension.

    .. __: https://www.sphinx-doc.org/en/master/usage/extensions/apidoc.html
    .. __: https://pypi.org/project/sphinxcontrib-apidoc/

``test``
~~~~~~~~

.. versionremoved:: 7.0

    *pbr* previously aliased the ``test`` command to use the testing tool of
    your choice. However, the two test runners it supported - ``testr`` and
    ``nose`` - are no longer maintained. The override of this command was
    therefore removed in *pbr* v7.0.0.

    If you relied on this command, you should switch to calling the test runner
    directly.

.. _pbr.sphinxext:

Sphinx Extension
----------------

.. admonition:: Summary

    *pbr* provides a Sphinx extension to allow you to use *pbr* version
    metadata in your Sphinx documentation.

.. versionadded:: 4.2

*pbr* provides a Sphinx extension which can be used to configure version
numbers for documentation. The package does not need to be installed for this
to function.

.. note::

    The ``openstackdocstheme`` Sphinx theme provides similar functionality.
    This should be preferred for official OpenStack projects. Refer to the
    `documentation`__ for more information.

    __ https://docs.openstack.org/openstackdocstheme/

For more information on the extension, refer to :doc:`/user/using`.
