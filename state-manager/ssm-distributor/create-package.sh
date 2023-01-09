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
python download.py -k $1 -s $2 -d -o win -f CS_WINDOWS/WindowsSensor.exe
python download.py -k $1 -s $2 -d -o amzn -v "2" -f CS_AMAZON2_x86_64/falcon-sensor.rpm
python download.py -k $1 -s $2 -d -o amzn -v "2 - arm64" -f CS_AMAZON2_ARM64/falcon-sensor.rpm
python download.py -k $1 -s $2 -d -o ubuntu -f CS_UBUNTU_x86_64/falcon-sensor.deb
python packager.py -r $3 -p $4 -b $5
rm CS_WINDOWS/WindowsSensor.exe
rm CS_AMAZON2_x86_64/falcon-sensor.rpm
rm CS_AMAZON2_ARM64/falcon-sensor.rpm
rm CS_UBUNTU_x86_64/falcon-sensor.deb
rm download.py
rm packager.py
rm s3-bucket/*