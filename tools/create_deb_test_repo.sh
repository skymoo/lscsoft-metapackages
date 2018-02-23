#!/bin/bash

# this will create a local package repository suitable for testing only
# external variables which may need to be set
# REMOTE: target where to rsync to (needed)
# LOCALREPO: where to place the local repository (defaults to /tmp/metatest)
# TARGETDIST: target distribution (jessie/stretch/...; defaults to whatever is set here ;)

# in the testing chroot one should run (with aptly chosen $TARGETDIST)
# echo "deb http://software.ligo.org/lscsoft/debian/ $TARGETDIST contrib" > /etc/apt/sources.list.d/lscsoft.list
# echo "deb  [ allow-insecure=yes allow-weak=yes allow-downgrade-to-insecure=yes ] file:///tmp/metatest /" > /etc/apt/sources.list.d/metatest.list

if [[ -z "$REMOTE" ]]
then
    echo "Environment variable REMOTE needs to be set!"
    exit 1
fi

LOCALREPO=${LOCALREPO:-/tmp/metatest}
TARGETDIST=${TARGETDIST:-stretch}

# ensure we are at the top level of our repo management
if [[ ! -d "./stage" || ! -d "./meta" ]]
then
    echo "This script needs to be run from the top level directory"
    exit 1
fi

# pretty lazy/dangerous
# needed to enfore rebuild of test packages without increased version numbers
rm -rf ./stage/lscsoft-*

# let the magic begin
./generate.rb

for i in stage/*/deb/
do
    printf "############# % 40s ###############\n" $i
    (cd $i; equivs-build control >/dev/null)
done

find ./stage -name "*deb" -type f | xargs -i rsync -a {} $LOCALREPO

(cd $LOCALREPO
 rm -f Packages.gz Packages
 dpkg-scanpackages -m . > Packages
 gzip --keep --force -9 Packages
 cat > Release <<EOF
Origin: metatest
Label: metatest
Codename: $TARGETDIST
Architectures: amd64
Components: contrib
Description: metatest
EOF
 echo -e "Date: `LANG=C date -Ru`" >> Release

 echo -e 'MD5Sum:' >> Release
 printf ' '$(md5sum Packages.gz | cut --delimiter=' ' --fields=1)' %16d Packages.gz' $(wc --bytes Packages.gz | cut --delimiter=' ' --fields=1) >> Release
 printf '\n '$(md5sum Packages | cut --delimiter=' ' --fields=1)' %16d Packages' $(wc --bytes Packages | cut --delimiter=' ' --fields=1) >> Release

 echo -e '\nSHA256:' >> Release
 printf ' '$(sha256sum Packages.gz | cut --delimiter=' ' --fields=1)' %16d Packages.gz' $(wc --bytes Packages.gz | cut --delimiter=' ' --fields=1) >> Release
 printf '\n '$(sha256sum Packages | cut --delimiter=' ' --fields=1)' %16d Packages' $(wc --bytes Packages | cut --delimiter=' ' --fields=1) >> Release

)

rsync -a /tmp/metatest "$REMOTE/tmp"

exit 0
