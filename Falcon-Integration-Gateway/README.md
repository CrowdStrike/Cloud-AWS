# Falcon Integration Gateway (FIG) v.2.0.x
The Falcon Integration Gateway publishes detections identified by CrowdStrike Falcon for instances
residing within Amazon Web Services (AWS) to AWS Security Hub.

## Table of Contents
+ [Overview](#overview)
    + [Architecture](#architecture)
    + [Data Flow](#data-flow)
+ [Installation](#installation)
    - [Installing the SQS queue](#installing-the-fig-detections-sqs-queue)
    - [Installing the findings publishing lambda](#installing-the-fig-publishing-lambda-handler)
    - [Installing the service application](#installing-the-fig-service-application)
    - [Configuring the application](#configuring-the-application)
+ [Troubleshooting](#troubleshooting)

## Overview
This solution makes use of small EC2 instances to consume detections published to the CrowdStrike Falcon _event-stream_ API and then publishes detection events that align
to instances that exist within AWS to a pre-existing SQS queue. A lambda function consumes these messages, confirms that the detection matches a valid instance in a valid
AWS region, and then publishes the detection as a new finding in AWS Security Hub.

There are several benefits to this architecture:
+ Reduced compute cost as a large portion of the compute cycles are consumed as on-demand lambda function executions
+ Easily scalable depending upon need
+ Can be deployed quickly

### Architecture 
![Falcon Integration Gateway Architecture Diagram)](images/fig-data-flow-architecture.png)

### Data Flow
1. Falcon Integration Gateway contacts the CrowdStrike Falcon API to request a list of available event streams.
2. A connection is opened to each available event stream. As new events are received within CrowdStrike, these events are published to the event stream, which are then consumed by the Falcon Integration Gateway.
3. Detection events are reviewed, with requests to the CrowdStrike Falcon API being performed to confirm these instances are deployed to AWS.
4. Detection events that meet severity threshold settings and are initially confirmed to exist within AWS are published to a SQS queue.
5. A lambda function is triggered that reviews the detection, and identifies the region the instance is located in. The instance is confirmed by matching the mac address to the address reported in the detection.
6. Confirmed detections that are positively identified as attached to valid instances are then published as a finding to AWS Security Hub.
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

#### Creating the dead-letter queue (DLQ)

#### Creating the main queue

### Installing the FIG publishing lambda handler

#### Lambda IAM role execution permissions
Basic lambda execution permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:{AWS-REGION}:{AWS-ACCOUNT-ID}:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:{AWS-REGION}:{AWS-ACCOUNT-ID}:log-group:/aws/lambda/{AWS-LAMBDA-FUNCTION-NAME}:*"
            ]
        }
    ]
}
```

Security hub related permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "securityhub:BatchUpdateFindings",
                "securityhub:BatchImportFindings"
            ],
            "Resource": [
                "arn:aws:securityhub:{AWS-REGION}:{AWS-ACCOUNT-ID}:hub/default",
                "arn:aws:securityhub:{AWS-REGION}:{AWS-ACCOUNT-ID}:product/*/*"
            ]
        },
        {
            "Action": "securityhub:*",
            "Resource": "arn:aws:securityhub:{AWS-REGION}:{AWS-ACCOUNT-ID}:/findings",
            "Effect": "Allow"
        },
        {
            "Action": "securityhub:*",
            "Resource": "arn:aws:securityhub:{AWS-REGION}:{AWS-ACCOUNT-ID}:hub/default",
            "Effect": "Allow"
        }
    ]
}
```

Additional policy attachments

![Additional lambda execution permission policy requirements](images/fig-lambda-execution-role-additional-policies.png)

#### Lambda function settings
![Runtime settings](images/fig-lambda-runtime-settings.png)

![Basic settings](images/fig-lambda-basic-settings.png)

#### Uploading the source code
![Uploading the source code](images/fig-upload-source-code-zip-file.png)

#### Creating the SQS trigger
![Add trigger](images/fig-add-lambda-trigger-button.png)

![Adding the SQS trigger](images/fig-add-lambda-sqs-trigger.png)

### Installing the FIG service application

#### Creating the FIG instance IAM role
![Instance IAM role permissions](images/fig-instance-role-policies.png)

#### Creating the FIG instance and installing the service application
The FIG service application was developed to run efficiently as a service on a small Linux EC2 instance. 
> This instance can be scaled up as necessary. 

The minimum requirements for this instance are:
+ t2.micro (or better) - 1 vCPU, 2 GB RAM
+ Amazon Linux 2 or CentOS 7
+ Python 3 and PIP3 installed
    - boto3 client library installed via PIP (--user)
    - requests client library installed via PIP (--user)
+ The necessary IAM permissions to access SSM parameters and publish messages to our SQS queue
+ A route to the Internet

##### Installing the FIG service during instance creation
This solution supports execution via a User Data script, which allows for deployment via CloudFormation or Terraform.
> Since User Data scripts execute as the root user, this script should not include references to _sudo_.

###### Example
```bash
#!/bin/bash
# version 3.0
# This is the userdata script for newly created EC2 instances. 
cd /var/tmp
wget -O fig-2.0.latest-install.run https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Falcon-Integration-Gateway/install/fig-2.0.latest-install.run
chmod 755 fig-2.0.latest-install.run
./fig-2.0.latest-install.run --target /usr/share/fig
```
##### Running the FIG automated service installer

##### Manual installation of the FIG service

### Configuring the application
The FIG service application allows for customer configuration via application parameters that can be provided in multiple ways. These parameters control
several aspects of the service application's behavior. This includes; the credentials utilized to access the CrowdStrike Falcon API, the application ID utilized 
to connect to the CrowdStrike Falcon API, the severity threshold used to filter out unwanted detections, the SQS queue to target for alerts being published,
and the AWS Region to report to.

#### Parameters
The Falcon Integration Gateway service application requires six parameters be defined in order to successfully operate.
+ `falcon_client_id` - The API client ID for the API key used to access your Falcon environment.
+ `falcon_client_secret` - The API client secret for the API key used to access your Falcon environment.
+ `app_id` - A unique string value that describes the name of the application you are connecting to Falcon. Most string values are supported.
+ `severity_threshold` - An integer representing the threshold for detections you want published to AWS Security Hub.
+ `sqs_queue_name` - Name of the SQS queue to publish detections to. This must reside in the region specified below.
+ `region` - The region we will be publishing to in AWS Security Hub. This will need to match the region the SQS queue resides in. For deployments leveraging SSM, this parameter does not need to be specified.

> Even though detections are published to AWS Security Hub within a single AWS region, they represent detections for instances found within _all_ AWS regions.

##### Using AWS Systems Manager _Parameter Store_
By default, service application configuration parameters are stored within AWS Systems Manager _Parameter Store_ but can be overridden by using a config.json file. 

SSM Parameter Store parameters are _case-sensitive_ and must reside within the same region as the FIG instance you are configuring. Please note the naming convention of the
parameters displayed below, as the variable names must match exactly.

> For deployments running multiple instances of FIG on the same instance, you _must_ use a config.json file.

###### Parameter Store Example
![FIG SSM Parameter Store](images/fig-ssm-parameter-store.png)

For more detail regarding [creating parameters](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-create-console.html) within the 
AWS Systems Manager Parameter Store, check the [AWS Systems Manager Parameter Store documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

##### config.json
Service application parameter values can also be specified within a _config.json_ file. This file **must** reside within the same directory the FIG application is installed. When present, values stored within a config.json file _take precedence_ over values provided via the AWS Systems Manager Parameter Store.
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




