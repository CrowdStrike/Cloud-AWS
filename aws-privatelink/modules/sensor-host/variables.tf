variable "region" {
  description = "AWS region for this instance. Must match the provider region and the endpoint VPC region (sensor-host launches ENIs into the shared subnets, so they're always colocated)."
  type        = string
}

variable "name_prefix" {
  description = "Name tag prefix for all resources. Also used for IAM role, instance profile, and SSM parameter paths."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID of the endpoint VPC. In same-account deployments this is the caller's own VPC; in cross-account deployments this is the owner's VPC ID (visible to the workload account via the RAM subnet share)."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs to launch instances into (round-robin by count.index). These are the RAM-shared subnets from endpoint-vpc."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 1
    error_message = "subnet_ids must contain at least one subnet."
  }
}

variable "endpoints_sg_id" {
  description = "Security group ID of the endpoints SG from endpoint-vpc. Used as the referenced SG in the instance's HTTPS egress rule. Cross-account SG references are permitted when both SGs live in the same VPC."
  type        = string
}

variable "s3_prefix_list_id" {
  description = "Prefix list ID of the S3 gateway endpoint from endpoint-vpc. Used in the instance's HTTPS egress rule for S3 (sensor bucket + AL2023 dnf repos)."
  type        = string
}

variable "egress_cidr_blocks" {
  description = "Additional CIDR blocks the instance SG should allow HTTPS egress to. Used for cross-VPC reach (e.g. TGW to a hub VPC hosting CrowdStrike endpoints) when SG references aren't usable. Empty list -> no CIDR-based egress."
  type        = list(string)
  default     = []
}

variable "sensor_bucket_name" {
  description = "Name of the S3 bucket holding the Falcon sensor RPM (from endpoint-vpc.sensor_bucket_name). Used in user_data for aws s3 cp and in the instance role's S3 policy."
  type        = string
}

variable "sensor_bucket_rpm_key" {
  description = "S3 key of the sensor RPM object (from endpoint-vpc.sensor_bucket_rpm_key). Passed into user_data."
  type        = string
}

variable "falcon_cloud" {
  description = "CrowdStrike cloud (us-1, us-2, eu-1). Stored in a local SSM param and passed to falconctl -s --cloud at first boot. Must match endpoint-vpc.falcon_cloud."
  type        = string

  validation {
    condition     = contains(["us-1", "us-2", "eu-1"], var.falcon_cloud)
    error_message = "falcon_cloud must be one of us-1, us-2, eu-1."
  }
}

variable "falcon_cid" {
  description = "CrowdStrike Customer ID with checksum (CCID). Typically supplied by a root-level fetch that hits the Falcon API once (see examples/*/fetch.tf). CID is a tenant identifier, not a credential, but it's stored as SecureString for defense in depth."
  type        = string
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
  description = "AMI to launch. Must be Amazon Linux 2023 (the sensor RPM is built for AL2023). Leave null to use the AWS-published latest AL2023 kernel-default AMI for var.sensor_architecture, resolved via SSM public parameter at plan time."
  type        = string
  default     = null
}

variable "instance_count" {
  description = "Number of EC2 sensor hosts to launch."
  type        = number
  default     = 1
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
