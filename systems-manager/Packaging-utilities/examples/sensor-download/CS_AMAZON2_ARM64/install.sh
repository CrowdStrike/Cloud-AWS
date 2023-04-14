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
    cat << EOF
Script to download and install the CrowdStrike Falcon sensor.

Usage:
This script supports two modes of execution and two methods of ingesting variables.
Using parameter arguments:
   cssensor_install <CLIENT_ID> <CLIENT_SECRET> <CLIENT_CID> <INSTALL_PARAMS> <INSTALL_TOKEN>
or
   cssensor_install <CLIENT_OATH_TOKEN> <CLIENT_CID> <INSTALL_PARAMS> <INSTALL_TOKEN>

Using environment variables:
   export CS_FALCON_OAUTH_TOKEN={TOKEN_HERE}
   export CS_FALCON_CID={CID_HERE}
   cssensor_install

Parameter Arguments:
  CLIENT_ID: This is the client_id for the CrowdStrike API Credentials.
  CLIENT_SECRET: This is the client_secret for the CrowdStrike API Credentials.
  CLIENT_CID: This is the Customer CID for the CrowdStrike Falcon API.
  CLIENT_OAUTH_TOKEN: This is the token returned post authentication to the API. 
    If this parameter is passed, CLIENT_ID and CLIENT_SECRET should not be provided.
  
Environment Variables:
  CS_FALCON_OAUTH_TOKEN: Required unless CS_FALCON_CLIENT_ID and CS_FALCON_CLIENT_SECRET are provided
    This is the OAUTH2 token from the CrowdStrike API
  CS_FALCON_CLIENT_ID: Required if CS_FALCON_OAUTH_TOKEN is unset.
    This is the client_id for the CrowdStrike API Credentials. Needs at least "Sensor Download" permissions.
  CS_FALCON_CLIENT_SECRET: Required if CS_FALCON_OAUTH_TOKEN is unset.
    This is the client_secret for the CrowdStrike API Credentials. Needs at least "Sensor Download" permissions.
  CS_FALCON_CID: This is the Customer CID for the CrowdStrike Falcon API.
  CS_INSTALL_PARAMS will set installer parameters
  CS_INSTALL_TOKEN will set the provisioning token

AWS Systems Manager (SSM) integration:
  SSM_CS_AUTH_TOKEN will override the value of CS_FALCON_OAUTH_TOKEN.
  SSM_CS_CCID will override the value of CS_FALCON_CID
  SSM_CS_NCNT will set the "N-" version count. (2 = N-2 version)
  SSM_CS_INSTALLPARAMS will set installer parameters, overriding environment / parameter values
  SSM_CS_INSTALLTOKEN will set the provisioning token, overriding environment / parameter values
EOF
}

osDetail(){
  UN=$(uname -s)
  if [[ "$UN" == "Darwin" ]]
  then
	OS_NAME="Darwin"
	OS_VERSION=$(uname -r)
  else
	OS_NAME=$(cat /etc/*release | grep NAME= | awk '!/CODENAME/ && !/PRETTY_NAME/' | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
	OS_NAME=$(echo $OS_NAME | awk '{ print $1 }')
	OS_VERSION=$(cat /etc/*release | grep VERSION_ID= | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
  fi
}

rpmInstall(){
   yum install libnl -y
   rpm -ivh $1
   /opt/CrowdStrike/falconctl -s -f --cid=$2 $3 $4
   systemctl restart falcon-sensor
   rm $1
}

aptInstall(){
   # May need to move this over to snap for Ubuntu 20
   apt-get -y install libnl-genl-3-200 libnl-3-200
   sudo dpkg -i $1
   apt-get -y --fix-broken install
   /opt/CrowdStrike/falconctl -s -f --cid=$2 $3 $4
   service falcon-sensor restart
   rm $1
}

if [ "$1" = "-h" ]; then
    usage
    exit
fi

NCNT=${SSM_CS_NCNT}
if [ -z "$NCNT" ]
then
  NCNT=0
fi
CS_FALCON_OAUTH_TOKEN=${CS_FALCON_OAUTH_TOKEN}
if ! [ -z "$SSM_CS_AUTH_TOKEN" ]
then
    CS_FALCON_OAUTH_TOKEN=${SSM_CS_AUTH_TOKEN}
fi
CS_FALCON_CLIENT_ID=${CS_FALCON_CLIENT_ID}
CS_FALCON_CLIENT_SECRET=${CS_FALCON_CLIENT_SECRET}
CS_INSTALL_PARAMS=${CS_INSTALL_PARAMS}
CS_INSTALL_TOKEN=${CS_INSTALL_TOKEN}
if ! [ -z "$SSM_CS_CCID" ]
then
    CS_FALCON_CID=${SSM_CS_CCID}
fi

if ! [ -z "$3" ] || ! [ -z "$4" ]
then
    CS_FALCON_OAUTH_TOKEN=$1
    CS_FALCON_CID=$2
    CS_INSTALL_PARAMS=$3
    CS_INSTALL_TOKEN="--provisioning-token=$4"
else
    if ! [ -z "$1" ]
    then
    	CS_FALCON_CLIENT_ID=$1
    	CS_FALCON_CLIENT_SECRET=$2
    	CS_FALCON_CID=$3
        CS_INSTALL_PARAMS=$4
        CS_INSTALL_TOKEN="--provisioning-token=$5"
    fi
fi

if ! [ -z "$SSM_CS_INSTALLPARAMS" ]
then
    CS_INSTALL_PARAMS=${SSM_CS_INSTALLPARAMS}
fi
if ! [ -z "$SSM_CS_INSTALLTOKEN" ]
then
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

if [ -z "$CS_FALCON_CID" ]
then
    echoRed "CS_FALCON_CID must be provided in order to perform installation."
    exit 1
fi

osDetail
OUTPUT_DESTINATION="."

case "$OS_NAME" in
    deb?*|Deb?*|ubu?*|Ubu?* )
        OS_NAME="Debian"
	PACKAGER="apt"
        ;;
    rhel|RHEL|red?*|cent?*|Red?*|Cent?*|ora?*|Ora?* )
        OS_NAME="RHEL/CentOS/Oracle"
    	PACKAGER="yum"
        ;;
    sles|SLES )
        OS_NAME="SLES"
	PACKAGER="zypper"
        ;;
    amz?*|Ama?*|ama?* )
        OS_NAME="Amazon Linux"
	PACKAGER="yum"
        ;;
    win?*|Win?* )
        OS_NAME="Windows"
	PACKAGER="exe"
        ;;
esac

OS_VERSION=2
if [[ "$(uname -p)" != *86* ]]
then
    OS_VERSION="$OS_VERSION - arm64"
fi

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
            ((found+=1))
            if [ "$found" == "$((NCNT+1))" ]
            then
	            break
	    fi
        fi
		((INDEX+=1))
    done
    if [ $found = 0 ]; then
        echoRed "Unable to locate matching sensor: $OS_NAME@$OS_VERSION"
        exit 1
    fi
fi

sha=$(echo "$jsonResult" | jsonValue "sha256" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')
file_type=$(echo "$jsonResult" | jsonValue "file_type" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')
name=$(echo "$jsonResult" | jsonValue "name" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')

if [ -z "$sha" ]; then
    echoRed "Unable to identify a sha matching sensor: $OS_NAME@$OS_VERSION"
    exit 1
fi

filename="$OUTPUT_DESTINATION/$name.$file_type"
#clean up our calculated sha
sha=$(echo $sha | xargs)
curl -s -L "https://$CS_API_BASE/sensors/entities/download-installer/v1?id=$sha" -H "Authorization: Bearer $CS_FALCON_OAUTH_TOKEN" -o "$filename"

echo "Sensor binary output to: $filename"

if [[ "$PACKAGER" == "yum" || "$PACKAGER" == "zypper" ]]
then
	rpmInstall $filename $CS_FALCON_CID $CS_INSTALL_PARAMS $CS_INSTALL_TOKEN
fi
if [[ "$PACKAGER" == "apt" ]]
then
	aptInstall $filename $CS_FALCON_CID $CS_INSTALL_PARAMS $CS_INSTALL_TOKEN
fi


