#!/bin/bash
# CrowdStrike Falcon Agent bootstrap - Amazon Linux

OS_VERSION=""
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
   if [[ "$var" == *--os=* ]]
   then
      OS_NAME="${var/--os=/}"
      PROCEED=$((PROCEED + 1))      
   fi         
   if [[ "$var" == *--osver=* ]]
   then
      OS_VERSION="${var/--osver=/}"
   fi   
done

if [[ $PROCEED -eq 4 ]]
then
   cd /var/tmp
   wget -O stage2 https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/cssensor_download.sh
   chmod 755 stage2
   # export CS_FALCON_CLIENT_ID=$CLIENT_ID
   # export CS_FALCON_CLIENT_SECRET=$CLIENT_SECRET
   ./stage2 $OS_NAME $OS_VERSION . $CLIENT_ID $CLIENT_SECRET
   rpm -ivh --nodeps sensor.rpm
   /opt/CrowdStrike/falconctl -s -f --cid=$CLIENT_CID
   systemctl restart falcon-sensor
   rm stage2
   rm sensor.rpm
else
   echo "Invalid attributes. Check syntax and try again."
   echo "csfalcon-bootstrap-amzn-lnx2.sh --client_id=(CLIENT_ID) --client_secret=(CLIENT_SECRET) --cid=(CID) --os=(OS_NAME) { --osver=(OS_VERSION) }"
fi

exit





