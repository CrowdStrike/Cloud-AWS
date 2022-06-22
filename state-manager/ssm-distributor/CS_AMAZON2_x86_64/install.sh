#!/bin/bash
#
# Distributor package installer - Amazon Linux 2 / RPM based distros
#
filename="falcon-sensor.rpm"

rpmInstall() {
  yum install libnl -y
  rpm -ivh "$1"
  echo "/opt/CrowdStrike/falconctl -s -f --cid=$2" >>log.txt
  /opt/CrowdStrike/falconctl -s -f --cid="$2" $3
  systemctl restart falcon-sensor
  rm $1
}

rpmInstall $filename $SSM_CS_CCID $SSM_CS_INSTALLPARAMS