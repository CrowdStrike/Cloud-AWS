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


echo -e "\nThis script should be executed from the s3-bucket-protection root directory.\n"
if [ -z "$1" ]
then
   echo "You must specify 'add' or 'remove' to run this script"
   exit 1
fi
MODE=$(echo "$1" | tr [:upper:] [:lower:])
if [[ "$MODE" == "add" ]]
then
	read -sp "CrowdStrike API Client ID: " FID
	echo
	read -sp "CrowdStrike API Client SECRET: " FSECRET
    echo
    read -p "Bucket name: " BUCKET_NAME
    # This demo will be using a custom version of the falconpy layer for now. - jshcodes@CrowdStrike 05.04.2023 #230
    #rm lambda/falconpy-layer.zip >/dev/null 2>&1
    #curl -o lambda/falconpy-layer.zip https://falconpy.io/downloads/falconpy-layer.zip
    if ! [ -f existing/.terraform.lock.hcl ]; then
        terraform -chdir=existing init
    fi
	terraform -chdir=existing apply -compact-warnings --var falcon_client_id=$FID \
		--var falcon_client_secret=$FSECRET --var bucket_name=$BUCKET_NAME --auto-approve
    all_done
	exit 0
fi
if [[ "$MODE" == "remove" ]]
then
    read -p "Bucket name: " BUCKET_NAME
	terraform -chdir=existing destroy -compact-warnings --var bucket_name=$BUCKET_NAME --auto-approve
    rm lambda/s3-bucket-protection.zip
    env_destroyed
	exit 0
fi
echo "Invalid command specified."
exit 1

