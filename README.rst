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

PBR builds on top of the work that `d2to1` started to provide for declarative
configuration. `d2to1` is itself an implementation of the ideas behind
`distutils2`. Although `distutils2` is now abandoned in favor of work towards
PEP 426 and Metadata 2.0, declarative config is still a great idea and
specifically important in trying to distribute setup code as a library
when that library itself will alter how the setup is processed. As Metadata
2.0 and other modern Python packaging PEPs come out, `pbr` aims to support
them as quickly as possible.

Running Tests
=============
The testing system is based on a combination of tox and testr. The canonical
approach to running tests is to simply run the command `tox`. This will
create virtual environments, populate them with dependencies and run all of
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

If you go this route, you can interact with the testr command directly.
Running `testr run` will run the entire test suite. `testr run --parallel`
will run it in parallel (this is the default incantation tox uses.) More
information about testr can be found at: http://wiki.openstack.org/testr
