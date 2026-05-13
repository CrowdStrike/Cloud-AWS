# Single-region stack. Creates one VPC with endpoints across two AZs, S3
# bucket, PHZ, IAM, and sensor host. service_region on the CrowdStrike
# endpoints is derived inside the module from var.falcon_cloud vs.
# var.region, so the stack reaches the US-2 service from wherever it is
# deployed without any customer-facing toggle.
#
# The RPM and CID come from fetch.tf (root-level), so the Falcon API is
# hit once per apply.

locals {
  name_prefix = "${var.environment}-${var.name_prefix}"
}

module "privatelink" {
  source = "../../modules/privatelink-stack"

  region             = var.region
  availability_zones = var.availability_zones
  name_prefix        = local.name_prefix

  vpc_cidr     = var.vpc_cidr
  subnet_cidrs = var.subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  falcon_cid      = local.fetched_cid
  sensor_rpm_path = local.fetched_rpm_path
}
