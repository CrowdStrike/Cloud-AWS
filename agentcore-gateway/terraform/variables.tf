# ---------------------------------------------------------------------------
# Required
# ---------------------------------------------------------------------------

variable "aws_region" {
  type        = string
  description = "AWS region to deploy into."
}

variable "gateway_id" {
  type        = string
  description = "AgentCore Gateway ID to register the interceptor on."
}

variable "gateway_service_role_arn" {
  type        = string
  description = "IAM role ARN used by the AgentCore Gateway to invoke Lambda functions."
}

variable "aidr_api_endpoint" {
  type        = string
  description = "Base URL of the CrowdStrike AIDR API (e.g. https://api.crowdstrike.com)."
}

variable "aidr_api_token" {
  type        = string
  sensitive   = true
  description = "CrowdStrike AIDR bearer token. Stored in Secrets Manager; never written to state in plaintext."
}

variable "image_uri" {
  type        = string
  default     = null
  nullable    = true
  description = "ECR image URI for the interceptor Lambda (e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com/aidr-agentcore-interceptor:latest). Leave unset on the first apply to create the ECR repository; set after pushing the image for the full apply."
}

# ---------------------------------------------------------------------------
# Optional
# ---------------------------------------------------------------------------

variable "function_name" {
  type        = string
  default     = "aidr-agentcore-interceptor"
  description = "Name of the Lambda function."
}

variable "table_name" {
  type        = string
  default     = "aidr-interceptor-state"
  description = "DynamoDB table name for REQUEST→RESPONSE context correlation."
}

variable "lambda_timeout_s" {
  type        = number
  default     = 10
  description = "Lambda execution timeout in seconds."
}

variable "lambda_memory_mb" {
  type        = number
  default     = 256
  description = "Lambda memory in MB."
}

variable "fail_open" {
  type        = bool
  default     = false
  description = "When true, pass traffic through if AIDR is unreachable instead of returning HTTP 500."
}

variable "llm_provider" {
  type        = string
  default     = ""
  description = "Override provider detection: openai, anthropic, gemini, cohere, bedrock. Leave empty for auto-detect."
}

variable "aidr_timeout_s" {
  type        = string
  default     = "3.0"
  description = "Hard timeout in seconds for the AIDR API call."
}

variable "app_id" {
  type        = string
  default     = ""
  description = "Application identifier forwarded to AIDR for audit logging."
}

variable "collector_instance_id" {
  type        = string
  default     = ""
  description = "Collector instance tag for AIDR telemetry."
}

variable "subnet_ids" {
  type        = list(string)
  default     = []
  description = "VPC subnet IDs for the Lambda function. Required if the AIDR endpoint is not internet-accessible."
}

variable "security_group_ids" {
  type        = list(string)
  default     = []
  description = "VPC security group IDs for the Lambda function."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all created resources."
}
