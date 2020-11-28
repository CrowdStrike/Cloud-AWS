# Terraform deployment example
This folder contains an example for deploying the FIG solution via Terraform.
This example is broken down into multiple parts, easing integration into existing
build scripts and allowing for quick customization.

Each folder is encapsulated and can be executed as a stand-alone Terraform deployment,
deploying just the elements described within that folder. The __*[full](full)*__ contains 
a complete deployment, allowing the entire FIG solution to be deployed within 10 minutes
using a single Terraform statement.

## Components
+ `ec2` - FIG [EC2 instance deployment](ec2)
+ `lambda` - FIG [Lambda function deployment](lambda)
+ `lambda-sqs` - FIG [Lambda SQS trigger deployment](lambda-sqs)
+ `sqs` - FIG [SQS queues deployment](sqs)
+ `ssm` - FIG [SSM parameter store deployment](ssm)
+ `full` - FIG [Complete deployment](full)

## Pre-requisites
+ Working AWS API credentials providing you permissions to create:
    - EC2 instances
    - IAM policies and roles
    - Lambda functions
    - SQS queues
    - SSM parameters
+ Terraform v0.11 or greater

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Passing Falcon API keys
FIG communicates directly with the CrowdStrike Falcon API using the API Client ID and Secret you generate. This solution creates these secrets as Systems Manager Parameter Store parameters. Pre-deployment, these values can be specified in the file _ssm-variables.tf_ but this is **not** recommended as this file is not encrypted. 

Instead, pass these values via the command line as follows.

```bash
terraform apply --var falcon_client_id "ID_GOES_HERE" --var falcon_client_secret "SECRET_GOES_HERE"