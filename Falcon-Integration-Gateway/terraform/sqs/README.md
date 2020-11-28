# FIG - SQS queue deployment
This folder contains the necessary Terraform files to deploy the FIG detections queues to Amazon SQS. 

## Components created
+ SQS primary queue
+ SQS dead-letter queue

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
Terraform variables for this deployment are contained within the file _sqs-variables.tf_ and define different aspects of the deployment. Several of these values must be updated
before you will be able to proceed.

> Please note: The __*region*__ variable is not stored within _sqs-variables.tf_ and instead resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you
proceed.

> Also note: The variable __*sqs_queue_name*__ is stored in a stand-alone file named _sqs-queue-name.tf_. If you wish to change the name of your primary SQS queue, this value will need to be updated to reflect the change. This will impact Lambda connectivity and should be updated in other aspects of the deployment as well. (See [lambda-sqs](lambda-sqs) for more detail.)

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `sqs_dlq_name` - The name of the dead-letter queue. This can be any string.
+ `sqs_dlq_delay` - The message delay for the dead-letter queue.
+ `sqs_dlq_max_size` - Maximum message size for messages handled by the dead-letter queue.
+ `sqs_dlq_message_retention` - Amount of time messages are retained within the dead-letter queue.
+ `sqs_dlq_wait_time` - Wait time before a message becomes visible within the dead-letter queue.
+ `sqs_queue_delay` - The message delay for the primary detections queue.
+ `sqs_queue_max_size` - The maximum message size for alerts received within the primary detections queue.
+ `sqs_queue_message_retention` - The amount of time messages are retained within the primary detections queue before being passed to the dead-letter queue.
+ `sqs_queue_wait_time` - The wait time before a message becomes visible within the primary detections queue.

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
