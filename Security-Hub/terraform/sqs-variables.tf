variable "sqs_dlq_name" {
	type = string
	default = "cs-sechub-int-sqs-queue-dlq"
}
variable "sqs_dlq_delay" {
	type = number
	default = 0
}
variable "sqs_dlq_max_size" {
	type = number
	default = 262144
}
variable "sqs_dlq_message_retention" {
	type = number
	default = 604800
}
variable "sqs_dlq_wait_time" {
	type = number
	default = 0
}
variable "sqs_queue_delay" {
	type = number
	default = 0
}
variable "sqs_queue_max_size" {
	type = number
	default = 262144
}
variable "sqs_queue_message_retention" {
	type = number
	default = 14400
}
variable "sqs_queue_wait_time" {
	type = number
	default = 0
}
