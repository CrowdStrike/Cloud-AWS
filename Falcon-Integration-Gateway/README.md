# Falcon Integration Gateway (FIG) v.2.0.x
The Falcon Integration Gateway publishes detections identified by CrowdStrike Falcon for instances
residing within Amazon Web Services (AWS) to AWS Security Hub.

## FIG Architecture and Data Flow
![Falcon Integration Gateway Architecture Diagram)](images/fig-data-flow-architecture.png)

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

### Installing during instance creation
This solution supports execution via a User Data script, which allows for deployment via CloudFormation or Terraform.
> Since User Data scripts execute as the root user, this script should not include references to _sudo_.

#### Example
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
### Running the automated installer

### Manual installation

## Troubleshooting

### Checking service status

### Log files




