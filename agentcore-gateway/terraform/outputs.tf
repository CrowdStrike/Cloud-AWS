output "lambda_arn" {
  description = "ARN of the interceptor Lambda function."
  value       = aws_lambda_function.interceptor.arn
}

output "ecr_repository_uri" {
  description = "ECR repository URI. Build and push your image here before running the full apply."
  value       = aws_ecr_repository.interceptor.repository_url
}

output "dynamodb_table_name" {
  description = "DynamoDB state table name."
  value       = aws_dynamodb_table.state.name
}

output "secret_arn" {
  description = "ARN of the Secrets Manager secret holding the AIDR token."
  value       = aws_secretsmanager_secret.aidr_token.arn
}

output "push_command" {
  description = "Docker push command for the interceptor image."
  value       = "docker push ${aws_ecr_repository.interceptor.repository_url}:latest"
}
