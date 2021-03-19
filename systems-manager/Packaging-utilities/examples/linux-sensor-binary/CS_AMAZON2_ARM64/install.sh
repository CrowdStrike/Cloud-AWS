#!/bin/bash
#
# Modify the `filename` value to match the installer in the directory
# Modify the `TARGET_VER` value to match your desired minimum version
#
filename="falcon-sensor-6.16.0-11308.amzn2.aarch64.rpm"
TARGET_VER=5.38.10404
CS_API_BASE=${CS_API_BASE:-api.crowdstrike.com}

echoRed() {
  echo -e "\033[0;31m$1\033[0m"
  echo ""
}

usage() {
  cat <<EOF
Script to download and install the CrowdStrike Falcon sensor.

Usage:

AWS Systems Manager (SSM) integration:
  SSM_CS_AUTH_TOKEN will override the value of CS_FALCON_OAUTH_TOKEN.
  SSM_CS_CCID will override the value of CS_FALCON_CID
  SSM_CS_NCNT will set the "N-" version count. (2 = N-2 version)
  SSM_CS_INSTALLPARAMS will set installer parameters, overriding environment / parameter values
  SSM_CS_INSTALLTOKEN will set the provisioning token, overriding environment / parameter values

EOF
}

osDetail() {
  UN=$(uname -s)
  if [[ "$UN" == "Darwin" ]]; then
    OS_NAME="Darwin"
    OS_VERSION=$(uname -r)
  else
    OS_NAME=$(cat /etc/*release | grep NAME= | awk '!/CODENAME/ && !/PRETTY_NAME/' | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
    OS_NAME=$(echo $OS_NAME | awk '{ print $1 }')
    OS_VERSION=$(cat /etc/*release | grep VERSION_ID= | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
  fi
}

install() {
  if [[ "$PACKAGER" == "yum" || "$PACKAGER" == "zypper" ]]; then
    rpmInstall $filename "$CS_FALCON_CID" "$CS_INSTALL_TOKEN"
  fi
  if [[ "$PACKAGER" == "apt" ]]; then
    aptInstall $filename "$CS_FALCON_CID" "$CS_INSTALL_TOKEN"
  fi
}

rpmInstall() {
  yum install libnl -y
  rpm -ivh "$1"
  /opt/CrowdStrike/falconctl -s -f --cid="$2" "$3" "$4"
  systemctl restart falcon-sensor
  rm $1
}

aptInstall() {
  # May need to move this over to snap for Ubuntu 20
  apt-get -y install libnl-genl-3-200 libnl-3-200
  sudo dpkg -i $1
  apt-get -y --fix-broken install
  /opt/CrowdStrike/falconctl -s -f --cid="$2" "$3" $4
  service falcon-sensor restart
  rm $1
}

if [ "$1" = "-h" ]; then
  usage
  exit
fi

NCNT=${SSM_CS_NCNT}
if [ -z "$NCNT" ]; then
  NCNT=0
fi
CS_FALCON_OAUTH_TOKEN=${CS_FALCON_OAUTH_TOKEN}
if ! [ -z "$SSM_CS_AUTH_TOKEN" ]; then
  CS_FALCON_OAUTH_TOKEN=${SSM_CS_AUTH_TOKEN}
fi

if ! [ -z "$SSM_CS_CCID" ]; then
  CS_FALCON_CID=${SSM_CS_CCID}
fi

if ! [ -z "$3" ] || ! [ -z "$4" ]; then
  CS_FALCON_OAUTH_TOKEN=$1
  CS_FALCON_CID=$2
  CS_INSTALL_PARAMS=$3
  CS_INSTALL_TOKEN="--provisioning-token=$4"
else
  if ! [ -z "$1" ]; then
    CS_FALCON_CLIENT_ID=$1
    CS_FALCON_CLIENT_SECRET=$2
    CS_FALCON_CID=$3
    CS_INSTALL_PARAMS=$4
    CS_INSTALL_TOKEN="--provisioning-token=$5"
  fi
fi

if ! [ -z "$SSM_CS_INSTALLPARAMS" ]; then
  CS_INSTALL_PARAMS=${SSM_CS_INSTALLPARAMS}
fi
if ! [ -z "$SSM_CS_INSTALLTOKEN" ]; then
  CS_INSTALL_TOKEN="--provisioning-token=${SSM_CS_INSTALLTOKEN}"
fi

if [ -z "$CS_FALCON_OAUTH_TOKEN" ] && [ -z "$CS_FALCON_CLIENT_ID" ] && [ -z "$CS_FALCON_CLIENT_SECRET" ]; then
  echoRed "Missing Falcon OAUTH Token or Client ID and Secret Environment Variable(s)"
  usage
  exit 1
elif [ -z "$CS_FALCON_OAUTH_TOKEN" ]; then
  if [ -z "$CS_FALCON_CLIENT_ID" ] || [ -z "$CS_FALCON_CLIENT_SECRET" ]; then
    echoRed "If using CS_FALCON_CLIENT_ID and CS_FALCON_CLIENT_SECRET, both must be set."
    exit 1
  else
    # Let's get a token
    tokenResult=$(curl -X POST -s -L "https://$CS_API_BASE/oauth2/token" \
      -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' \
      -d "client_id=$CS_FALCON_CLIENT_ID&client_secret=$CS_FALCON_CLIENT_SECRET")
    CS_FALCON_OAUTH_TOKEN=$(echo "$tokenResult" | jsonValue "access_token" | sed 's/ *$//g' | sed 's/^ *//g')
    if [ -z "$CS_FALCON_OAUTH_TOKEN" ]; then
      echoRed "Unable to retrieve oauth token from api"
      exit 1
    fi
  fi
fi

if [ -z "$CS_FALCON_CID" ]; then
  echoRed "CS_FALCON_CID must be provided in order to perform installation."
  exit 1
fi

osDetail

case "$OS_NAME" in
deb?* | Deb?* | ubu?* | Ubu?*)
  OS_NAME="Debian"
  PACKAGER="apt"
  ;;
rhel | RHEL | red?* | cent?* | Red?* | Cent?* | ora?* | Ora?*)
  OS_NAME="RHEL/CentOS/Oracle"
  PACKAGER="yum"
  ;;
sles | SLES)
  OS_NAME="SLES"
  PACKAGER="zypper"
  ;;
amz?* | Ama?* | ama?*)
  OS_NAME="Amazon Linux"
  PACKAGER="yum"
  ;;
win?* | Win?*)
  OS_NAME="Windows"
  PACKAGER="exe"
  ;;
esac

echo "Sensor binary output to: $filename"

if pgrep falcon-sensor >/dev/null; then
  TARGET_VER_INT=$(echo $TARGET_VER | awk -F. '{ print  $1$2$3$4}')
  FALCON_VER=$(sudo /opt/CrowdStrike/falconctl -g --version | awk -F= '{ print  $2}' | awk -F. '{ print  $1$2$3$4}')
  if [ "$FALCON_VER" -lt "$TARGET_VER_INT" ]; then
    echo "Install required"
    install
  else
    echo "Install not required"
    exit
  fi
else
  echo "Falcon-sensor not found"
  echo "Install required"
  install
fi
