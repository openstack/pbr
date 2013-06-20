#!/bin/bash -xe

function mkvenv {
    venv=$1
    setuptools=$2
    pip=$3

    rm -rf $venv
    if [ "$setuptools" == 'distribute' ] ; then
        virtualenv --distribute $venv
    elif [ "$setuptools" == 'setuptools' ] ; then
        virtualenv $venv
    else
        virtualenv $venv
        $venv/bin/pip install -v -U $setuptools
    fi
    $venv/bin/pip install $pip
}

# PROJECTS is a list of projects that we're testing
PROJECTS=$*

# BASE should be a directory with a subdir called "new" and in that
#      dir, there should be a git repository for every entry in PROJECTS
BASE=${BASE:-/opt/stack}

REPODIR=${REPODIR:-$BASE/new}

# TODO: Figure out how to get this on to the box properly
sudo apt-get install -y --force-yes libxml2-dev libxslt-dev libmysqlclient-dev libpq-dev libnspr4-dev pkg-config libsqlite3-dev libzmq-dev

tmpdir=`mktemp -d`

whoami=`whoami`
tmpdownload=$tmpdir/download
mkdir -p $tmpdownload

pypidir=$tmpdir/pypi
mkdir -p $pypidir

jeepybvenv=$tmpdir/jeepyb

rm -f ~/.pip/pip.conf ~/.pydistutils.cfg

mkvenv $jeepybvenv distribute pip
$jeepybvenv/bin/pip install -U git+https://review.openstack.org/p/openstack-infra/jeepyb.git

cat <<EOF > $tmpdir/mirror.yaml
cache-root: $tmpdownload

mirrors:
  - name: openstack
    projects:
      - https://github.com/openstack/requirements
    output: $pypidir
EOF

pbrsdistdir=$tmpdir/pbrsdist
git clone $REPODIR/pbr $pbrsdistdir
cd $pbrsdistdir

$jeepybvenv/bin/run-mirror -b remotes/origin/master --verbose -c $tmpdir/mirror.yaml --no-process

$jeepybvenv/bin/pip install -i http://pypi.python.org/simple -d $tmpdownload/pip/openstack 'pip==1.0' 'setuptools>=0.7'
$jeepybvenv/bin/pip install -i http://pypi.python.org/simple -d $tmpdownload/pip/openstack 'setuptools<0.7'

$jeepybvenv/bin/pip install -i http://pypi.python.org/simple -d $tmpdownload/pip/openstack -r requirements.txt
$jeepybvenv/bin/python setup.py sdist -d $tmpdownload/pip/openstack

$jeepybvenv/bin/run-mirror -b remotes/origin/master --verbose -c $tmpdir/mirror.yaml --no-download

# Make pypi thing
pypiurl=file://$pypidir

cat <<EOF > ~/.pydistutils.cfg
[easy_install]
index_url = $pypiurl
EOF

mkdir -p ~/.pip
cat <<EOF > ~/.pip/pip.conf
[global]
index-url = $pypiurl
extra-index-url = http://pypi.openstack.org/openstack
EOF

projectdir=$tmpdir/projects
mkdir -p $projectdir

for PROJECT in $PROJECTS ; do
    SHORT_PROJECT=`basename $PROJECT`
    if ! grep 'pbr' $REPODIR/$SHORT_PROJECT/requirements.txt >/dev/null 2>&1
    then
        # project doesn't use pbr
        continue
    fi
    if [ $SHORT_PROJECT = 'tempest' ]; then
        # Tempest doesn't really install
        continue
    fi
    shortprojectdir=$projectdir/$SHORT_PROJECT
    git clone $REPODIR/$SHORT_PROJECT $shortprojectdir

    sdistvenv=$tmpdir/sdist

    # Test that we can make a tarball from scratch
    mkvenv $sdistvenv distribute pip
    cd $shortprojectdir
    $sdistvenv/bin/python setup.py sdist

    # Test that the tarball installs
    cd $tmpdir
    tarballvenv=$tmpdir/tarball
    mkvenv $tarballvenv 'setuptools>=0.7' 'pip>=1.3,<1.4'
    $tarballvenv/bin/pip install $shortprojectdir/dist/*tar.gz

    # Test pip installing
    pipvenv=$tmpdir/pip
    mkvenv $pipvenv setuptools 'pip==1.0'
    cd $tmpdir
    echo $pipvenv/bin/pip install git+file://$REPODIR/$SHORT_PROJECT
    $pipvenv/bin/pip install git+file://$REPODIR/$SHORT_PROJECT

    # Test python setup.py install
    installvenv=$tmpdir/install
    mkvenv $installvenv setuptools pip
    installprojectdir=$projectdir/install$SHORT_PROJECT
    git clone $REPODIR/$SHORT_PROJECT $installprojectdir
    cd $installprojectdir
    $installvenv/bin/python setup.py install

    # TODO(mordred): extend script to do a better job with the mirrir
    # easy_install to a file:/// can't handle name case insensitivity
    # Test python setup.py develop
    # developvenv=$tmpdir/develop
    # mkvenv $developvenv setuptools pip
    # developprojectdir=$projectdir/develop$SHORT_PROJECT
    # git clone $REPODIR/$SHORT_PROJECT $developprojectdir
    # cd $developprojectdir
    # $developvenv/bin/python setup.py develop

    # TODO(mordred): need to implement egg filtering
    # Because install will have caused eggs to be locally downloaded
    # pbr and d2to1 can get excluded from being in the actual venv
    # test that this did not happen
    # $tempvenv/bin/python -c 'import pkg_resources as p; import sys; pbr=p.working_set.find(p.Requirement.parse("pbr")) is None; sys.exit(pbr or 0)'
done
