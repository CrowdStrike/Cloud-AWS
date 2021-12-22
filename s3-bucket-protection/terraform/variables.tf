variable "unique_id" {
    description = "A unique identifier that is prepended to all created resource names"
    type = string
    default = "s3example"
}
variable "bucket_name" {
    description = "The name of the bucket that is created"
    type = string
    default = "s3-protected-bucket"
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
    default = "quickscan-bucket.zip"
}
variable "lambda_function_name" {
    description = "The name used for the lambda function"
    type = string
    default = "s3_bucket_protection"
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
variable "cidr_vpc" {
    description = "CIDR block for the VPC"
    default     = "10.99.0.0/16"
}
variable "cidr_subnet" {
    description = "CIDR block for the subnet"
    default     = "10.99.10.0/24"
}
variable "environment_tag" {
    description = "Environment tag"
    type        = string
    default     = "S3 Bucket Protection"
}
variable "trusted_ip" {
    description = "Trusted IP address to access the test bastion"
    type        = string
    default     = "1.1.1.1/32"
}
variable "ssh_group_name" {
    description = "Name of the security group allowing inbound SSH from the Trusted IP"
    type        = string
    default     = "S3-BUCKET-PROTECTION-TRUSTED-ADMIN"
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
variable "instance_name" {
    description = "The name of the EC2 instance that is created to demo functionality"
    type = string
    default = "CS-S3-BUCKET-PROTECTION-TEST"
}
variable "instance_key_name" {
    description = "The name of the SSH PEM key that will be used for authentication to the EC2 instance"
    type = string
    default = ""
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
variable "instance_type" {
    description = "The type.size of the EC2 instance that is created"
	type = string
	default = "t2.small"
}
