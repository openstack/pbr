#!/bin/bash -xe

# PROJECTS is a list of projects that we're testing
PROJECTS=$1

# BASE should be a directory with a subdir called "new" and in that
#      dir, there should be a git repository for every entry in PROJECTS
BASE=$2

REPODIR=${REPODIR:-$BASE/new}

tmpdir=`mkdtemp`

tmpdownload=`mktemp -d`
tmpvenv=$tmpdownload/venv
virtualenv $tempvenv
cd $REPODIR/pbr
$tempvenv/bin/pip install -d $tmpdownload -r requirements.txt
$tempvenv/bin/python setup.py sdist -d $tmpdownload

# Make pypi thing
pypidir=`mktemp -d`
pypiurl=file://$pypidir
echo "<html><body>" > $pypidir/index.html
for fulltarball in $tmpdownload/*.tar.gz ; do
    tarball=`basename $fulltarball`
    name=`echo $tarball | sed 's/-[^-]*.tar.gz//'`
    md5=`md5sum $fulltarball | awk '{print $1}'`
    subdir=$pypidir/$name
    mkdir -p $subdir
    mv $fulltarball $subdir
    echo "<a href='$tarball#md5=$md5'>$tarball</a>" >>$subdir/index.html
    if ! grep $name $pypidir/index.html >/dev/null 2>&1 ; then
        echo "<a href='$name'>$name</a>" >>$pypidir/index.html
    fi
done
echo "</body></html>" >> $pypidir/index.html
rm -rf $tmpdownload


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

# Test that pbr installs in different combinations
for setuptools in 'setuptools' 'setuptools>=0.7' 'distribute' ; do
    for pip in 'pip==1.0' 'pip>=1.3,<1.4' ; do
        for PROJECT in $PROJECTS ; do
            SHORT_PROJECT=`basename $PROJECT`
            tmpdir=`mktemp -d`
            tmpvenv=$tmpdir/venv

            # Test pip installing
            mkvenv $tmpvenv $setuptools $pip
            cd $tmpdir
            $tempvenv/bin/pip install git+file://$REPODIR/$SHORT_PROJECT

            # Test python setup.py install
            mkvenv $tmpvenv $setuptools $pip
            cd $REPODIR/$SHORT_PROJECT
            $tempvenv/bin/python setup.py install

            # Because install will have caused eggs to be locally downloaded
            # pbr and d2to1 can get excluded from being in the actual venv
            # test that this did not happen
            $tempvenv/bin/python -c 'import pkg_resources as p; import sys; pbr=p.working_set.find(p.Requirement.parse("pbr")) is None; sys.exit(pbr or 0)'

            # Test that we can make a tarball from scratch
            mkvenv $tmpvenv $setuptools $pip
            $tempvenv/bin/python setup.py sdist

            # Test that the tarball installs
            cd $tmpdir
            mkvenv $tmpvenv $setuptools $pip
            $tempvenv/bin/pip install $REPODIR/$SHORT_PROJECT/dist/*tar.gz

            rm -rf $tmpdir
        done
    done
done
