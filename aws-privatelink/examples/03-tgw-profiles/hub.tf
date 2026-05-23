# Hub account — the endpoint VPC (reusing the same module as 01 and 02)
# plus the TGW and TGW RAM share. The endpoints SG ingress is wired from
# the spoke's CIDR (cross-VPC, so we can't use SG references like 02 does).

data "aws_availability_zones" "available" {
  provider = aws.hub
  state    = "available"
}

locals {
  azs                = slice(data.aws_availability_zones.available.names, 0, 2)
  hub_vpc_cidr       = "10.70.0.0/16"
  hub_subnet_cidrs   = [cidrsubnet(local.hub_vpc_cidr, 8, 1), cidrsubnet(local.hub_vpc_cidr, 8, 2)]
  spoke_vpc_cidr     = "10.71.0.0/16"
  spoke_subnet_cidrs = [cidrsubnet(local.spoke_vpc_cidr, 8, 1), cidrsubnet(local.spoke_vpc_cidr, 8, 2)]
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  providers = {
    aws = aws.hub
  }

  region             = var.region
  availability_zones = local.azs
  name_prefix        = var.environment

  vpc_cidr     = local.hub_vpc_cidr
  subnet_cidrs = local.hub_subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  sensor_rpm_path = local.fetched_rpm_path

  ram_principals = []

  consumer_cidr_blocks = [local.spoke_vpc_cidr]

  authorized_role_arns = [
    module.sensor_host.instance_role_arn,
  ]
}

resource "aws_ec2_transit_gateway" "this" {
  provider = aws.hub

  description                     = "${var.environment} TGW"
  amazon_side_asn                 = 64532
  auto_accept_shared_attachments  = "enable"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  dns_support                     = "enable"
  vpn_ecmp_support                = "enable"

  tags = {
    Name = "${var.environment}-tgw"
  }
}

resource "aws_ram_resource_share" "tgw" {
  provider = aws.hub

  name                      = "${var.environment}-tgw"
  allow_external_principals = false

  tags = {
    Name = "${var.environment}-tgw"
  }
}

resource "aws_ram_resource_association" "tgw" {
  provider = aws.hub

  resource_arn       = aws_ec2_transit_gateway.this.arn
  resource_share_arn = aws_ram_resource_share.tgw.arn
}

resource "aws_ram_principal_association" "tgw" {
  provider = aws.hub

  principal          = var.spoke_account_id
  resource_share_arn = aws_ram_resource_share.tgw.arn
}

resource "aws_ec2_transit_gateway_vpc_attachment" "hub" {
  provider = aws.hub

  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = module.endpoint_vpc.vpc_id
  subnet_ids         = module.endpoint_vpc.subnet_ids_list

  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false

  tags = {
    Name = "${var.environment}-hub-attach"
  }
}

resource "aws_route" "hub_to_spoke" {
  provider = aws.hub

  route_table_id         = module.endpoint_vpc.route_table_id
  destination_cidr_block = local.spoke_vpc_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.hub]
}
