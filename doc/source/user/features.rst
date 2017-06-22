==========
 Features
==========

Version
-------

Versions can be managed two ways - postversioning and preversioning.
Postversioning is the default, and preversioning is enabled by setting
``version`` in the setup.cfg ``metadata`` section. In both cases version
strings are inferred from git.

If the currently checked out revision is tagged, that tag is used as
the version.

If the currently checked out revision is not tagged, then we take the
last tagged version number and increment it to get a minimum target
version.

We then walk git history back to the last release. Within each commit we look
for a Sem-Ver: pseudo header, and if found parse it looking for keywords.
Unknown symbols are not an error (so that folk can't wedge pbr or break their
tree), but we will emit an info level warning message. Known symbols:
``feature``, ``api-break``, ``deprecation``, ``bugfix``. A missing
Sem-Ver line is equivalent to ``Sem-Ver: bugfix``. The ``bugfix`` symbol causes
a patch level increment to the version. The ``feature`` and ``deprecation``
symbols cause a minor version increment. The ``api-break`` symbol causes a
major version increment.

If postversioning is in use, we use the resulting version number as the target
version.

If preversioning is in use we check that the version set in the metadata
section of `setup.cfg` is greater than the version we infer using the above
method.  If the inferred version is greater than the preversioning value we
raise an error, otherwise we use the version from `setup.cfg` as the target.

We then generate dev version strings based on the commits since the last
release and include the current git sha to disambiguate multiple dev versions
with the same number of commits since the release.

.. note::

   `pbr` expects git tags to be signed for use in calculating versions

The versions are expected to be compliant with :doc:`semver`.

The ``version.SemanticVersion`` class can be used to query versions of a
package and present it in various forms - ``debian_version()``,
``release_string()``, ``rpm_string()``, ``version_string()``, or
``version_tuple()``.

AUTHORS and ChangeLog
---------------------

Why keep an `AUTHORS` or a `ChangeLog` file when git already has all of the
information you need? `AUTHORS` generation supports filtering/combining based
on a standard `.mailmap` file.

Manifest
--------

Just like `AUTHORS` and `ChangeLog`, why keep a list of files you wish to
include when you can find many of these in git. `MANIFEST.in` generation
ensures almost all files stored in git, with the exception of `.gitignore`,
`.gitreview` and `.pyc` files, are automatically included in your
distribution. In addition, the generated `AUTHORS` and `ChangeLog` files are
also included. In many cases, this removes the need for an explicit
'MANIFEST.in' file

Sphinx Autodoc
--------------

Sphinx can produce auto documentation indexes based on signatures and
docstrings of your project but you have to give it index files to tell it
to autodoc each module: that's kind of repetitive and boring. PBR will scan
your project, find all of your modules, and generate all of the stub files for
you.

Sphinx documentation setups are altered to generate man pages by default. They
also have several pieces of information that are known to setup.py injected
into the sphinx config.

See the :ref:`pbr-setup-cfg` section of the configuration file for
details on configuring your project for autodoc.

Requirements
------------

You may not have noticed, but there are differences in how pip
`requirements.txt` files work and how distutils wants to be told about
requirements. The pip way is nicer because it sure does make it easier to
populate a virtualenv for testing or to just install everything you need.
Duplicating the information, though, is super lame. To solve this issue, `pbr`
will let you use `requirements.txt`-format files to describe the requirements
for your project and will then parse these files, split them up appropriately,
and inject them into the `install_requires`, `tests_require` and/or
`dependency_links` arguments to `setup`. Voila!

You can also have a requirement file for each specific major version of Python.
If you want to have a different package list for Python 3 then just drop a
`requirements-py3.txt` and it will be used instead.

Finally, it is possible to specify groups of optional dependencies, or
:ref:`"extra" requirements <extra-requirements>`, in your `setup.cfg`
rather than `setup.py`.

long_description
----------------

There is no need to maintain two long descriptions- and your README file is
probably a good long_description. So we'll just inject the contents of your
README.rst, README.txt or README file into your empty long_description. Yay
for you.
