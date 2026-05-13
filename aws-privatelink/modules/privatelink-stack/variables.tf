variable "region" {
  description = "AWS region for this stack. Must match the provider region."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "availability_zones" {
  description = "AZs to spread private subnets across. One interface endpoint ENI is placed per subnet, so two AZs is the minimum for HA."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "availability_zones must contain at least two AZs so interface endpoints get an ENI in more than one AZ."
  }
}

variable "subnet_cidrs" {
  description = "Private subnet CIDRs, one per AZ in var.availability_zones (order-aligned). Hosts the EC2 + interface endpoint ENIs."
  type        = list(string)

  validation {
    condition     = length(var.subnet_cidrs) >= 2
    error_message = "subnet_cidrs must contain at least two CIDRs."
  }
}

variable "name_prefix" {
  description = "Name tag prefix for all resources. Also used for IAM role, instance profile, sensor bucket, and SSM parameter paths."
  type        = string
}

variable "key_name" {
  description = "Optional EC2 key pair for SSH. Leave null for SSM-only access (recommended)."
  type        = string
  default     = null
}

variable "ssh_allowed_cidr" {
  description = "Optional source CIDR for SSH (port 22). Only used when key_name is also set. Traffic must arrive via VPN/TGW/peering — this module does not create one."
  type        = string
  default     = null
}

variable "instance_type" {
  description = "EC2 instance type. Must match var.sensor_architecture (e.g. t3.small for x86_64, t4g.small for aarch64/Graviton)."
  type        = string
  default     = "t3.small"
}

variable "sensor_architecture" {
  description = "CPU architecture for the Falcon sensor RPM and the AL2023 AMI. Must match the family of var.instance_type."
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "aarch64"], var.sensor_architecture)
    error_message = "sensor_architecture must be either \"x86_64\" or \"aarch64\"."
  }
}

variable "ami_id" {
  description = "AMI to launch. Must be an Amazon Linux 2023 image (the sensor RPM the module downloads is built for AL2023 — any other OS will fail on `dnf install`). Leave null (default) to use the AWS-published latest AL2023 kernel-default AMI for var.sensor_architecture, resolved via the SSM public parameter /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-<arch>. Set to pin a specific AMI ID or to bring your own hardened AL2023 image."
  type        = string
  default     = null
}

variable "instance_count" {
  description = "Number of EC2 sensor hosts to launch."
  type        = number
  default     = 1
}

variable "sensor_bucket_name" {
  description = "Optional existing S3 bucket to reuse instead of creating one. The sensor RPM will be uploaded to this bucket."
  type        = string
  default     = null
}

variable "falcon_cloud" {
  description = "CrowdStrike Falcon cloud (us-1, us-2, or eu-1). Determines the endpoint service IDs, home region, and PHZ hostnames."
  type        = string
  default     = "us-2"

  validation {
    condition     = contains(["us-1", "us-2", "eu-1"], var.falcon_cloud)
    error_message = "falcon_cloud must be one of us-1, us-2, eu-1."
  }
}

variable "falcon_cid" {
  description = "CrowdStrike Customer ID with checksum (CCID). The caller is expected to supply this — typically from a root-level fetch that hits the Falcon API once per deployment (see examples/*/fetch.tf). CID is a tenant identifier, not a credential."
  type        = string
}

variable "sensor_rpm_path" {
  description = "Local path to the Falcon sensor RPM. The caller is expected to supply this — typically from a root-level fetch that downloads once per deployment (see examples/*/fetch.tf)."
  type        = string
}
