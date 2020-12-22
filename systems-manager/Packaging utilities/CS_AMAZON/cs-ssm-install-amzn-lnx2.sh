#!/bin/bash
# CrowdStrike Falcon Agent bootstrap - Amazon Linux
#$SSM_CS_AUTH_TOKEN --cid=$SSM_CS_CCID
OS_VERSION=""
PROCEED=0
for var in $*; do
  if [[ "$var" == *--auth_token=* ]]; then
    SSM_CS_AUTH_TOKEN="${var/--auth_token=/}"
    PROCEED=$((PROCEED + 1))
  fi
  if [[ "$var" == *--cid=* ]]; then
    CLIENT_CID="${var/--cid=/}"
    PROCEED=$((PROCEED + 1))
  fi
  if [[ "$var" == *--os=* ]]; then
    OS_NAME="${var/--os=/}"
    PROCEED=$((PROCEED + 1))
  fi
  if [[ "$var" == *--osver=* ]]; then
    OS_VERSION="${var/--osver=/}"
    PROCEED=$((PROCEED + 1))
  fi
done

if [[ $PROCEED -eq 4 ]]; then
  #cd /var/tmp
  #wget -O stage2 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/systems-manager/Packaging%20utilities/CS_AMAZON/cs-ssm-sensor_download.sh
  #chmod +x stage2
  ./cs-ssm-sensor_download.sh $OS_NAME $OS_VERSION . $SSM_CS_AUTH_TOKEN
  rpm -ivh --nodeps sensor.rpm
  /opt/CrowdStrike/falconctl -s -f --cid=$CLIENT_CID
  systemctl restart falcon-sensor
  #rm stage2
  rm sensor.rpm
else
  echo "Invalid attributes. Check syntax and try again."
  echo "csfalcon-bootstrap-amzn-lnx2.sh --client_id=(CLIENT_ID) --client_secret=(CLIENT_SECRET) --cid=(CID) --os=(OS_NAME) { --osver=(OS_VERSION) }"
fi

exit
