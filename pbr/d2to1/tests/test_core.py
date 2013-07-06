import glob
import os
import tarfile

from . import D2to1TestCase


VERSION = '0.1.dev'


class TestCore(D2to1TestCase):
    def test_setup_py_version(self):
        """
        Test that the `./setup.py --version` command returns the correct
        value without balking.
        """

        self.run_setup('egg_info')
        stdout, _, _ = self.run_setup('--version')
        assert stdout == VERSION

    def test_setup_py_keywords(self):
        """
        Test that the `./setup.py --keywords` command returns the correct
        value without balking.
        """

        self.run_setup('egg_info')
        stdout, _, _ = self.run_setup('--keywords')
        assert stdout == 'packaging,distutils,setuptools'

    def test_sdist_extra_files(self):
        """
        Test that the extra files are correctly added.
        """

        stdout, _, return_code = self.run_setup('sdist', '--formats=gztar')

        # There can be only one
        try:
            tf_path = glob.glob(os.path.join('dist', '*.tar.gz'))[0]
        except IndexError:
            assert False, 'source dist not found'

        tf = tarfile.open(tf_path)
        names = ['/'.join(p.split('/')[1:]) for p in tf.getnames()]

        assert 'extra-file.txt' in names
