# FIG - Lambda / SQS trigger deployment
This folder contains the necessary Terraform files to deploy the SQS trigger to the FIG detections handler Lambda function within AWS. 

## Components created
+ Lambda SQS trigger

> In order to properly deploy this trigger, the [Lambda function](terraform/lambda) and the [SQS queues](terraform/sqs) must already exist. This means
the trigger deployment must be executed _after_ the Lambda and SQS deployments.

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
The __*region*__ variable resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you proceed.

The variable __*lambda_function_name*__ is stored in a stand-alone file named _lambda-function-name.tf_. If you have changed the name of your Lambda function, this value will need to be updated to reflect the change. 

The variable __*sqs_queue_name*__ is stored in a stand-alone file named _sqs-queue-name.tf_. If you have changed the name of your primary SQS queue, this value will need to be updated to reflect the change. 

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `lambda_function_name` - The string value used for the name of the lambda function.
+ `sqs_queue_name` - The string to use for the name of the primary detections SQS queue.

## Confirming the deployment
Before deploying, confirm you've set the appropriate variable values by executing the following command.
```bash
$ terraform plan
```

## Executing the deployment
You may deploy the infrastructure defined within this folder by issuing the following command.
```bash
$ terraform apply
```
