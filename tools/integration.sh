#!/bin/bash -xe

function mkvenv {
    venv=$1

    rm -rf $venv
    virtualenv $venv
    $venv/bin/pip install -U pip wheel
}

# This function takes a list of files that contains
# a list of python packages (in pip freeze format) and
# strips the version info from each entry.
# $1 - The files containing python packages (with version).
function gen_bare_package_list () {
    set +x
    IN_FILES=$1
    for FILE in $IN_FILES
    do
        while read line; do
              if [[ "$line" == "" ]] || [[ "$line" == \#* ]] || [[ "$line" == \-f* ]]; then
                  continue
              elif [[ "$line" == \-e* ]]; then
                  echo "${line#*=}"
              elif [[ "$line" == *\>* ]]; then
                  echo "${line%%>*}"
              elif [[ "$line" == *\=* ]]; then
                  echo "${line%%=*}"
              elif [[ "$line" == *\<* ]]; then
                  echo "${line%%<*}"
              else
                  echo "${line%%#*}"
              fi
        done < $FILE
    done
    set -x
}

# BASE should be a directory with a subdir called "new" and in that
#      dir, there should be a git repository for every entry in PROJECTS
BASE=${BASE:-/opt/stack}

REPODIR=${REPODIR:-$BASE/new}

# TODO: Figure out how to get this on to the box properly
sudo apt-get install -y --force-yes libxml2-dev libxslt-dev libmysqlclient-dev libpq-dev libnspr4-dev pkg-config libsqlite3-dev libzmq-dev libffi-dev libldap2-dev libsasl2-dev

tmpdir=$(mktemp -d)

whoami=$(whoami)
tmpdownload=$tmpdir/download
mkdir -p $tmpdownload

pypidir=/var/www/pypi
sudo mkdir -p $pypidir
sudo chown $USER $pypidir

pypimirrorvenv=$tmpdir/pypi-mirror

sudo touch $HOME/pip.log
sudo chown $USER $HOME/pip.log

rm -f ~/.pip/pip.conf ~/.pydistutils.cfg
mkdir -p ~/.pip
cat <<EOF > ~/.pip/pip.conf
[global]
log = $HOME/pip.log
EOF

pypimirrorsourcedir=$tmpdir/pypimirrorsourcedir
git clone $REPODIR/pypi-mirror $pypimirrorsourcedir

mkvenv $pypimirrorvenv
$pypimirrorvenv/bin/pip install -e $pypimirrorsourcedir

cat <<EOF > $tmpdir/mirror.yaml
cache-root: $tmpdownload

mirrors:
  - name: openstack
    projects:
      - file://$REPODIR/requirements
    output: $pypidir
EOF

# wheel mirrors are below a dir level containing distro and release
# because the wheel format itself does not distinguish
distro=`lsb_release -i -r -s | xargs | tr ' ' '-'`

# set up local apache to serve the mirror we're about to create
if [ ! -d /etc/apache2/sites-enabled/ ] ; then
    echo "Apache does not seem to be installed!!!"
    exit 1
fi

sudo rm /etc/apache2/sites-enabled/*
cat <<EOF > $tmpdir/pypi.conf
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www
    Options Indexes FollowSymLinks
</VirtualHost>
EOF
sudo mv $tmpdir/pypi.conf /etc/apache2/sites-available/pypi
sudo chown root:root /etc/apache2/sites-available/pypi
sudo a2ensite pypi
sudo service apache2 reload

#BRANCH
BRANCH=${OVERRIDE_ZUUL_BRANCH=:-master}
# PROJECTS is a list of projects that we're testing
PROJECTS=$*

pbrsdistdir=$tmpdir/pbrsdist
git clone $REPODIR/pbr $pbrsdistdir
cd $pbrsdistdir

# Note the -b argument here is essentially a noop as
# --no-update is passed as well. The one thing the -b
# does give us is it makes run-mirror install dependencies
# once instead of over and over for all branches it can find.
$pypimirrorvenv/bin/run-mirror -b remotes/origin/$BRANCH --no-update --verbose -c $tmpdir/mirror.yaml --no-process --export=$HOME/mirror_package_list.txt
# Compare packages in the mirror with the list of requirements
gen_bare_package_list "$REPODIR/requirements/global-requirements.txt $REPODIR/requirements/dev-requirements.txt" > bare_all_requirements.txt
gen_bare_package_list $HOME/mirror_package_list.txt > bare_mirror_package_list.txt
echo "Diff between python mirror packages and requirements packages:"
grep -v -f bare_all_requirements.txt bare_mirror_package_list.txt > diff_requirements_mirror.txt
cat diff_requirements_mirror.txt

$pypimirrorvenv/bin/pip install -i http://pypi.python.org/simple -d $tmpdownload/pip/openstack 'pip==1.0' 'setuptools>=0.7' 'd2to1'

$pypimirrorvenv/bin/pip install -i http://pypi.python.org/simple -d $tmpdownload/pip/openstack -r requirements.txt
$pypimirrorvenv/bin/python setup.py sdist -d $tmpdownload/pip/openstack

$pypimirrorvenv/bin/run-mirror -b remotes/origin/$BRANCH --no-update --verbose -c $tmpdir/mirror.yaml --no-download

find $pypidir -type f -name '*.html' -delete
find $pypidir


# Make pypi thing
pypiurl=http://localhost/pypi
export no_proxy=$no_proxy${no_proxy:+,}localhost

cat <<EOF > ~/.pydistutils.cfg
[easy_install]
index_url = $pypiurl
EOF

cat <<EOF > ~/.pip/pip.conf
[global]
index-url = $pypiurl
extra-index-url = $pypiurl/$distro
extra-index-url = http://pypi.openstack.org/openstack
log = $HOME/pip.log
EOF

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
