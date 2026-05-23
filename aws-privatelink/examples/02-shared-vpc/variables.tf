variable "owner_profile" {
  description = "AWS CLI profile for the owner account (hosts the VPC + endpoints + RAM share). Typical shape: an SSO / Identity Center profile like \"my-sso-owner\"."
  type        = string
}

variable "workload_profile" {
  description = "AWS CLI profile for the workload account (launches EC2 into the shared subnets)."
  type        = string
}

variable "workload_account_id" {
  description = "12-digit account ID of the workload account. Used as the RAM share principal."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.workload_account_id))
    error_message = "workload_account_id must be a 12-digit AWS account ID."
  }
}

variable "region" {
  description = "AWS region. Both provider aliases use this region — the whole stack is single-region."
  type        = string
  default     = "us-east-2"
}

variable "availability_zones" {
  description = "Two AZs in var.region. One private subnet (and one endpoint ENI) is placed per AZ."
  type        = list(string)
  default     = ["us-east-2a", "us-east-2b"]
}

variable "vpc_cidr" {
  description = "VPC CIDR for the owner-side endpoint VPC. Workload ENIs launch directly into the shared subnets, so this also covers workload host IPs."
  type        = string
  default     = "10.60.0.0/16"
}

variable "subnet_cidrs" {
  description = "Private subnet CIDRs, one per AZ in availability_zones (order-aligned)."
  type        = list(string)
  default     = ["10.60.1.0/24", "10.60.2.0/24"]
}

variable "name_prefix" {
  description = "Base name prefix. Combined with var.environment to produce the effective prefix applied to all resources."
  type        = string
  default     = "cs-privatelink-shared"
}

variable "environment" {
  description = "Environment tag value applied to every resource."
  type        = string
  default     = "demo"
}

variable "owner_email" {
  description = "OwnerEmail tag value applied to every resource. Required — every deployment is tied to an accountable owner."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.owner_email))
    error_message = "owner_email must be a valid email address (e.g. you@example.com)."
  }
}

variable "falcon_client_id" {
  description = "CrowdStrike Falcon API client ID with Sensor Download: Read scope. Export as TF_VAR_falcon_client_id."
  type        = string
  sensitive   = true
}

variable "falcon_client_secret" {
  description = "CrowdStrike Falcon API client secret. Export as TF_VAR_falcon_client_secret."
  type        = string
  sensitive   = true
}

variable "falcon_cloud" {
  description = "CrowdStrike Falcon cloud (us-1, us-2, or eu-1)."
  type        = string
  default     = "us-2"
}
