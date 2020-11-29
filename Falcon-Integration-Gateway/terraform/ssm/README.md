# FIG - Parameter Store deployment
This folder contains the necessary Terraform files to deploy FIG parameters to Parameter Store within AWS. 

## Components created
+ Parameter Store parameters


## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
Terraform variables for this deployment are contained within the file _ssm-variables.tf_ and define different aspects of the deployment. Several of these values must be updated
before you will be able to proceed.

> Please note: The __*region*__ variable is not stored within _ssm-variables.tf_ and instead resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you
proceed.

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.
+ `falcon_client_id` - **DO NOT** store this value within _ssm-variables.tf_. Instead pass it during execution on the command line as shown below.
+ `falcon_client_secret` - **DO NOT** store this value within _ssm-variables.tf_. Instead pass it during execution on the command line as shown below.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `fig_app_id` - The string used for an application identifier when communicating with the CrowdStrike Falcon API.
+ `fig_severity_threshold` - The integer value to use as a threshold for alerts considered worthy of notification.
+ `fig_sqs_queue_name` - The name of the SQS queue to send detections to.
> If you have updated the name of the SQS queue to reflect a different value, you must update this variable to match or your deployment will not function properly.

## Confirming the deployment
Before deploying, confirm you've set the appropriate variable values by executing the following command.
```bash
$ terraform plan
```

## Executing the deployment
You may deploy the infrastructure defined within this folder by issuing the following command.
```bash
$ terraform apply --var falcon_client_id "ID_GOES_HERE" --var falcon_client_secret "SECRET_GOES_HERE"
```
