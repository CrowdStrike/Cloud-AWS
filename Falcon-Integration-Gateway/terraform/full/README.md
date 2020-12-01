# FIG - Full deployment
This folder contains the necessary Terraform files to deploy the entire FIG solution to your environment within AWS. 

## Components created
+ t2.micro instance running Amazon Linux 2 
    + Python 3 is installed
    + Boto3 and requests packages are installed
    + FIG service is deployed and started
+ Parameter Store parameters
+ SQS primary queue
+ SQS dead-letter queue
+ Lambda function 
+ IAM execution role and policies
+ IAM instance role and policy
+ Lambda SQS trigger

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
The __*region*__ variable resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you proceed.

The variable __*lambda_function_name*__ is stored in a stand-alone file named _lambda-function-name.tf_. To change the name of your Lambda function, this value will need to be updated to reflect the change. 

The variable __*sqs_queue_name*__ is stored in a stand-alone file named _sqs-queue-name.tf_. To change the name of your primary SQS queue, this value will need to be updated to reflect the change. 

- EC2 variables can be found in the file _ec2-variables.tf_. 
- Lambda variables are contained in the file _lambda-variables.tf_.
- SQS variables reside in the file _sqs-variables.tf_. 
- SSM (Parameter Store) variables are located within _ssm-variables.tf_.

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.
+ `ami_id` - The AMI ID for the most recent Amazon Linux 2 build. This ID is specific to your region and can be retrieved from the AWS console.
+ `key_name` - The name of the SSH key pair used to secure the instance. You must have access to this key in order to connect to your FIG instance remotely.
+ `vpc_security_groups` - A _list_ of security groups to attach to the instance deployed. If no external security permissions are required, set this value
to reflect the ID of the default security group for the VPC.
+ `subnet_id` - The ID of the subnet to deploy this instance to. This value will control which VPC your instance is deployed to as well.
+ `falcon_client_id` - **DO NOT** store this value within _ssm-variables.tf_. Instead pass it during execution on the command line as shown below.
+ `falcon_client_secret` - **DO NOT** store this value within _ssm-variables.tf_. Instead pass it during execution on the command line as shown below.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `instance_name` - The string value to use as a name for this instance within the AWS console.
+ `instance_type` - The type and size of instance to use for this deployment. Defaults to t2.micro.
+ `iam_role_name` - The string value to use as the name for the IAM role assigned to the instance.
+ `iam_policy_name` - The string value to use as the name for the policy attached to the instance IAM role.
+ `lambda_filename` - This variable points to the ZIP file containing the lambda source code. By default it refers to the archive maintained within this repository.
If you wish to use a different version of the lambda function, you should update this value to reflect the appropriate ZIP archive.
+ `lambda_function_name` - The string value used for the name of the lambda function.
+ `sqs_dlq_name` - The name of the dead-letter queue. This can be any string.
+ `sqs_dlq_delay` - The message delay for the dead-letter queue.
+ `sqs_dlq_max_size` - Maximum message size for messages handled by the dead-letter queue.
+ `sqs_dlq_message_retention` - Amount of time messages are retained within the dead-letter queue.
+ `sqs_dlq_wait_time` - Wait time before a message becomes visible within the dead-letter queue.
+ `sqs_queue_name` - The string to use for the name of the primary detections SQS queue.
+ `sqs_queue_delay` - The message delay for the primary detections queue.
+ `sqs_queue_max_size` - The maximum message size for alerts received within the primary detections queue.
+ `sqs_queue_message_retention` - The amount of time messages are retained within the primary detections queue before being passed to the dead-letter queue.
+ `sqs_queue_wait_time` - The wait time before a message becomes visible within the primary detections queue.
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
