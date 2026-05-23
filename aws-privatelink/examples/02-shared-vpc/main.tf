# Two-account shared VPC. The owner provisions a single VPC with all the
# PrivateLink plumbing and RAM-shares its subnets to the workload account.
# The workload launches a sensor host directly into those shared subnets.
#
# The RPM and CID come from fetch.tf (root-level), so the Falcon API is
# hit once per apply.

data "aws_availability_zones" "available" {
  provider = aws.owner
  state    = "available"
}

locals {
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
  vpc_cidr     = "10.60.0.0/16"
  subnet_cidrs = [cidrsubnet(local.vpc_cidr, 8, 1), cidrsubnet(local.vpc_cidr, 8, 2)]
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  providers = {
    aws = aws.owner
  }

  region             = var.region
  availability_zones = local.azs
  name_prefix        = var.environment

  vpc_cidr     = local.vpc_cidr
  subnet_cidrs = local.subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  sensor_rpm_path = local.fetched_rpm_path

  ram_principals = [var.workload_account_id]

  consumer_sg_ids = {
    workload-host = module.sensor_host.instance_sg_id
  }

  authorized_role_arns = [
    module.sensor_host.instance_role_arn,
  ]
}

module "sensor_host" {
  source = "../../modules/sensor-host"

  providers = {
    aws = aws.workload
  }

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
