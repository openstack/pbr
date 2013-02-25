from __future__ import with_statement

import contextlib
import os
import shutil
import stat


from ConfigParser import ConfigParser


@contextlib.contextmanager
def open_config(filename):
    cfg = ConfigParser()
    cfg.read(filename)
    yield cfg
    with open(filename, 'w') as fp:
        cfg.write(fp)


def rmtree(path):
    """
    shutil.rmtree() with error handler for 'access denied' from trying to
    delete read-only files.
    """

    def onerror(func, path, exc_info):
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    return shutil.rmtree(path, onerror=onerror)
