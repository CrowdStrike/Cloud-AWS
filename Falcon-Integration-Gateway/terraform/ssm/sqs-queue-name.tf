#This is the name of the SQS queue used for the deployment

# This file exists in this folder due to our setting the 
# SQS queue name as a SSM parameter.

variable "sqs_queue_name" {
        type = string
        default = "fig-example-sqs-queue-name"
}
