#!/usr/bin/env sh

set -e

echo 'Uninstalling Falcon Sensor...'
echo 'Parameters'
while [ "$#" -ne 0 ]; do
  echo "$1"
  shift
done
# Paramters



#Get configs params
echo 'Getting required config params ...'

if [ -z "$SSM_CS_CCID" ]; then
  echo "Missing required param SSM_CS_CCID. Ensure the target instance is running the latest SSM agent version"
  exit 1
fi
CCID="${SSM_CS_CCID}"

INSTALLTOKEN="${SSM_CS_INSTALLTOKEN}"

INSTALLPARAMS="${SSM_CS_INSTALLPARAMS}"

SSM_CS_AUTH_TOKEN="${SSM_CS_AUTH_TOKEN}"

# Error Hanldling
errout () {
    rc=$?
    echo "[ERROR] Falcon Sensor un-installation failed with $rc while executing '$2' on line $1"
    exit "$rc"
}

trap 'errout "${LINENO}" "${BASH_COMMAND}" ' EXIT

#Starting
aid=$(sudo /opt/CrowdStrike/falconctl -g --aid | awk -F\" '{print $2}')
echo "Running uninstall command for agent $aid ... "
sudo dpkg -r falcon-sensor

#Running clean up
echo "Running cleanup... "

# Verification
if ! pgrep falcon-sensor >/dev/null; then
  echo "Successfully finished uninstall..."
else
  echo "Uninstall failed..."
  exit 1
fi

# # Delete AID in Console
# echo "Now deleting the host on Falcon Console"
# aid_delete=$(curl -X POST "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name=hide_host" -H "accept: application/json" -H "authorization: bearer ""$SSM_CS_AUTH_TOKEN" -H "Content-Type: application/json" -d "{ \"action_parameters\": [ { \"name\": \"string\", \"value\": \"string\" } ], \"ids\": [ \"$aid\" ]}")
# echo $aid_delete