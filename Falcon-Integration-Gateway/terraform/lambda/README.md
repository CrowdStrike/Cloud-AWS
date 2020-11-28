# FIG - Lambda function deployment
This folder contains the necessary Terraform files to deploy the FIG detections handler as a Lambda function within AWS. 

## Components created
+ Lambda function 
+ IAM execution role and policies

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
Terraform variables for this deployment are contained within the file _lambda-variables.tf_ and define different aspects of the deployment. Several of these values must be updated
before you will be able to proceed.

> Please note: The __*region*__ variable is not stored within _lambda-variables.tf_ and instead resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you
proceed.

> Also note: The variable __*lambda_function_name*__ is stored in a stand-alone file named _lambda-function-name.tf_. If you wish to change the name of your Lambda function, this value will need to be updated to reflect the change. This will impact SQS connectivity and should be updated in other aspects of the deployment as well. (See [lambda-sqs](lambda-sqs) for more detail.)

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `lambda_filename` - This variable points to the ZIP file containing the lambda source code. By default it refers to the archive maintained within this repository.
If you wish to use a different version of the lambda function, you should update this value to reflect the appropriate ZIP archive.
+ `lambda_function_name` - The string value used for the name of the lambda function.

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
