#!/bin/bash
#
# Distributor package installer - Ubuntu based distros
#
filename="falcon-sensor.deb"

rpmInstall() {
  apt-get install -y libnl-3-200 libnl-genl-3-200
  dpkg -i "$1"
  echo "/opt/CrowdStrike/falconctl -s -f --cid=$2 $3" >>log.txt
  /opt/CrowdStrike/falconctl -s -f --cid="$2" $3
  systemctl restart falcon-sensor
  rm $1
}

rpmInstall $filename $SSM_CS_CCID $SSM_CS_INSTALLPARAMS