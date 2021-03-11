#!/usr/bin/env bash
###################################
#
#
# Installs CrowdStrike Falcon
#
#
##################################

#Starting
echo 'Installing Falcon Sensor...'

echo "Parameters"
while (( "$#" )); do
  echo "$1"
  shift
done

# Paramters
INSTALLER="falcon-sensor-6.16.0-11308.amzn2.x86_64.rpm"
#Get configs params
echo 'Getting required config params ...'

if [[ -z "$SSM_CS_CCID" ]]; then
  echo "Missing required param SSM_CS_CCID. Ensure the target instance is running the latest SSM agent version"
  exit 1
fi
CCID="${SSM_CS_CCID}"

INSTALLTOKEN="${SSM_CS_INSTALLTOKEN}"

INSTALLPARAMS="${SSM_CS_INSTALLPARAMS}"

SSM_CS_AUTH_TOKEN="${SSM_CS_AUTH_TOKEN}"

echo "Running install command ..."
sudo yum install $INSTALLER -y

if [ -n "$INSTALLTOKEN" ] && [ "$INSTALLTOKEN" != "" ]; then
       echo "Passing installation token..."
       TAG=" --provisioning-token="
       INSTALLPARAMS=$INSTALLPARAMS$TAG$INSTALLTOKEN
fi

#Configuring Falconsensor
eval /opt/CrowdStrike/falconctl -s --cid="$CCID" "$INSTALLPARAMS"

#Starting Falcon sensor
if [[ -L "/sbin/init" ]]
then
    systemctl start falcon-sensor
else
    sudo service falcon-sensor start
fi

# Adding sleep before verification
sleep 5s

# Verification
if [[ -n $(ps -e | grep falcon-sensor) ]]
then
  echo "Successfully finished installation..."
else
  echo "Installation failed..."
  exit 1
fi