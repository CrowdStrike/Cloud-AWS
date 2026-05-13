# Two-account shared VPC. The owner provisions a single VPC with all the
# PrivateLink plumbing and RAM-shares its subnets to the workload account.
# The workload launches a sensor host directly into those shared subnets —
# no workload VPC, no cross-account R53, no cross-account SSM params.
#
# Cross-cutting wiring:
#   * endpoint_vpc.consumer_sg_ids <- sensor_host.instance_sg_id (the SG
#     reference breaks out of the workload account into the endpoints SG
#     because both SGs live in the owner's VPC)
#   * endpoint_vpc.authorized_role_arns <- sensor_host.instance_role_arn
#     (grants the workload instance role s3:GetObject on the sensor bucket)
#
# for_each on the consumer_sg_ids uses a literal string key ("workload-host"),
# so it's plan-time known; the SG ID value is apply-time computed. That's
# what lets this compose without a resource cycle or depends_on hack.

locals {
  name_prefix = "${var.environment}-${var.name_prefix}"
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  providers = {
    aws = aws.owner
  }

  region             = var.region
  availability_zones = var.availability_zones
  name_prefix        = local.name_prefix

  vpc_cidr     = var.vpc_cidr
  subnet_cidrs = var.subnet_cidrs

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
