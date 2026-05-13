locals {
  common_tags = {
    Environment = var.environment
    OwnerEmail  = var.owner_email
    ManagedBy   = "terraform"
    Project     = "aws-privatelink-reference"
    Example     = "02-shared-vpc"
  }
}

# Owner account — hosts the VPC, endpoints, PHZ, sensor bucket, RAM share.
# One AWS allowlist ticket is filed against this account.
provider "aws" {
  alias   = "owner"
  region  = var.region
  profile = var.owner_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "owner" })
  }
}

# Workload account — launches EC2 into the RAM-shared subnets. No VPC of its
# own. Any number of workload accounts share this shape; the module just gets
# called once per account with a matching provider alias.
provider "aws" {
  alias   = "workload"
  region  = var.region
  profile = var.workload_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "workload" })
  }
}
