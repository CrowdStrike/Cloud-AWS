# Security Hub Integration Deployment - Terraform examples
This folder contains an example for deploying the Security Hub integration solution in an automated fashion by leveraging Terraform.

## Pre-requisites
+ Working AWS API credentials providing you permissions to create:
    - EC2 instances
    - IAM policies and roles
    - Lambda functions
    - SQS queues
    - SSM parameters
+ Terraform v0.11 or greater

## Passing Falcon API keys
This solution creates the necessary Falcon API client ID and secret as Systems Manager Parameter Store parameters. These values can be specified in the file _ssm-variables.tf_ but this is **not** recommended. Instead, pass these values via the command line.

```bash
terraform apply --var falcon_client_id "ID_GOES_HERE" --var falcon_client_secret "SECRET_GOES_HERE"
```