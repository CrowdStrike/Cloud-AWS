# Background

An example of an autoscale group consisting and Amazon Linux 2 instances.

We use user-data scripts to install the sensor during initialisation and autoscale Lifecycle hooks to remove the instance from the Falcon Console when it is terminated. 

# Instructions 

1. Create s3 bucket 

2. Upload lambda files contained in the lambda directory to the bucket

    The lambda files required are 

    * manage_instance.zip 
    * layer.zip

3. Upload the relevant Agent install file for Amazon AMI to the same bucket

4. Create API keys in falcon console for managing hosts

5. Complete the CFT

## Overview
* Template will deploy an ASG with a host count of one.   An example install script using "user-data" is included. 
* The install script will pull the install file from the s3 bucket.
* API keys are stored in Env variables in lambda but should be stored in SSM parameter store for production
* Lambda Instance lifecycle hooks are used to remove the host from the falcon console when it is terminated.

## Key Points for Consideration
CFT - UserData
```
UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          INSTALLPARAMS="--tags=\"autoscale_test\""
          echo 'Starting'
          REGION=`curl http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
          echo $REGION
          echo 'Configuring region'
          aws configure set region $REGION
          aws s3 cp s3://${FalconInstallerBucket}/${FalconFileName} ./
          yum install ${FalconFileName} -y
          eval /opt/CrowdStrike/falconctl -s --cid="${CCID}"
          #Starting Falcon sensor
          if [[ -L "/sbin/init" ]]
          then
              systemctl start falcon-sensor
          else
              sudo service falcon-sensor start
          fi
          cd /var/tmp

          # Verification
          if [[ -n $(ps -e | grep falcon-sensor) ]]
          then
            echo "Successfully finished installation..."
          else
            echo "Installation failed..."
            exit 1
          fi
```
The CrowdStrike customer ID is passed from the input parameters, this could be stored in the the ssm parameter store if required.
```
 eval /opt/CrowdStrike/falconctl -s --cid="${CCID}"
```
The location and name of the install file is passed from the input parameters.
```
 aws s3 cp s3://${FalconInstallerBucket}/${FalconFileName} ./
```

Lambda Function
For simplicity the CrowdStrike API keys are stored in Environment variables. 
```
client_id = os.environ['Falcon_ClientID']
client_secret = os.environ['Falcon_Secret']
```
Code is included that would allow the lambda function to fetch the values from the ssm parameter store if required
