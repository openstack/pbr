#!/bin/bash -xe
# Parameters:
# PBR_PIP_VERSION :- if not set, run pip's latest release, if set must be a
#    valid reference file entry describing what pip to use.
# WHEELHOUSE :- if not set, use a temporary wheelhouse, set to a specific path
#    to use an existing one.
# PIPFLAGS :- may be set to any pip global option for e.g. debugging.
# Bootstrappping the mkenv needs to install *a* pip
export PIPVERSION=pip
PIPFLAGS=${PIPFLAGS:-}

function mkvenv {
    venv=$1

    rm -rf $venv
    virtualenv -p python3 $venv
    $venv/bin/pip install $PIPFLAGS -U $PIPVERSION wheel

    # If a change to PBR is being tested, preinstall the wheel for it
    if [ -n "$PBR_CHANGE" ] ; then
        $venv/bin/pip install $PIPFLAGS $pbrsdistdir/dist/pbr-*.whl
    fi
}

# BASE should be a directory with a subdir called "openstack" and in that
#      dir, there should be a git repository for every entry in PROJECTS
BASE=${BASE:-/home/zuul/src/opendev.org/}

REPODIR=${REPODIR:-$BASE/openstack}

# TODO: Figure out how to get this on to the box properly
sudo apt-get update
sudo apt-get install -y --force-yes libvirt-dev libxml2-dev libxslt-dev libmysqlclient-dev libpq-dev libnspr4-dev pkg-config libsqlite3-dev libffi-dev libldap2-dev libsasl2-dev ccache libkrb5-dev liberasurecode-dev libjpeg-dev libsystemd-dev libnss3-dev libssl-dev libpcre3-dev

# FOR pyyaml
sudo apt-get install -y --force-yes debhelper python3-all-dev python3-all-dbg libyaml-dev cython3 quilt

# And use ccache explitly
export PATH=/usr/lib/ccache:$PATH

tmpdir=$(mktemp -d)

# Set up a wheelhouse
export WHEELHOUSE=${WHEELHOUSE:-$tmpdir/.wheelhouse}
mkvenv $tmpdir/wheelhouse
# Specific PIP version - must succeed to be useful.
# - build/download a local wheel so we don't hit the network on each venv.
if [ -n "${PBR_PIP_VERSION:-}" ]; then
    td=$(mktemp -d)
    $tmpdir/wheelhouse/bin/pip wheel -w $td $PBR_PIP_VERSION
    # This version will now be installed in every new venv.
    export PIPVERSION="$td/$(ls $td)"
    $tmpdir/wheelhouse/bin/pip install -U $PIPVERSION
    # We have pip in global-requirements as open-ended requirements,
    # but since we don't use -U in any other invocations, our version
    # of pip should be sticky.
fi
# Build wheels for everything so we don't hit the network on each venv.
# Not all packages properly build wheels (httpretty for example).
# Do our best but ignore errors when making wheels.
set +e
$tmpdir/wheelhouse/bin/pip $PIPFLAGS wheel -w $WHEELHOUSE -f $WHEELHOUSE -r \
    $REPODIR/requirements/global-requirements.txt
set -e

#BRANCH
BRANCH=${OVERRIDE_ZUUL_BRANCH=:-master}
# PROJECTS is a list of projects that we're testing
PROJECTS=$*

pbrsdistdir=$tmpdir/pbrsdist
git clone $REPODIR/pbr $pbrsdistdir
cd $pbrsdistdir

# Capture Zuul repo state info. Local master should be the current change.
# origin/master should refer to the parent of the current change. If they
# are the same then there is no change either from zuul or locally.
git --git-dir $REPODIR/pbr/.git show --format=oneline --no-patch master
git --git-dir $REPODIR/pbr/.git show --format=oneline --no-patch origin/master
# If there is no diff between the branches then there is no local change.
if ! git --git-dir $REPODIR/pbr/.git diff --quiet master..origin/master ; then
    git show --format=oneline --no-patch HEAD
    mkvenv wheel
    # TODO(clarkb) switch to using build tool here
    wheel/bin/pip install setuptools
    wheel/bin/python setup.py bdist_wheel
    PBR_CHANGE=1
fi

##### Test Project Installation #####
# Create a test project and install it multiple different ways
# using different tools to sanity check behavior is consistent
# with what expect and doesn't change.
# TODO(clarkb) Add test coverage for build and wheel tools too.
eptest=$tmpdir/eptest
mkdir $eptest
cd $eptest

cat <<EOF > setup.cfg
[metadata]
name = test_project

[entry_points]
console_scripts =
    test_cmd = test_project:main
EOF

cat <<EOF > setup.py
import setuptools

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)
EOF

mkdir test_project
cat <<EOF > test_project/__init__.py
def main():
    print("Test cmd")
EOF

eppbrdir=$tmpdir/eppbrdir
git clone $REPODIR/pbr $eppbrdir

function check_setuppy {
    local checkname
    checkname=$1

    local epvenv
    epvenv=$eptest/setuppyvenv_$checkname
    mkvenv $epvenv
    $epvenv/bin/pip $PIPFLAGS install -f $WHEELHOUSE -e $eppbrdir
    # We install setuptools only in this venv to check setup.py
    # behaviors.
    $epvenv/bin/pip $PIPFLAGS install -f $WHEELHOUSE setuptools

    # First check develop
    PBR_VERSION=0.0 $epvenv/bin/python setup.py develop
    cat $epvenv/bin/test_cmd
    grep 'PBR Generated' $epvenv/bin/test_cmd
    $epvenv/bin/test_cmd | grep 'Test cmd'
    PBR_VERSION=0.0 $epvenv/bin/python setup.py develop --uninstall

    # Now check install
    PBR_VERSION=0.0 $epvenv/bin/python setup.py install
    cat $epvenv/bin/test_cmd
    grep 'PBR Generated' $epvenv/bin/test_cmd
    $epvenv/bin/test_cmd | grep 'Test cmd'
}

function check_pip {
    local checkname
    checkname=$1

    local epvenv
    epvenv=$eptest/pipvenv_$checkname
    mkvenv $epvenv
    $epvenv/bin/pip $PIPFLAGS install -f $WHEELHOUSE -e $eppbrdir

    # First check develop
    PBR_VERSION=0.0 $epvenv/bin/pip install -e ./
    cat $epvenv/bin/test_cmd
    if [ -f ./pyproject.toml ] ; then
        # Pip dev installs with pyproject.toml build from editable wheels
        # which do not use PBR generated console scripts.
        grep 'from test_project import main' $epvenv/bin/test_cmd
        ! grep 'PBR Generated' $epvenv/bin/test_cmd
    else
        # Otherwise we should get the PBR generated script
        grep 'PBR Generated' $epvenv/bin/test_cmd
    fi
    $epvenv/bin/test_cmd | grep 'Test cmd'
    PBR_VERSION=0.0 $epvenv/bin/pip uninstall -y test-project

    # Now check install
    PBR_VERSION=0.0 $epvenv/bin/pip install ./
    cat $epvenv/bin/test_cmd
    # Pip installs install from wheel builds which do not use
    # PBR generated console scripts.
    grep 'from test_project import main' $epvenv/bin/test_cmd
    ! grep 'PBR Generated' $epvenv/bin/test_cmd
    $epvenv/bin/test_cmd | grep 'Test cmd'
}

### No pyproject.toml ###
# Check setup.py behavior
check_setuppy nopyprojecttoml

# Check pip behavior
check_pip nopyprojecttoml

### pyproject.toml ###
# Now write a pyproject.toml and recheck the results.
# Note the pip install -e behavior differs.
cat <<EOF > pyproject.toml
[build-system]
requires = [
  "pbr>=6.0.0",
  "setuptools>=64.0.0",
]
build-backend = "pbr.build"
EOF

# Check setup.py behavior
check_setuppy pyprojecttoml

# Check pip behavior
check_pip pyprojecttoml

projectdir=$tmpdir/projects
mkdir -p $projectdir
sudo chown -R $USER $REPODIR

export PBR_INTEGRATION=1
export PIPFLAGS
export PIPVERSION
PBRVERSION=pbr
if [ -n "$PBR_CHANGE" ] ; then
    PBRVERSION=$(ls $pbrsdistdir/dist/pbr-*.whl)
fi
export PBRVERSION
export PROJECTS
export REPODIR
export WHEELHOUSE
export OS_TEST_TIMEOUT=1200
cd $REPODIR/pbr
mkvenv .venv
source .venv/bin/activate
pip install -r test-requirements.txt
pip install ${REPODIR}/requirements
stestr run --suppress-attachments test_integration
