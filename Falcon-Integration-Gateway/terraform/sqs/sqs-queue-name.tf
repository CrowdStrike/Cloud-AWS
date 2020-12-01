#This is the name of the SQS queue used for the deployment
variable "sqs_queue_name" {
        type = string
        default = "fig-example-sqs-queue-name"
}
