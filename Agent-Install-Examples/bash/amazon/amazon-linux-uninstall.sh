#
#  This is free and unencumbered software released into the public domain.
#
#  Anyone is free to copy, modify, publish, use, compile, sell, or
#  distribute this software, either in source code form or as a compiled
#  binary, for any purpose, commercial or non-commercial, and by any
#  means.
#
#  In jurisdictions that recognize copyright laws, the author or authors
#  of this software dedicate any and all copyright interest in the
#  software to the public domain. We make this dedication for the benefit
#  of the public at large and to the detriment of our heirs and
#  successors. We intend this dedication to be an overt act of
#  relinquishment in perpetuity of all present and future rights to this
#  software under copyright law.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#  OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#
#

#!/bin/bash

echo 'Uninstalling Crowdstrike on Amazon Linux...'
echo 'Starting'
REGION=`curl http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
echo $REGION
echo 'Configuring region'
aws configure set region $REGION

# Get API Keys from Parameter Store
echo 'Getting API keys'
APIKEY=$(aws ssm get-parameter --name APIKey --query 'Parameter.Value' --output text)
APISECRET=$(aws ssm get-parameter --name APISecret --query 'Parameter.Value' --output text)

#Get AID and remove local files to cleanup
echo 'Getting the AID for the instance'
aid=$(sudo /opt/CrowdStrike/falconctl -g --aid | awk -F\" '{print $2}')
echo $aid
sudo apt-get purge falcon-sensor

#With AID and API keys, delete host on Crowdstrike console
#Get OAuth2 Token
echo 'Getting OAuth2 Token'
TOKEN=$(curl -X POST "https://api.crowdstrike.com/oauth2/token" -H "accept: application/json" -H "Content-Type: application/x-www-form-urlencoded" -d "client_id"=""$APIKEY"&client_secret"="$APISECRET" | grep access_token| awk -F\" '{print $4}')
echo $TOKEN

# Check to see if AID is present
echo 'Getting the AID and verifying against Falcon console'
aid_status=$(curl -X GET "https://api.crowdstrike.com/devices/entities/devices/v1?ids"="$aid" -H "Accept: application/json" -H "Authorization: Bearer "$TOKEN"")
echo $aid_status

# Will need to add some sort of HTTP status check here

# Delete with AID
echo "Now deleting the host on Falcon Console"
aid_delete=$(curl -X POST "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name=hide_host" -H "accept: application/json" -H "authorization: bearer ""$TOKEN" -H "Content-Type: application/json" -d "{ \"action_parameters\": [ { \"name\": \"string\", \"value\": \"string\" } ], \"ids\": [ \"$aid\" ]}")
echo $aid_delete

# Will need to add some sort of HTTP status check here
