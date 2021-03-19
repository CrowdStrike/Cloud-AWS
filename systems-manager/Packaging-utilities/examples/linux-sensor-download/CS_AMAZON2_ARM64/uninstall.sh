#! /bin/bash

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

rpmUninstall(){
   yum remove falcon-sensor -y
}

aptUninstall(){
   apt-get -y remove falcon-sensor
}

getAID(){
    AID=$(/opt/CrowdStrike/falconctl -g --aid)
    AID=${AID/aid=/}
    AID=${AID/./}
}

hideHost(){
    curl  -X POST "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name=hide_host" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
       	-d "{ \"ids\": [$AID]}" 
}


AUTH_TOKEN=${SSM_CS_AUTH_TOKEN}
getAID
osDetail
case "$OS_NAME" in
    deb?*|Deb?*|ubu?*|Ubu?* )
        PACKAGER="apt"
        ;;
    rhel|RHEL|red?*|cent?*|Red?*|Cent?*|ora?*|Ora?* )
        PACKAGER="yum"
        ;;
    sles|SLES )
        PACKAGER="zypper"
        ;;
    amz?*|Ama?*|ama?* )
        PACKAGER="yum"
        ;;
    win?*|Win?* )
        PACKAGER="exe"
        ;;
esac
if [ "$PACKAGER" == "apt" ]
then
    aptUninstall
    hideHost
elif [ "$PACKAGER" == "yum" ] || [ "$PACKAGER" == "zypper" ]
then
    rpmUninstall
    hideHost
fi

