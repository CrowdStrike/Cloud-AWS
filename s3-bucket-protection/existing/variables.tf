variable "bucket_name" {
    description = "The name of the bucket that is created"
    type = string
    default = ""
}
variable "lambda_execution_role_name" {
    description = "The name of the lambda execution IAM role"
    type = string
    default = "s3-protected-bucket-role"
}
variable "falconpy_layer_filename" {
    description = "The name of the archive to use for the lambda layer"
    type = string
    default = "falconpy-layer.zip"
}
variable "falconpy_layer_name" {
    description = "The name used for the lambda layer"
    type = string
    default = "crowdstrike_falconpy"
}
variable "lambda_function_filename" {
    description = "The name of the archive to use for the lambda function"
    type = string
    default = "s3-bucket-protection.zip"
}
variable "lambda_function_name" {
    description = "The name used for the lambda function"
    type = string
    default = "s3_bucket_protection"
}
variable "lambda_mitigate_threats" {
    description = "Remove malicious files from the bucket as they are discovered."
    type = string
    default = "TRUE"
}
variable "ssm_param_client_id" {
    description = "Name of the SSM parameter storing the API client ID"
    type = string
    default = "S3_FALCONX_SCAN_CLIENT_ID"
}
variable "ssm_param_client_secret" {
    description = "Name of the SSM parameter storing the API client secret"
    type = string
    default = "S3_FALCONX_SCAN_CLIENT_SECRET"
}
variable "falcon_client_id" {
    description = "The CrowdStrike Falcon API client ID"
    type = string
    default = ""
    sensitive = true
}
variable "falcon_client_secret" {
    description = "The CrowdStrike Falcon API client secret"
    type = string
    default = ""
    sensitive = true
}
variable "lambda_description" {
    description = "The description used for the lambda function"
    type = string
    default = "CrowdStrike S3 bucket protection"
}
variable "iam_prefix" { 
    description = "The prefix used for resources created within IAM"
	type = string
	default = "s3-bucket-protection"
}
variable "base_url" {
    description = "The Base URL for the CrowdStrike Cloud API"
    type = string
    default = "https://api.crowdstrike.com"
}
data "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name
}