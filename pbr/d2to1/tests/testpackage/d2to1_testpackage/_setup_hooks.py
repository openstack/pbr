from distutils.command.build_py import build_py


def test_hook_1(config):
    print 'test_hook_1'


def test_hook_2(config):
    print 'test_hook_2'


class test_command(build_py):
    command_name = 'build_py'

    def run(self):
        print 'Running custom build_py command.'
        return build_py.run(self)


def test_pre_hook(cmdobj):
    print 'build_ext pre-hook'


def test_post_hook(cmdobj):
    print 'build_ext post-hook'
