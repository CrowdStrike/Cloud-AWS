variable "hub_profile" {
  description = "AWS CLI profile for the hub (networking) account. Hosts the endpoint VPC, TGW, CrowdStrike endpoints, and R53 Profile. Typical shape: an SSO / Identity Center profile like \"my-sso-hub\"."
  type        = string
}

variable "spoke_profile" {
  description = "AWS CLI profile for the spoke (workload) account. Owns a VPC that attaches to the hub's TGW."
  type        = string
}

variable "spoke_account_id" {
  description = "12-digit account ID of the spoke account. Used as the RAM principal for both the TGW share and the R53 Profile share."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.spoke_account_id))
    error_message = "spoke_account_id must be a 12-digit AWS account ID."
  }
}

variable "region" {
  description = "AWS region. Both provider aliases use this region — the whole stack is single-region. R53 Profiles are region-scoped; extend with a second profile per additional region."
  type        = string
  default     = "us-east-2"
}

variable "availability_zones" {
  description = "Two AZs in var.region. One private subnet (and one endpoint ENI) is placed per AZ in both the hub and spoke VPCs."
  type        = list(string)
  default     = ["us-east-2a", "us-east-2b"]
}

variable "hub_vpc_cidr" {
  description = "CIDR for the hub endpoint VPC. Must not overlap with spoke_vpc_cidr (both attach to the same TGW)."
  type        = string
  default     = "10.70.0.0/16"
}

variable "hub_subnet_cidrs" {
  description = "Private subnet CIDRs in the hub VPC, one per AZ in availability_zones (order-aligned)."
  type        = list(string)
  default     = ["10.70.1.0/24", "10.70.2.0/24"]
}

variable "spoke_vpc_cidr" {
  description = "CIDR for the spoke workload VPC. Must not overlap with hub_vpc_cidr."
  type        = string
  default     = "10.71.0.0/16"
}

variable "spoke_subnet_cidrs" {
  description = "Private subnet CIDRs in the spoke VPC, one per AZ in availability_zones (order-aligned)."
  type        = list(string)
  default     = ["10.71.1.0/24", "10.71.2.0/24"]
}

variable "name_prefix" {
  description = "Base name prefix. Combined with var.environment to produce the effective prefix applied to all resources."
  type        = string
  default     = "cs-privatelink-tgw"
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
