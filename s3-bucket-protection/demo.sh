#!/bin/bash
DG="\033[1;30m"
RD="\033[0;31m"
NC="\033[0;0m"
LB="\033[1;34m"
all_done(){
    echo -e "$LB"
    echo '  __                        _'
    echo ' /\_\/                   o | |             |'
    echo '|    | _  _  _    _  _     | |          ,  |'
    echo '|    |/ |/ |/ |  / |/ |  | |/ \_|   |  / \_|'
    echo ' \__/   |  |  |_/  |  |_/|_/\_/  \_/|_/ \/ o'
    echo -e "$NC"
}
env_destroyed(){
    echo -e "$RD"
    echo ' ___                              __,'
    echo '(|  \  _  , _|_  ,_        o     /  |           __|_ |'
    echo ' |   ||/ / \_|  /  | |  |  |    |   |  /|/|/|  |/ |  |'
    echo '(\__/ |_/ \/ |_/   |/ \/|_/|/    \_/\_/ | | |_/|_/|_/o'
    echo -e "$NC"
}

# Ensure script is executed from the s3-bucket-protection root directory
[[ -d demo ]] && [[ -d lambda ]] || { echo -e "\nThis script should be executed from the s3-bucket-protection root directory.\n"; exit 1; }

if [ -z "$1" ]
then
   echo "You must specify 'up' or 'down' to run this script"
   exit 1
fi
MODE=$(echo "$1" | tr [:upper:] [:lower:])
if [[ "$MODE" == "up" ]]
then
	read -sp "CrowdStrike API Client ID: " FID
	echo
	read -sp "CrowdStrike API Client SECRET: " FSECRET
	echo -e "\nThe following values are not required for the integration, only the demo."
	read -p "EC2 Instance Key Name: " ECKEY
	read -p "Trusted IP address: " TRUSTED
    UNIQUE=$(echo $RANDOM | md5sum | sed "s/[[:digit:].-]//g" | head -c 8)
    # This demo will be using a custom version of the falconpy layer for now. - jshcodes@CrowdStrike 05.04.2023 #230
    #rm lambda/falconpy-layer.zip >/dev/null 2>&1
    #curl -o lambda/falconpy-layer.zip https://falconpy.io/downloads/falconpy-layer.zip
    if ! [ -f demo/.terraform.lock.hcl ]; then
        terraform -chdir=demo init
    fi
	terraform -chdir=demo apply -compact-warnings --var falcon_client_id=$FID \
		--var falcon_client_secret=$FSECRET --var instance_key_name=$ECKEY \
		--var trusted_ip=$TRUSTED/32 --var unique_id=$UNIQUE --auto-approve
    echo -e "$RD\nPausing for 60 seconds to allow configuration to settle.$NC"
    sleep 60
    all_done
	exit 0
fi
if [[ "$MODE" == "down" ]]
then
	terraform -chdir=demo destroy -compact-warnings --auto-approve
    rm lambda/quickscan-bucket.zip
    env_destroyed
	exit 0
fi
echo "Invalid command specified."
exit 1

