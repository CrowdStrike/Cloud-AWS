resource "aws_sqs_queue" "sqs_queue_dlq" {
  name                      = var.sqs_dlq_name
  delay_seconds             = var.sqs_dlq_delay
  max_message_size          = var.sqs_dlq_max_size
  message_retention_seconds = var.sqs_dlq_message_retention
  receive_wait_time_seconds = var.sqs_dlq_wait_time
}

resource "aws_sqs_queue" "sqs_queue" {
  name                      = var.sqs_queue_name
  delay_seconds             = var.sqs_queue_delay
  max_message_size          = var.sqs_queue_max_size
  message_retention_seconds = var.sqs_queue_message_retention
  receive_wait_time_seconds = var.sqs_queue_wait_time
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.sqs_queue_dlq.arn
    maxReceiveCount     = 4
  })
  }
}
