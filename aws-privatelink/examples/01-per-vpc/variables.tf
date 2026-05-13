variable "region" {
  description = "Consumer region where the VPC and endpoints are created."
  type        = string
  default     = "us-east-2"
}

variable "availability_zones" {
  description = "Two AZs in the consumer region. One private subnet (and one endpoint ENI) is placed per AZ."
  type        = list(string)
  default     = ["us-east-2a", "us-east-2b"]
}

variable "vpc_cidr" {
  description = "VPC CIDR for the consumer VPC."
  type        = string
  default     = "10.50.0.0/16"
}

variable "subnet_cidrs" {
  description = "Private subnet CIDRs, one per AZ in availability_zones (order-aligned)."
  type        = list(string)
  default     = ["10.50.1.0/24", "10.50.2.0/24"]
}

variable "name_prefix" {
  description = "Base name prefix. Combined with var.environment to produce the effective prefix applied to all resources."
  type        = string
  default     = "cs-privatelink"
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
  description = "CrowdStrike Falcon API client ID with Sensor Download: Read scope. Prefer exporting as TF_VAR_falcon_client_id."
  type        = string
  sensitive   = true
}

variable "falcon_client_secret" {
  description = "CrowdStrike Falcon API client secret. Prefer exporting as TF_VAR_falcon_client_secret."
  type        = string
  sensitive   = true
}

variable "falcon_cloud" {
  description = "CrowdStrike Falcon cloud (us-1, us-2, or eu-1)."
  type        = string
  default     = "us-2"
}
