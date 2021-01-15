#!/bin/bash

PROCEED=0
for var in $*; do 
   if [[ "$var" == *--client_id=* ]]
   then
      CLIENT_ID="${var/--client_id=/}"
      PROCEED=$((PROCEED + 1))
   fi   
   if [[ "$var" == *--client_secret=* ]]
   then
      CLIENT_SECRET="${var/--client_secret=/}"
      PROCEED=$((PROCEED + 1))      
   fi   
   if [[ "$var" == *--cid=* ]]
   then
      CLIENT_CID="${var/--cid=/}"
      PROCEED=$((PROCEED + 1))      
   fi   
done

OS_NAME=$(cat /etc/*release | grep NAME= | awk '!/CODENAME/ && !/PRETTY_NAME/' | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
OS_NAME=$(echo $OS_NAME | awk '{ print $1 }')
OS_VERSION=$(cat /etc/*release | grep VERSION_ID= | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")

#Shortcut for RHEL 6, might have to change this
if [[ $OS_NAME == "" ]]
then
    OS_NAME="Red"
    OS_VERSION="6"
fi
if [[ $PROCEED -eq 3 ]]
then
    case "$OS_NAME" in
        SLES )
            cd /var/tmp
            curl -o stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/sles/csfalcon-bootstrap-sles.sh
            chmod 755 stage1
            if [[ "$OS_VERSION" == *11* ]]
            then
                curl -o stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/sles/csfalcon-bootstrap-sles11.sh
                chmod 755 stage1
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=sles --osver=11
            elif [[ "$OS_VERSION" == *12* ]]
            then
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=sles --osver=12
            else
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=sles --osver=15
            fi
            ;;
        Amazon )
            cd /var/tmp
            wget -O stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/amazon/csfalcon-bootstrap-amzn-lnx2.sh
            chmod 755 stage1
            #TODO: Add arm detection
            ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=amzn --osver=2
            ;;

        CentOS )
            cd /var/tmp
            curl -o stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/centos/csfalcon-bootstrap-centos.sh
            chmod 755 stage1
            if [[ "$OS_VERSION" == *7* ]]
            then
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=centos --osver=7
            fi
            ;;

        Red )
            cd /var/tmp
            curl -o stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/centos/csfalcon-bootstrap-centos.sh
            chmod 755 stage1
            if [[ "$OS_VERSION" == *7* ]]
            then
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=rhel --osver=7
            elif [[ "$OS_VERSION" == *6* ]]
            then
                rm stage1
                curl -o stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/rhel/csfalcon-bootstrap-rhel6.sh
                chmod 755 stage1
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=rhel --osver=6
            else
                ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=rhel --osver=8
            fi
            ;;
        
        Ubuntu )
            cd /var/tmp
            wget -O stage1 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/debian/csfalcon-bootstrap-debian.sh
            chmod 755 stage1
            #TODO: Add arm / ubuntu version detection
            ./stage1 --client_id=$CLIENT_ID --client_secret=$CLIENT_SECRET --cid=$CLIENT_CID --os=debian --osver=9
            ;;

    esac
    rm stage1
fi