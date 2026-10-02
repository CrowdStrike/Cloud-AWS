resource "aws_lambda_function" "interceptor" {
  function_name = var.function_name
  role          = aws_iam_role.interceptor.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  timeout       = var.lambda_timeout_s
  memory_size   = var.lambda_memory_mb

  dynamic "vpc_config" {
    for_each = length(var.subnet_ids) > 0 ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.security_group_ids
    }
  }

  environment {
    variables = merge(
      {
        AIDR_API_ENDPOINT        = var.aidr_api_endpoint
        AIDR_API_TOKEN_SECRET_ARN = aws_secretsmanager_secret.aidr_token.arn
        AIDR_STATE_TABLE         = aws_dynamodb_table.state.name
        AIDR_FAIL_OPEN           = tostring(var.fail_open)
        AIDR_TIMEOUT_S           = var.aidr_timeout_s
      },
      var.llm_provider != "" ? { AIDR_LLM_PROVIDER = var.llm_provider } : {},
      var.app_id != "" ? { AIDR_APP_ID = var.app_id } : {},
      var.collector_instance_id != "" ? { AIDR_COLLECTOR_INSTANCE_ID = var.collector_instance_id } : {},
    )
  }

  tags = var.tags

  depends_on = [aws_iam_role_policy_attachment.basic_execution]

  lifecycle {
    precondition {
      condition     = var.image_uri != null
      error_message = "image_uri is required to create the Lambda function. Run 'terraform apply -target=aws_ecr_repository.interceptor' first, push the image, then set image_uri in terraform.tfvars and run 'terraform apply'."
    }
  }
}
