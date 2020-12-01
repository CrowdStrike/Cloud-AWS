#This is the name of the Dead-Letter queue used for the deployment
variable "sqs_dlq_name" {
	type = string
	default = "fig-testing-sqs-queue-dlq"
}
#DLQ message delay
variable "sqs_dlq_delay" {
	type = number
	default = 0
}
#DLQ maximum message size
variable "sqs_dlq_max_size" {
	type = number
	default = 262144
}
#DLQ message retention (in seconds)
variable "sqs_dlq_message_retention" {
	type = number
	default = 604800
}
#DLQ message delivery wait time
variable "sqs_dlq_wait_time" {
	type = number
	default = 0
}
#Main queue message delay
variable "sqs_queue_delay" {
	type = number
	default = 0
}
#Main queue maximum message size
variable "sqs_queue_max_size" {
	type = number
	default = 262144
}
#Main queueu message retention (in seconds)
variable "sqs_queue_message_retention" {
	type = number
	default = 14400
}
#Main queue message delivery wait time
variable "sqs_queue_wait_time" {
	type = number
	default = 0
}
