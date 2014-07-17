import re
from distutils.core import Command
from distutils import log as logger
from . import packaging

__all__ = ['tag']

VERSION_MATCH = re.compile('^(?P<major>\d\d*)\.(?P<minor>\d*)\.(?P<patch>\d*)($|\.|)(?P<pre_release>[0-9A-Za-z-]*)($|\.g|)(?P<git_id>[0-9A-Za-z-]*)($|\+)(?P<metadata>[0-9A-Za-z-\.]*$)')

class tag(Command):
    """ """
    description = "Will add a git tag for the highest defined version increment based on the current version detected"
    user_options = [('major', None,
                     "Define this release as a major version increment (default: false)"),
                    ('minor', None,
                     "Define this release as a minor version increment (default: false)"),
                    ('patch', None,
                     "Define this release as a patch version increment (default: true)")]
    boolean_options = ['major', 'minor', 'patch']
    def initialize_options(self):
        """ """
        self.major = False
        self.minor = False
        self.patch = True

    def finalize_options(self):
        """ """
        if not packaging._git_is_installed():
            raise Exception('Unable to run git commandline, please make sure it is installed!')
        self.git_dir = packaging._get_git_directory()
        
    def get_next_release_id(self, version, major=None, minor=None, patch=None):
        if patch:
            version['patch'] = int(version['patch']) + 1
        if minor:
            version['minor'] = int(version['minor']) + 1
            version['patch'] = 0
        if major:
            version['major'] = int(version['major']) + 1
            version['minor'] = 0
            version['patch'] = 0
        
        return version
    
    def next_version_string(self, major=False, minor=False, patch=False):
        mod = __import__(self.distribution.get_name() + '.version')
        version = mod.version_info.version_string()
        match = VERSION_MATCH.match(version)
        if match is None:
            match = VERSION_MATCH.match('0.0.0')
        
        version_dict = self.get_next_release_id(match.groupdict(), 
                                                major,
                                                minor,
                                                patch)
        
        return '{major}.{minor}.{patch}'.format(**version_dict)
    
    def get_tags(self):
        """ """
        tags = packaging._run_git_command(['tag'], self.git_dir)
        return sorted(tags.splitlines())
        
    def has_tag(self, tag_name=None):
        """ """
        for tag in self.get_tags():
            if tag_name == tag:
                return True
        
        return False
    
    def run(self):
        """Will tag the currently active git commit id with the next release tag id"""
        sha = packaging._run_git_command(['rev-parse', 'HEAD'], self.git_dir)
        tag = self.next_version_string(self.major, self.minor, self.patch)
        if self.has_tag(tag):
            logger.info('tag {0} already exists for git repo'.format(tag))
        else:
            logger.info('Adding tag {0} for commit {1}'.format(tag, sha))
            if not self.dry_run:
                packaging._run_git_command(['tag', '-m', '""', '--sign', tag, sha], self.git_dir, throw_on_error=True)