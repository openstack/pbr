import os
import textwrap

from . import D2to1TestCase
from .util import open_config


class TestHooks(D2to1TestCase):
    def setup(self):
        super(TestHooks, self).setup()
        with open_config(os.path.join(self.package_dir, 'setup.cfg')) as cfg:
            cfg.set('global', 'setup-hooks',
                    'd2to1_testpackage._setup_hooks.test_hook_1\n'
                    'd2to1_testpackage._setup_hooks.test_hook_2')
            cfg.set('build_ext', 'pre-hook.test_pre_hook',
                    'd2to1_testpackage._setup_hooks.test_pre_hook')
            cfg.set('build_ext', 'post-hook.test_post_hook',
                    'd2to1_testpackage._setup_hooks.test_post_hook')

    def test_global_setup_hooks(self):
        """
        Test that setup_hooks listed in the [global] section of setup.cfg are
        executed in order.
        """

        stdout, _, return_code = self.run_setup('egg_info')
        assert 'test_hook_1\ntest_hook_2' in stdout
        assert return_code == 0

    def test_command_hooks(self):
        """
        Simple test that the appropriate command hooks run at the
        beginning/end of the appropriate command.
        """

        stdout, _, return_code = self.run_setup('egg_info')
        assert 'build_ext pre-hook' not in stdout
        assert 'build_ext post-hook' not in stdout
        assert return_code == 0

        stdout, _, return_code = self.run_setup('build_ext')
        assert textwrap.dedent("""
            running build_ext
            running pre_hook d2to1_testpackage._setup_hooks.test_pre_hook for command build_ext
            build_ext pre-hook
        """) in stdout
        assert stdout.endswith('build_ext post-hook')
        assert return_code == 0


