locals {
  common_tags = {
    Environment = var.environment
    OwnerEmail  = var.owner_email
    ManagedBy   = "terraform"
    Project     = "aws-privatelink"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}
