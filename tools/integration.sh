#!/bin/bash -xe

function mkvenv {
    venv=$1

    rm -rf $venv
    virtualenv $venv
    $venv/bin/pip install -U pip wheel
}

# BASE should be a directory with a subdir called "new" and in that
#      dir, there should be a git repository for every entry in PROJECTS
BASE=${BASE:-/opt/stack}

REPODIR=${REPODIR:-$BASE/new}

# TODO: Figure out how to get this on to the box properly
sudo apt-get install -y --force-yes libxml2-dev libxslt-dev libmysqlclient-dev libpq-dev libnspr4-dev pkg-config libsqlite3-dev libzmq-dev libffi-dev libldap2-dev libsasl2-dev ccache

# FOR numpy / pyyaml
sudo apt-get build-dep -y --force-yes python-numpy
sudo apt-get build-dep -y --force-yes python-yaml

# And use ccache explitly
export PATH=/usr/lib/ccache:$PATH

tmpdir=$(mktemp -d)

#BRANCH
BRANCH=${OVERRIDE_ZUUL_BRANCH=:-master}
# PROJECTS is a list of projects that we're testing
PROJECTS=$*

pbrsdistdir=$tmpdir/pbrsdist
git clone $REPODIR/pbr $pbrsdistdir
cd $pbrsdistdir

eptest=$tmpdir/eptest
mkdir $eptest
cd $eptest

cat <<EOF > setup.cfg
[metadata]
name = test_project

[entry_points]
console_scripts =
    test_cmd = test_project:main

[global]
setup-hooks =
    pbr.hooks.setup_hook
EOF

cat <<EOF > setup.py
import setuptools

try:
    from requests import Timeout
except ImportError:
    from pip._vendor.requests import Timeout

from socket import error as SocketError

# Some environments have network issues that drop connections to pypi
# when running integration tests, so we retry here so that hour-long
# test runs are less likely to fail randomly.
try:
    setuptools.setup(
        setup_requires=['pbr'],
        pbr=True)
except (SocketError, Timeout):
    setuptools.setup(
        setup_requires=['pbr'],
        pbr=True)

EOF

mkdir test_project
cat <<EOF > test_project/__init__.py
def main():
    print "Test cmd"
EOF

epvenv=$eptest/venv
mkvenv $epvenv

eppbrdir=$tmpdir/eppbrdir
git clone $REPODIR/pbr $eppbrdir
$epvenv/bin/pip install -e $eppbrdir

PBR_VERSION=0.0 $epvenv/bin/python setup.py install
cat $epvenv/bin/test_cmd
grep 'PBR Generated' $epvenv/bin/test_cmd
$epvenv/bin/test_cmd | grep 'Test cmd'

projectdir=$tmpdir/projects
mkdir -p $projectdir

for PROJECT in $PROJECTS ; do
    SHORT_PROJECT=$(basename $PROJECT)
    if ! grep 'pbr' $REPODIR/$SHORT_PROJECT/setup.py >/dev/null 2>&1
    then
        # project doesn't use pbr
        continue
    fi
    if [ $SHORT_PROJECT = 'pypi-mirror' ]; then
        # pypi-mirror doesn't consume the mirror
        continue
    fi
    if [ $SHORT_PROJECT = 'jeepyb' ]; then
        # pypi-mirror doesn't consume the mirror
        continue
    fi
    if [ $SHORT_PROJECT = 'tempest' ]; then
        # Tempest doesn't really install
        continue
    fi
    if [ $SHORT_PROJECT = 'requirements' ]; then
        # requirements doesn't really install
        continue
    fi

    # set up the project synced with the global requirements
    sudo chown -R $USER $REPODIR/$SHORT_PROJECT
    (cd $REPODIR/requirements && python update.py $REPODIR/$SHORT_PROJECT)
    pushd $REPODIR/$SHORT_PROJECT
    if ! git diff --quiet ; then
        git commit -a -m'Update requirements'
    fi
    popd

    # Clone from synced repo
    shortprojectdir=$projectdir/$SHORT_PROJECT
    git clone $REPODIR/$SHORT_PROJECT $shortprojectdir

    # Test that we can make a tarball from scratch
    sdistvenv=$tmpdir/sdist
    mkvenv $sdistvenv
    cd $shortprojectdir
    $sdistvenv/bin/python setup.py sdist

    cd $tmpdir

    # Test that the tarball installs
    tarballvenv=$tmpdir/tarball
    mkvenv $tarballvenv
    $tarballvenv/bin/pip install $shortprojectdir/dist/*tar.gz

    # Test pip installing
    pipvenv=$tmpdir/pip
    mkvenv $pipvenv
    $pipvenv/bin/pip install git+file://$shortprojectdir

    # Test python setup.py install
    installvenv=$tmpdir/install
    mkvenv $installvenv

    installprojectdir=$projectdir/install$SHORT_PROJECT
    git clone $shortprojectdir $installprojectdir
    cd $installprojectdir
    $installvenv/bin/python setup.py install

    # Ensure the install_package_data is doing the thing it should do
    if [ $SHORT_PROJECT = 'nova' ]; then
        find $installvenv | grep migrate.cfg
    fi
done
