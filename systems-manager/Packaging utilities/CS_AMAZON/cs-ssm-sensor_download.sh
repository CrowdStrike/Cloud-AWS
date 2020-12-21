#!/bin/bash

CS_API_BASE=${CS_API_BASE:-api.crowdstrike.com}

echoRed() {
  echo -e "\033[0;31m$1\033[0m"
  echo ""
}

jsonValue() {
  KEY=$1
  num=$2
  awk -F"[,:}]" '{for(i=1;i<=NF;i++){if($i~/'"$KEY"'\042/){print $(i+1)}}}' | tr -d '"' | sed -n "${num}p"
}

usage() {
  cat <<EOF
Script to download the CrowdStrike Falcon sensor

Usage:
 cssensor_download <OS_NAME> [OS_VERSION] <OUTPUT_DESTINATION>

Arguments:
 CS_FALCON_OAUTH_TOKEN: This is the OAUTH2 token from the CrowdStrike API
 OS_NAME: This is the name of the desired operating system
    Supported Values:
      - Debian (or variations: deb, Deb)
      - RHEL/CentOS/Oracle (or variations: rhel, centos, CentOS, Oracle, oracle)
      - Windows (or variations: win, Win, windows)
 OS_VERSION: This is an optional argument to specify the OS Version.
    Supported Operating Systems:
      - Debian (only has 9 right now)
      - RHEL/CentOS/Oracle (7, 8, 9)
 OUTPUT_DESTINATION: The directory path that the sensor file will be downloaded to.


EOF
}

if [ "$1" = "-h" ]; then
  usage
  exit
fi

OS_NAME=$1
OS_VERSION=$2
OUTPUT_DESTINATION=$3
SSM_CS_AUTH_TOKEN=$4

if [ -z "$OS_NAME" ]; then
  echoRed "Must supply an os name as the first argument to this script"
  usage
  exit 1
elif [ ! -d "$OUTPUT_DESTINATION" ] && [ ! -d "$OS_VERSION" ]; then
  echoRed "Must specify an output destination for the binary"
  usage
  exit 1
elif [ ! -d "$OUTPUT_DESTINATION" ] && [ -d "$OS_VERSION" ]; then
  OUTPUT_DESTINATION=$OS_VERSION
  OS_VERSION=""
fi

case "$OS_NAME" in
deb?*)
  OS_NAME="Debian"
  ;;
rhel)
  OS_NAME="RHEL/CentOS/Oracle"
  ;;
centos)
  OS_NAME="RHEL/CentOS/Oracle"
  ;;
CentOS)
  OS_NAME="RHEL/CentOS/Oracle"
  ;;
oracle)
  OS_NAME="RHEL/CentOS/Oracle"
  ;;
Oracle)
  OS_NAME="RHEL/CentOS/Oracle"
  ;;
sles)
  OS_NAME="SLES"
  ;;
amzn)
  OS_NAME="Amazon Linux"
  ;;
win?*)
  OS_NAME="Windows"
  ;;
Win?*)
  OS_NAME="Windows"
  ;;
esac

## Get Installer Versions
jsonResult=$(curl -s -L -G "https://$CS_API_BASE/sensors/combined/installers/v1" --data-urlencode "filter=os:\"$OS_NAME\"" -H "Authorization: Bearer $CS_FALCON_OAUTH_TOKEN")

if [[ $jsonResult == *"denied"* ]]; then
  echoRed "Invalid Access Token"
  exit 1
fi
#echo $jsonResult
sha_list=$(echo "$jsonResult" | jsonValue "sha256")
if [ -z "$sha_list" ]; then
  echoRed "No sensor found for with OS Name: $OS_NAME"
  exit 1
fi

INDEX=1
if [ -n "$OS_VERSION" ]; then
  found=0
  IFS=$'\n'
  for l in $(echo "$jsonResult" | jsonValue "os_version"); do
    l=$(echo "$l" | sed 's/ *$//g' | sed 's/^ *//g')
    if [ "$l" = "$OS_VERSION" ]; then
      found=1
      break
    fi
    ((INDEX += 1))
  done
  if [ $found = 0 ]; then
    echoRed "Unable to locate matching sensor: $OS_NAME@$OS_VERSION"
    exit 1
  fi
fi

sha=$(echo "$jsonResult" | jsonValue "sha256" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')
file_type=$(echo "$jsonResult" | jsonValue "file_type" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')

if [ -z "$sha" ]; then
  echoRed "Unable to identify a sha matching sensor: $OS_NAME@$OS_VERSION"
  exit 1
fi

filename="$OUTPUT_DESTINATION/sensor.$file_type"

curl -s -L "https://$CS_API_BASE/sensors/entities/download-installer/v1?id=$sha" -H "Authorization: Bearer $CS_FALCON_OAUTH_TOKEN" -o "$filename"

echo "Output the sensor binary to: $filename"
