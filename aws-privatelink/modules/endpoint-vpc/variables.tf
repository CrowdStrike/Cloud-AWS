variable "region" {
  description = "AWS region for this VPC. Must match the provider region."
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
  description = "Private subnet CIDRs, one per AZ in var.availability_zones (order-aligned). Hosts the interface endpoint ENIs and any consumer workloads launched into the RAM-shared subnets."
  type        = list(string)

  validation {
    condition     = length(var.subnet_cidrs) >= 2
    error_message = "subnet_cidrs must contain at least two CIDRs."
  }
}

variable "name_prefix" {
  description = "Name tag prefix for all resources. Also used for the sensor bucket and PHZ tags."
  type        = string
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

variable "sensor_rpm_path" {
  description = "Local path to the Falcon sensor RPM. Uploaded to the sensor bucket as a single object; consumer accounts pull it via the S3 gateway endpoint on first boot."
  type        = string
}

variable "ram_principals" {
  description = "AWS account IDs (or OU ARNs) to share the private subnets with via AWS RAM. Empty list disables the RAM share (single-account mode)."
  type        = list(string)
  default     = []
}

variable "consumer_sg_ids" {
  description = "Map of logical name -> security group ID for consumer SGs that need HTTPS ingress into the endpoints SG. Keys must be plan-time known (literals); values can be apply-time computed. Typically fed from sensor-host.instance_sg_id in the caller. Only works when the consumer SG lives in the same VPC (same-account or RAM-shared subnets). For cross-VPC reach (TGW), use consumer_cidr_blocks instead."
  type        = map(string)
  default     = {}
}

variable "consumer_cidr_blocks" {
  description = "CIDR blocks that need HTTPS ingress to the endpoints SG. Used when consumers live in a different VPC reachable over TGW/peering (SG references don't cross VPCs). One ingress rule is created per CIDR. Empty list -> no CIDR-based ingress."
  type        = list(string)
  default     = []
}

variable "authorized_role_arns" {
  description = "IAM role ARNs (from consumer accounts) that should be granted s3:GetObject on the RPM in the sensor bucket. Empty list -> no cross-account bucket policy statement. For org-wide access, set an empty list here and attach your own policy with aws:PrincipalOrgID outside the module."
  type        = list(string)
  default     = []
}
