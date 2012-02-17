"""zest.releaser entry points to support projects using distutils2-like
setup.cfg files.  The only actual functionality this adds is to update the
version option in a setup.cfg file, if it exists.  If setup.cfg does not exist,
or does not contain a version option, then this does nothing.

TODO: d2to1 theoretically supports using a different filename for setup.cfg;
this does not support that.  We could hack in support, though I'm not sure how
useful the original functionality is to begin with (and it might be removed) so
we ignore that for now.

TODO: There exists a proposal
(http://mail.python.org/pipermail/distutils-sig/2011-March/017628.html) to add
a 'version-from-file' option (or something of the like) to distutils2; if this
is added then support for it should be included here as well.
"""


import logging
import os

from ConfigParser import ConfigParser


logger = logging.getLogger(__name__)


def update_setupcfg_version(filename, version):
    """Opens the given setup.cfg file, locates the version option in the
    [metadata] section, updates it to the new version.
    """

    setup_cfg = open(filename).readlines()
    current_section = None
    updated = False

    for idx, line in enumerate(setup_cfg):
        m = ConfigParser.SECTCRE.match(line)
        if m:
            if current_section == 'metadata':
                # We already parsed the entire metadata section without finding
                # a version line, and are now moving into a new section
                break
            current_section = m.group('header')
            continue
        opt, val = line.split('=', 1)
        opt, val = opt.strip(), val.strip()
        if current_section == 'metadata' and opt == 'version':
            setup_cfg[idx] = 'version = %s\n' % version
            updated = True
            break

    if updated:
        open(filename, 'w').writelines(setup_cfg)
        logger.info("Set %s's version to %r" % (os.path.basename(filename),
                                                version))


def prereleaser_middle(data):
    filename = os.path.join(data['workingdir'], 'setup.cfg')
    if os.path.exists(filename):
        update_setupcfg_version(filename, data['new_version'])


def postreleaser_middle(data):
    filename = os.path.join(data['workingdir'], 'setup.cfg')
    if os.path.exists(filename):
        update_setupcfg_version(filename, data['dev_version'])
