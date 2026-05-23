# Single-account, single-region stack. Creates one VPC with CrowdStrike
# PrivateLink endpoints, S3 bucket, PHZ, and a private sensor host. Uses
# the same endpoint-vpc + sensor-host modules as 02 and 03.
#
# The RPM and CID come from fetch.tf (root-level), so the Falcon API is
# hit once per apply.

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
  vpc_cidr     = "10.50.0.0/16"
  subnet_cidrs = [cidrsubnet(local.vpc_cidr, 8, 1), cidrsubnet(local.vpc_cidr, 8, 2)]
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  region             = var.region
  availability_zones = local.azs
  name_prefix        = var.environment

  vpc_cidr     = local.vpc_cidr
  subnet_cidrs = local.subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  sensor_rpm_path = local.fetched_rpm_path

  ram_principals = []

  consumer_sg_ids = {
    sensor-host = module.sensor_host.instance_sg_id
  }
}

module "sensor_host" {
  source = "../../modules/sensor-host"

  region      = var.region
  name_prefix = var.environment

  vpc_id     = module.endpoint_vpc.vpc_id
  subnet_ids = module.endpoint_vpc.subnet_ids_list

  endpoints_sg_id   = module.endpoint_vpc.endpoints_sg_id
  s3_prefix_list_id = module.endpoint_vpc.s3_prefix_list_id

  sensor_bucket_name    = module.endpoint_vpc.sensor_bucket_name
  sensor_bucket_rpm_key = module.endpoint_vpc.sensor_bucket_rpm_key

  falcon_cloud  = var.falcon_cloud
  falcon_cid    = local.fetched_cid
  instance_type = var.instance_type
  ami_id        = var.ami_id
}
