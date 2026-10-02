resource "aws_secretsmanager_secret" "aidr_token" {
  name        = "aidr/interceptor/api-token"
  description = "CrowdStrike AIDR bearer token for the AgentCore interceptor Lambda."
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "aidr_token" {
  secret_id     = aws_secretsmanager_secret.aidr_token.id
  secret_string = var.aidr_api_token
}
