### Required — credentials & identity ########################################

variable "owner_email" {
  description = "OwnerEmail tag value applied to every resource."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.owner_email))
    error_message = "owner_email must be a valid email address (e.g. you@example.com)."
  }
}

variable "falcon_client_id" {
  description = "CrowdStrike Falcon API client ID with Sensor Download: Read scope."
  type        = string
  sensitive   = true
}

variable "falcon_client_secret" {
  description = "CrowdStrike Falcon API client secret."
  type        = string
  sensitive   = true
}

variable "falcon_cloud" {
  description = "CrowdStrike Falcon cloud (us-1, us-2, or eu-1)."
  type        = string

  validation {
    condition     = contains(["us-1", "us-2", "eu-1"], var.falcon_cloud)
    error_message = "falcon_cloud must be one of us-1, us-2, eu-1."
  }
}

### Optional — deployment configuration #####################################

variable "region" {
  description = "AWS region to deploy into. AZs are auto-derived."
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name used as the resource prefix and tag value."
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type for sensor hosts."
  type        = string
  default     = "t3.small"
}

variable "ami_id" {
  description = "Amazon Linux 2023 AMI ID. Only set if the default becomes unavailable. Must be AL2023."
  type        = string
  default     = null
}
