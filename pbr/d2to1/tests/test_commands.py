from . import D2to1TestCase


class TestCommands(D2to1TestCase):
    def test_custom_build_py_command(self):
        """
        Test that a custom subclass of the build_py command runs when listed in
        the commands [global] option, rather than the normal build command.
        """

        stdout, _, return_code = self.run_setup('build_py')
        assert 'Running custom build_py command.' in stdout
        assert return_code == 0
