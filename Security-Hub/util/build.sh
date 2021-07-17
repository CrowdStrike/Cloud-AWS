#!/bin/bash
# !!!NOTE!!! This script is intended to be run on Darwin !!!NOTE!!!
vers=$(cat ../VERSION)

major=$(echo $vers | cut -d . -f 1)
minor=$(echo $vers | cut -d . -f 2)
installer=$(echo $vers | cut -d . -f 3)
installer=$((installer+1))
vers="$major.$minor.$installer"
echo $vers > ../VERSION
contents=('../credvault.py' '../logger.py' '../main.py' '../stream.py' '../install/install.sh' '../service/fig.service')
target="sechub-2.0.$installer-install.run"

for file in "${contents[@]}"
do
    cp $file ../build/.
done
chmod +x ../build/install.sh
makeself --keep-umask ../build $target "Falcon Integration Gateway 2.0" sudo ./install.sh
mv $target ../install
rm ../build/*.py
rm ../build/*.sh
rm ../build/*.service
echo "Build completed."
