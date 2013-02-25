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
