#!/bin/bash
# Downloads the specified sensor file from an AWS S3 bucket
# and performs the installation.

# Amazon Linux 2 version
# THIS SCRIPT MUST BE EXECUTED AS ROOT OR VIA SUDO

# Default values to use when not specified as an argument to the script
BUCKET_NAME="DEFAULT BUCKET NAME"
SENSOR_FILE="DEFAULT SENSOR FILE NAME"
CCID="ENTER YOUR CCID HERE"

if type aws >/dev/null 2>&1; then
    for var in $*
    do
        if [[ "$var" == *--bucket=* ]]
        then
            BUCKET_NAME=${var/--bucket=/}
        fi
        if [[ "$var" == *--sensor=* ]]
        then
            SENSOR_FILE=${var/--sensor=/}
        fi
        if [[ "$var" == *--ccid=* ]]
        then
            CCID=${var/--ccid=/}
        fi
    done
    aws s3 cp s3://$BUCKET_NAME/$SENSOR_FILE $SENSOR_FILE
    yum install libnl -y
    rpm -ivh $SENSOR_FILE
    /opt/CrowdStrike/falconctl -s -f --cid="$CCID"
    service falcon-sensor restart
    rm $SENSOR_FILE
else
    echo "AWS command line client not installed, cannot continue."
    echo "Please install the AWS CLI before attempting to use this script."
fi
