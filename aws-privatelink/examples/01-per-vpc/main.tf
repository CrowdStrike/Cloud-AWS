# Single-account, single-region stack. Creates one VPC with CrowdStrike
# PrivateLink endpoints, S3 bucket, PHZ, and a private sensor host. Uses
# the same endpoint-vpc + sensor-host modules as 02 and 03 — the only
# difference is that both modules share one provider and no RAM / TGW is
# needed.
#
# The RPM and CID come from fetch.tf (root-level), so the Falcon API is
# hit once per apply.

locals {
  name_prefix = "${var.environment}-${var.name_prefix}"
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  region             = var.region
  availability_zones = var.availability_zones
  name_prefix        = local.name_prefix

  vpc_cidr     = var.vpc_cidr
  subnet_cidrs = var.subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  sensor_rpm_path = local.fetched_rpm_path

  # Single-account: no RAM subnet sharing needed.
  ram_principals = []

  # Wire instance SG into the endpoints SG ingress.
  consumer_sg_ids = {
    sensor-host = module.sensor_host.instance_sg_id
  }
}

module "sensor_host" {
  source = "../../modules/sensor-host"

  region      = var.region
  name_prefix = local.name_prefix

  vpc_id     = module.endpoint_vpc.vpc_id
  subnet_ids = module.endpoint_vpc.subnet_ids_list

  endpoints_sg_id   = module.endpoint_vpc.endpoints_sg_id
  s3_prefix_list_id = module.endpoint_vpc.s3_prefix_list_id

  sensor_bucket_name    = module.endpoint_vpc.sensor_bucket_name
  sensor_bucket_rpm_key = module.endpoint_vpc.sensor_bucket_rpm_key

  falcon_cloud = var.falcon_cloud
  falcon_cid   = local.fetched_cid
}
