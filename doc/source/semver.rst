Linux/Python Compatible Semantic Versioning 3.0.0
=================================================

This is a fork of Semantic Versioning 2.0. The specific changes have to do
with the format of pre-release and build labels, specifically to make them
not confusing when co-existing with Linux distribution packaging and Python
packaging. Inspiration for the format of the pre-release and build labels
came from Python's PEP440.

Changes vs SemVer 2.0
---------------------

#. dev versions are defined. These are extremely useful when
   dealing with CI and CD systems when 'every commit is a release' is not
   feasible.

#. All versions have been made PEP-440 compatible, because of our deep
   roots in Python. Pre-release versions are now separated by . not -, and
   use a/b/c rather than alpha/beta etc.

Summary
-------

Given a version number MAJOR.MINOR.PATCH,
increment the:

#. MAJOR version when you make incompatible API changes,
#. MINOR version when you add functionality in a backwards-compatible
   manner, and
#. PATCH version when you make backwards-compatible bug fixes.

Introduction
------------

In the world of software management there exists a dread place called
"dependency hell." The bigger your system grows and the more packages
you integrate into your software, the more likely you are to find
yourself, one day, in this pit of despair.

In systems with many dependencies, releasing new package versions can
quickly become a nightmare. If the dependency specifications are too
tight, you are in danger of version lock (the inability to upgrade a
package without having to release new versions of every dependent
package). If dependencies are specified too loosely, you will inevitably
be bitten by version promiscuity (assuming compatibility with more
future versions than is reasonable). Dependency hell is where you are
when version lock and/or version promiscuity prevent you from easily and
safely moving your project forward.

As a solution to this problem, I propose a simple set of rules and
requirements that dictate how version numbers are assigned and
incremented. These rules are based on but not necessarily limited to
pre-existing widespread common practices in use in both closed and
open-source software. For this system to work, you first need to declare
a public API. This may consist of documentation or be enforced by the
code itself. Regardless, it is important that this API be clear and
precise. Once you identify your public API, you communicate changes to
it with specific increments to your version number. Consider a version
format of X.Y.Z (Major.Minor.Patch). Bug fixes not affecting the API
increment the patch version, backwards compatible API additions/changes
increment the minor version, and backwards incompatible API changes
increment the major version.

I call this system "Semantic Versioning." Under this scheme, version
numbers and the way they change convey meaning about the underlying code
and what has been modified from one version to the next.

Semantic Versioning Specification (SemVer)
------------------------------------------

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in `RFC
2119 <http://tools.ietf.org/html/rfc2119>`__.

#.  Software using Semantic Versioning MUST declare a public API. This
    API could be declared in the code itself or exist strictly in
    documentation. However it is done, it should be precise and
    comprehensive.

#.  A normal version number MUST take the form X.Y.Z where X, Y, and Z
    are non-negative integers, and MUST NOT contain leading zeroes. X is
    the major version, Y is the minor version, and Z is the patch
    version. Each element MUST increase numerically. For instance: 1.9.0
    -> 1.10.0 -> 1.11.0.

#.  Once a versioned package has been released, the contents of that
    version MUST NOT be modified. Any modifications MUST be released as
    a new version.

#.  Major version zero (0.y.z) is for initial development. Anything may
    change at any time. The public API should not be considered stable.

#.  Version 1.0.0 defines the public API. The way in which the version
    number is incremented after this release is dependent on this public
    API and how it changes.

#.  Patch version Z (x.y.Z \| x > 0) MUST be incremented if only
    backwards compatible bug fixes are introduced. A bug fix is defined
    as an internal change that fixes incorrect behavior.

#.  Minor version Y (x.Y.z \| x > 0) MUST be incremented if new,
    backwards compatible functionality is introduced to the public API.
    It MUST be incremented if any public API functionality is marked as
    deprecated. It MAY be incremented if substantial new functionality
    or improvements are introduced within the private code. It MAY
    include patch level changes. Patch version MUST be reset to 0 when
    minor version is incremented.

#.  Major version X (X.y.z \| X > 0) MUST be incremented if any
    backwards incompatible changes are introduced to the public API. It
    MAY also include minor and patch level changes. Patch and minor
    version MUST be reset to 0 when major version is incremented.

#.  A pre-release version MAY be denoted by appending a dot
    separated identifier immediately following the patch version.
    The identifier MUST comprise only a, b, c followed by non-negative
    integer value. The identifier MUST NOT be empty.
    Pre-release versions have a lower precedence than the associated normal
    version. A pre-release version indicates that
    the version is unstable and might not satisfy the intended
    compatibility requirements as denoted by its associated normal
    version. Examples: 1.0.0.a1, 1.0.0.b99, 1.0.0.c1000.

#.  A development version MAY be denoted by appending a dot separated
    identifier immediately following the patch version.
    The identifier MUST comprise the string dev followed by non-negative
    integer value. The identifier MUST NOT be empty. Development versions
    have a lower precedence than the associated normal version or pre-release
    version. A development version is a completely unsupported and conveys no
    API promises when related to other versions. They are more useful as
    communication vehicles between developers of a community, whereas
    pre-releases, while potentially prone to break still, are intended for
    externally facing communication of not-yet-released ideas. Dev versions
    are not public artifacts and should never be placed in public
    repositories: they are intended as developer-local resources. Examples:
    1.0.0.dev1, 1.0.0.a1.dev1

#.  git version metadata MAY be denoted by appending a dot separated
    identifier immediately following a development or pre-release version.
    The identifier MUST comprise the character g followed by a seven
    character git short-sha. The sha MUST NOT be empty. git version
    metadata MUST be ignored when determining version precedence. Thus
    two versions that differ only in the git version, have the same
    precedence. Example: 1.0.0.a1.g95a9beb.

#.  Build metadata MAY be denoted by appending a plus sign and a series
    of dot separated identifiers immediately following the patch or
    pre-release version. Identifiers MUST comprise only ASCII
    alphanumerics [0-9A-Za-z]. Identifiers MUST NOT be empty. Build
    metadata MUST be ignored when determining version precedence. Thus
    two versions that differ only in the build metadata, have the same
    precedence. Examples: 1.0.0.a1+001, 1.0.0+20130313144700,
    1.0.0.b1+exp.sha.5114f85.

#.  Precedence refers to how versions are compared to each other when
    ordered. Precedence MUST be calculated by separating the version
    into major, minor, patch, pre-release, and development identifiers in
    that order (Build metadata does not figure into precedence). Precedence
    is determined by the first difference when comparing each of these
    identifiers from left to right as follows: Major, minor, and patch
    versions are always compared numerically. Example: 1.0.0 < 2.0.0 <
    2.1.0 < 2.1.1. When major, minor, and patch are equal, a pre-release
    version has lower precedence than a normal version. Example:
    1.0.0.a1 < 1.0.0. When major, minor, patch and pre-release are equal, a
    development version has a lower precedence than a normal version and of a
    pre-release version. Example: 1.0.0.dev1 < 1.0.0 and 1.0.0.dev9 <
    1.0.0.a1 and 1.0.0.a1 < 1.0.0.a2.dev4. Precedence for two pre-release
    versions with the same major, minor, and patch version MUST be determined
    by comparing the identifier to the right of the patch version as follows:
    if the alpha portion matches, the numeric portion is compared in
    numerical sort order. If the alpha portion does not match, the sort order
    is dev < a < b < c. Example: 1.0.0.dev8 < 1.0.0.dev9 < 1.0.0.a1.dev3 <
    1.0.0.a1 < 1.0.0.b2 < 1.0.0.c1 < 1.0.0.  Precedence for dev versions if
    all other components are equal is done by comparing their numeric
    component. If all other components are not equal, predence is determined
    by comparing the other components.

Why Use Semantic Versioning?
----------------------------

This is not a new or revolutionary idea. In fact, you probably do
something close to this already. The problem is that "close" isn't good
enough. Without compliance to some sort of formal specification, version
numbers are essentially useless for dependency management. By giving a
name and clear definition to the above ideas, it becomes easy to
communicate your intentions to the users of your software. Once these
intentions are clear, flexible (but not too flexible) dependency
specifications can finally be made.

A simple example will demonstrate how Semantic Versioning can make
dependency hell a thing of the past. Consider a library called
"Firetruck." It requires a Semantically Versioned package named
"Ladder." At the time that Firetruck is created, Ladder is at version
3.1.0. Since Firetruck uses some functionality that was first introduced
in 3.1.0, you can safely specify the Ladder dependency as greater than
or equal to 3.1.0 but less than 4.0.0. Now, when Ladder version 3.1.1
and 3.2.0 become available, you can release them to your package
management system and know that they will be compatible with existing
dependent software.

As a responsible developer you will, of course, want to verify that any
package upgrades function as advertised. The real world is a messy
place; there's nothing we can do about that but be vigilant. What you
can do is let Semantic Versioning provide you with a sane way to release
and upgrade packages without having to roll new versions of dependent
packages, saving you time and hassle.

If all of this sounds desirable, all you need to do to start using
Semantic Versioning is to declare that you are doing so and then follow
the rules. Link to this website from your README so others know the
rules and can benefit from them.

Examples
---------

.. code::

   # MAJOR.MINOR.PATCH versions
   1.0.0
   2.0.0
   2.1.0
   2.1.1
   10.0.0

   # Pre-release versions
   1.0.0.a1
   1.0.0.a10
   1.0.0.b99
   1.0.0.c1000

   # Development versions
   1.0.0.dev1
   1.0.0.dev2
   1.0.0.dev10
   1.0.0.a1.dev1
   1.0.0.a1.dev2
   1.0.0.a1.dev10

   # Git short-sha Development (*) versions
   1.0.0.a1.g95a9beb
   1.0.0.c999.g95a9beb (TODO: ?)

   # Build metadata
   1.0.0.a1+001
   1.0.0+20130313144700
   1.0.0.b1+exp.sha.5114f85

   # Git short-sha and build metadata
   1.0.0.a1.g95a9beb+001
   1.0.0.a1.g95a9beb+20130313144700
   1.0.0.a1.g95a9beb+exp.sha.5114f85

   # Git short-sha and ISO8601 build metadata (* TODO: ?)
   1.0.0.a1.g95a9beb+2013-03-13T14:47:00-0000
   1.0.0.a1.g95a9beb+2013-03-13T14:47:00+Z


FAQ
---

How should I deal with revisions in the 0.y.z initial development phase?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest thing to do is start your initial development release at
0.1.0 and then increment the minor version for each subsequent release.

How do I know when to release 1.0.0?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your software is being used in production, it should probably already
be 1.0.0. If you have a stable API on which users have come to depend,
you should be 1.0.0. If you're worrying a lot about backwards
compatibility, you should probably already be 1.0.0.

Doesn't this discourage rapid development and fast iteration?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Major version zero is all about rapid development. If you're changing
the API every day you should either still be in version 0.y.z or on a
separate development branch working on the next major version.

If even the tiniest backwards incompatible changes to the public API require a major version bump, won't I end up at version 42.0.0 very rapidly?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a question of responsible development and foresight.
Incompatible changes should not be introduced lightly to software that
has a lot of dependent code. The cost that must be incurred to upgrade
can be significant. Having to bump major versions to release
incompatible changes means you'll think through the impact of your
changes, and evaluate the cost/benefit ratio involved.

Documenting the entire public API is too much work!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is your responsibility as a professional developer to properly
document software that is intended for use by others. Managing software
complexity is a hugely important part of keeping a project efficient,
and that's hard to do if nobody knows how to use your software, or what
methods are safe to call. In the long run, Semantic Versioning, and the
insistence on a well defined public API can keep everyone and everything
running smoothly.

What do I do if I accidentally release a backwards incompatible change as a minor version?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As soon as you realize that you've broken the Semantic Versioning spec,
fix the problem and release a new minor version that corrects the
problem and restores backwards compatibility. Even under this
circumstance, it is unacceptable to modify versioned releases. If it's
appropriate, document the offending version and inform your users of the
problem so that they are aware of the offending version.

What should I do if I update my own dependencies without changing the public API?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

That would be considered compatible since it does not affect the public
API. Software that explicitly depends on the same dependencies as your
package should have their own dependency specifications and the author
will notice any conflicts. Determining whether the change is a patch
level or minor level modification depends on whether you updated your
dependencies in order to fix a bug or introduce new functionality. I
would usually expect additional code for the latter instance, in which
case it's obviously a minor level increment.

What if I inadvertently alter the public API in a way that is not compliant with the version number change (i.e. the code incorrectly introduces a major breaking change in a patch release)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use your best judgment. If you have a huge audience that will be
drastically impacted by changing the behavior back to what the public
API intended, then it may be best to perform a major version release,
even though the fix could strictly be considered a patch release.
Remember, Semantic Versioning is all about conveying meaning by how the
version number changes. If these changes are important to your users,
use the version number to inform them.

How should I handle deprecating functionality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deprecating existing functionality is a normal part of software
development and is often required to make forward progress. When you
deprecate part of your public API, you should do two things: (1) update
your documentation to let users know about the change, (2) issue a new
minor release with the deprecation in place. Before you completely
remove the functionality in a new major release there should be at least
one minor release that contains the deprecation so that users can
smoothly transition to the new API.

Does SemVer have a size limit on the version string?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No, but use good judgment. A 255 character version string is probably
overkill, for example. Also, specific systems may impose their own
limits on the size of the string.

About
-----

The Linux/Python Compatible Semantic Versioning specification is maintained
by the `OpenStack <http://openstack.org>`_ project.

It is based on The Semantic Versioning specification, which was
authored by `Tom Preston-Werner <http://tom.preston-werner.com>`__,
with inputs from `PEP 440 <http://www.python.org/dev/peps/pep-0440/>`_

If you'd like to leave feedback, please `open an issue
<https://bugs.launchpad.net/pbr/+filebug>`_.

License
-------

Creative Commons - CC BY 3.0 http://creativecommons.org/licenses/by/3.0/
