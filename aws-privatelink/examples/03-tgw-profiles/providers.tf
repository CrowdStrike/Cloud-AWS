locals {
  common_tags = {
    Environment = var.environment
    OwnerEmail  = var.owner_email
    ManagedBy   = "terraform"
    Project     = "aws-privatelink-reference"
    Example     = "03-tgw-profiles"
  }
}

# Hub (networking) account — hosts the endpoint VPC, TGW, CrowdStrike
# endpoints, cloudsink.net PHZ, R53 Profile, and sensor bucket. One
# CrowdStrike allowlist ticket is filed against this account.
provider "aws" {
  alias   = "hub"
  region  = var.region
  profile = var.hub_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "hub" })
  }
}

# Spoke (workload) account — owns its own VPC with local SSM + S3 gateway
# endpoints, attaches to the TGW, and consumes the hub's CrowdStrike
# endpoints + PHZ via the RAM-shared R53 Profile. Any number of spokes
# share this shape.
provider "aws" {
  alias   = "spoke"
  region  = var.region
  profile = var.spoke_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "spoke" })
  }
}
