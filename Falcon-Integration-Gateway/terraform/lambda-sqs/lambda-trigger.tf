#THIS VERSION ONLY WORKS FOR STAND-ALONE SQS / LAMBDA / SQS-LAMBDA DEPLOYMENTS
#If you want to deploy all functionality at the same time, please use the 
#files contained within the "full" folder as this version will fail due to the
#SQS and Lambda functions not yet existing.
data "aws_sqs_queue" "fig_sqs_queue" {
	name = var.sqs_queue_name
}

data "aws_lambda_function" "fig_lambda" {
	function_name = var.lambda_function_name
}
resource "aws_lambda_event_source_mapping" "event_source_mapping" {
  event_source_arn = data.aws_sqs_queue.fig_sqs_queue.arn
  enabled          = true
  function_name    = data.aws_lambda_function.fig_lambda.arn
  batch_size       = 1
}
