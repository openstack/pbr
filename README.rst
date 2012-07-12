.. toctree::
   :maxdepth 2

PBR: Python Build Reasonablness
===============================

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

What It Does
------------

PBR can and does do a bunch of things for you:

 * **Version**: Manage version number bad on git revisions and tags
 * **AUTHORS**: Generate AUTHORS file from git log
 * **ChangeLog**: Generate ChangeLog from git log
 * **Sphinx Autodoc**: Generate autodoc stub files for your whole module
 * **Requirements**: Store your dependencies in a pip requirements file
 * **long_description**: Use your README file as a long_description

Version
^^^^^^^

You can tell pbr to manage your version based on git tags.
Two different modes are supported, a pre-version mode, in
which there is a version your project is working towards a
release of, and post-version mode, in which the version
between releases is the previous release plus a counter.
In both cases, a release is indicated by tagging a revision.

AUTHORS and ChangeLog
^^^^^^^^^^^^^^^^^^^^^

Why keep an AUTHORS or a ChangeLog file, when git already has all of the
information you need. AUTHORS generation supports filtering/combining based
on a standard .mailmap file, as well as looking through commit logs for
Signed-off-by lines.

Sphinx Autodoc
^^^^^^^^^^^^^^

Sphinx can produce auto documentation indexes based on signatures and
docstrings of your project- but you have to give it index files to tell it
to autodoc each module. That's kind of repetitive and boring. PBR will
scan your project, find all of your modules, and generate all of the stub
files for you.

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

Getting Started
---------------

Wow, you're still here? NEAT!

Step one is to add::

  setup_requires=['pbr'],

to your setup call in setup.py. Next, change your version= line to::

  version="#:",

Don't argue, just do it - there is no valid reason to not use git tags to
manage your project version. Unless you want to be ornery, go to the main
__init__.py of the module that's the same name as your package - let's call
your package "hipsterbeard", and add this code::

  from pbr import version
  __version_info = version.VersionInfo('hipsterbeard')
  __version__ = __version_info.deferred_version_string()

You will now get version information, AUTHORS and ChangeLog and Sphinx stubs
generation, and long_description injetion.

Now, if you're weird like openstack and make your python-package something
different than your top level code module (such as "I'm going to
install python-hipsterbeard and get a thing I can import called hipsterbeard")
you'll need to make two slight modifications. First, tell setup where to find
your version hooks::

  version="#:hipsterbeard:__version_info"

That's the form "Module.submodule:InstanceName" - sort of like nosetests.
Then::

  from pbr import version
  __version_info = version.VersionInfo('python-hipsterbeard')
  __version__ = __version_info.deferred_version_string()

goes in hipsterbeard/__init__.py. Mainly that's because pkg-resources needs
to look into the egg that setup.py install produced, but your code is called
something different, and there is really no other way to figure out what the
heck you're doing.

Stop being weird next time. Seriously.

Depends tracking is a little bit easier. The easiest version goes like
this::

    install_requires=['#:tools/pip-requires'],
    tests_require=['#:tools/test-requires'],
    dependency_links=['#:tools/pip-requires', '#:tools/test-requires'],

That will put the contents of tools/pip-requires into install_requires,
tools/test-requires into tests_require (please someone shoot whoever got the
pluralization backwards there) and will split out dependency link
information from both files into dependency_links. All three matchers will
do what they do on any number of entries that are prefixed by '#:' - so feel
free to use that for whatever you'd like.
