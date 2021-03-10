# Description

Templates for setting up and using AWS Systems Manager to install and uninstall the CrowdStrike Falcon agent in AWS.

We provide a collection of utilities for customers to create a

# Important Information

The solution requires version *2.3.1550.0* or later of the AWS Sytems Manager agent installed on the host.

The customer is required to select from one of two methods of delivering the CrowdStrike agent to the ec2 instance.

a) Create an install package that combines the installation scripts with the CrowdStrike Falcon installer. For
information on how to complete these steps follow the
guide [here](https://github.com/CrowdStrike/Cloud-AWS/blob/systems-manager/systems-manager/Packaging-utilities/examples/linux-sensor-binary/README.md)
.

b) Create an install package that uses installation scripts to download the CrowdStrike Falcon installer during
installation. For information on how to complete these steps follow the
guide [here](https://github.com/CrowdStrike/Cloud-AWS/blob/systems-manager/systems-manager/Packaging-utilities/examples/linux-sensor-download/README.md)

# Folder Structure

### *cloudformation*

Folder containing a CloudFormation template **CrowdStrike-ssm-setup.yaml**.

The solution uses AWS Systems Manager automation documents, package documents, packages and encrypted parameters stored
in the paramater store. For more information follow
the [setup instructions](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/setup/Setup-your-account.md)

### *cloudformation-s3-bucket*

The **s3-bucket** Folder contains all the files that must be uploaded to an S3Bucket for the cloudformation template.
Note: this should be the same s3 bucket used to store the CrowdStrike package.

### *Packaging utilities*

Example files for creating custom install packages with a script to create the package and optionally upload it to an S3
bucket and create or update the package in systems manager.

# Documentation

### *Systems Manager Introduction*

Systems Manager Introduction

[https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/introduction/AWS-Systems-Manager-Intro.md](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/introduction/AWS-Systems-Manager-Intro.md)

### *Overview*
Systems Manager Overview

[https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/overview/Overview.md](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/overview/Overview.md)

### *Setup Instructions*
How to setup your account using the CloudFormation template

[https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/setup/Setup-your-account.md](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/setup/Setup-your-account.md)

### *Using Sytems Manager with CrowdStrike*

[https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/using/Using-Crowdstrike-with-Systems-Manager.md](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/using/Using-Crowdstrike-with-Systems-Manager.md)

