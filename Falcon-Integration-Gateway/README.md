# Falcon Integration Gateway (FIG) v.2.0.x
The Falcon Integration Gateway publishes detections identified by CrowdStrike Falcon for instances
residing within Amazon Web Services (AWS) to AWS Security Hub.

## Table of Contents
+ [Architecture and Data Flow](##fig-architecture-and-data-flow)
+ [Installation](##installation)
    - [Installing the SQS queue](###installing-the-fig-detections-sqs-queue)
    - [Installing the findings publishing lambda](###installing-the-fig-publishing-lambda-handler)
    - [Installing the service application](###installing-the-fig-service-application)
+ [Troubleshooting](##troubleshooting)

## FIG Architecture and Data Flow
![Falcon Integration Gateway Architecture Diagram)](images/fig-data-flow-architecture.png)

---

## Installation
The Falcon Integration Gateway is intended to be deployed as a service on a Linux instance. 
The solution can be run stand-alone, but is not recommended for production deployments.
> When executed within a Mac OS or Windows environment, FIG will assume it is running in stand-alone mode.

### Pre-requisites
+ Falcon Complete 
+ Falcon Discover
+ API keys for your Falcon environment
+ An AWS environment with the following:
    + Available VPC with properly defined subnets
    + An available private subnet within this VPC
    + A NAT gateway attached to this VPC and set as the default route for the selected private subnet
+ Permissions to perform the following actions within AWS:
    + Create EC2 instance
        + Amazon Linux 2
            - Python 3
            - Boto3 client
            - Requests client
    + Create Lambda function
    + Create SQS queue
    + Create IAM role
    + Create SSM parameters
+ If you are not using SSM parameters to store application settings then you will also need a properly formatted _[config.json](#configjson)_ file.

### Installing the FIG detections SQS queue

#### Creating the Dead-letter queue (DLQ)

#### Creating the main queue

### Installing the FIG publishing lambda handler

#### Lambda function settings

#### Uploading the source code

#### Creating the SQS trigger

### Installing the FIG service application

#### Installing the FIG service during instance creation
This solution supports execution via a User Data script, which allows for deployment via CloudFormation or Terraform.
> Since User Data scripts execute as the root user, this script should not include references to _sudo_.

##### Example
```bash
#!/bin/bash
# version 3.0
# This is the userdata script for newly created EC2 instances. 
# This script should not be executed manually
cd /var/tmp
wget -O fig-2.0.10-install.run https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Falcon-Integration-Gateway/install/fig-2.0.10-install.run
chmod 755 fig-2.0.10-install.run
./fig-2.0.10-install.run --target /usr/share/fig
```
#### Running the FIG automated service installer

#### Manual installation of the FIG servoce

### Configuration

#### Parameters
The Falcon Integration Gateway requires six parameters be defined in order to successfully operate.
+ `falcon_client_id` - The API client ID for the API key used to access your Falcon environment.
+ `falcon_client_secret` - The API client secret for the API key used to access your Falcon environment.
+ `app_id` - A unique string value that describes the name of the application you are connecting to Falcon. Most string values are supported.
+ `severity_threshold` - An integer representing the threshold for detections you want published to AWS Security Hub.
+ `region` - The region we will be publishing to in AWS Security Hub. This will need to match the region the SQS queue resides in.

> Even though detections are published to AWS Security Hub within a single AWS region, they represent detections for instances found within _all_ AWS regions.

##### SSM
![FIG SSM Parameter Store](images/fig-ssm-parameter-store.png)
##### config.json
These values can also be specified to the application within a _config.json_ file. This file **must** reside within the same directory the FIG application is installed.
```json
{
    "falcon_client_id":"FALCON_CLIENT_ID_GOES_HERE",
    "falcon_client_secret":"FALCON_CLIENT_SECRET_GOES_HERE",
    "app_id":"FIG_APP_ID",
    "severity_threshold":3,
    "sqs_queue_name":"SQS_QUEUE_NAME_SAME_REGION_AS_BELOW",
    "region":"REGION_GOES_HERE"
}
```

---

## Troubleshooting

### Checking service status

### Log files




