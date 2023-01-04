#!/bin/bash
#
# Leverages helper scripts to deploy the SSM distributor package.
#
# The boto3, crowdstrike-falconpy and tabulate libraries
# must be available (either installed to your machine or a venv)
#
usage(){
    echo "Usage: create-package.sh [CLIENT-ID] [CLIENT-SECRET] [AWS REGION] [SSM PACKAGE NAME] [S3 BUCKET NAME]"
    exit 1
}
if [ -z "$1" ]
then
  usage
fi
if [ -z "$2" ]
then
  usage
fi
if [ -z "$3" ]
then
  usage
fi
if [ -z "$4" ]
then
  usage
fi
if [ -z "$5" ]
then
  usage
fi
DOWNLOAD_HELPER="https://raw.githubusercontent.com/CrowdStrike/falconpy/main/samples/sensor_download/download_sensor.py"
PACKAGER="https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/main/systems-manager/Packaging-utilities/examples/linux-sensor-binary/packager.py"
curl -o download.py $DOWNLOAD_HELPER
curl -o packager.py $PACKAGER
python3 download.py -k $1 -s $2 -d -o win -n 1 -f CS_WINDOWS/WindowsSensor.exe
python3 download.py -k $1 -s $2 -d -o amzn -n 1 -f CS_AMAZON2_x86_64/falcon-sensor.rpm
python3 packager.py -r $3 -p $4 -b $5
rm CS_WINDOWS/WindowsSensor.exe
rm CS_AMAZON2_x86_64/falcon-sensor.rpm
rm download.py
rm packager.py
rm s3-bucket/* !("README.md")
