locals {
  common_tags = {
    Environment = var.environment
    OwnerEmail  = var.owner_email
    ManagedBy   = "terraform"
    Project     = "aws-privatelink"
  }
}

provider "aws" {
  alias   = "hub"
  region  = var.region
  profile = var.hub_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "hub" })
  }
}

provider "aws" {
  alias   = "spoke"
  region  = var.region
  profile = var.spoke_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "spoke" })
  }
}
