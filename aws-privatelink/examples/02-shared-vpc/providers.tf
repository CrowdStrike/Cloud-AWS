locals {
  common_tags = {
    Environment = var.environment
    OwnerEmail  = var.owner_email
    ManagedBy   = "terraform"
    Project     = "aws-privatelink"
  }
}

provider "aws" {
  alias   = "owner"
  region  = var.region
  profile = var.owner_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "owner" })
  }
}

provider "aws" {
  alias   = "workload"
  region  = var.region
  profile = var.workload_profile

  default_tags {
    tags = merge(local.common_tags, { Role = "workload" })
  }
}
