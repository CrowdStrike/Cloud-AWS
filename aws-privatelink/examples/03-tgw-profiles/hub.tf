# Hub account — the endpoint VPC (reusing the same module as 01 and 02)
# plus the TGW and TGW RAM share. The endpoints SG ingress is wired from
# the spoke's CIDR (cross-VPC, so we can't use SG references like 02 does).

locals {
  name_prefix = "${var.environment}-${var.name_prefix}"
}

module "endpoint_vpc" {
  source = "../../modules/endpoint-vpc"

  providers = {
    aws = aws.hub
  }

  region             = var.region
  availability_zones = var.availability_zones
  name_prefix        = local.name_prefix

  vpc_cidr     = var.hub_vpc_cidr
  subnet_cidrs = var.hub_subnet_cidrs

  falcon_cloud    = var.falcon_cloud
  sensor_rpm_path = local.fetched_rpm_path

  # No subnet RAM share — 03 uses TGW for cross-account reach, not shared subnets.
  ram_principals = []

  # Spoke instance lives in a different VPC, so SG references don't work;
  # ingress is CIDR-based instead.
  consumer_cidr_blocks = [var.spoke_vpc_cidr]

  # Bucket policy grants the spoke instance role s3:GetObject on the RPM.
  authorized_role_arns = [
    module.sensor_host.instance_role_arn,
  ]
}

# Transit Gateway. auto_accept_shared_attachments = "enable" means spoke
# attachments created by the spoke account via the RAM share are accepted
# automatically (no owner-side aws_ec2_transit_gateway_vpc_attachment_accepter
# resource needed).
resource "aws_ec2_transit_gateway" "this" {
  provider = aws.hub

  description                     = "${local.name_prefix} TGW"
  amazon_side_asn                 = 64532
  auto_accept_shared_attachments  = "enable"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  dns_support                     = "enable"
  vpn_ecmp_support                = "enable"

  tags = {
    Name = "${local.name_prefix}-tgw"
  }
}

# Share the TGW itself with the spoke account. The spoke uses this grant to
# create its own aws_ec2_transit_gateway_vpc_attachment pointing at this TGW.
resource "aws_ram_resource_share" "tgw" {
  provider = aws.hub

  name                      = "${local.name_prefix}-tgw"
  allow_external_principals = false

  tags = {
    Name = "${local.name_prefix}-tgw"
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

# Hub VPC attaches to the TGW. Explicitly in hub.tf (not inside the module)
# so the module stays topology-agnostic — a TGW isn't relevant for 01/02.
resource "aws_ec2_transit_gateway_vpc_attachment" "hub" {
  provider = aws.hub

  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = module.endpoint_vpc.vpc_id
  subnet_ids         = module.endpoint_vpc.subnet_ids_list

  # Explicit — hub RT association/propagation is managed in tgw_route_tables.tf.
  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false

  tags = {
    Name = "${local.name_prefix}-hub-attach"
  }
}

# Hub VPC route table needs a spoke-CIDR route pointing at the TGW so
# return traffic to the spoke instance makes it out of the hub VPC.
resource "aws_route" "hub_to_spoke" {
  provider = aws.hub

  route_table_id         = module.endpoint_vpc.route_table_id
  destination_cidr_block = var.spoke_vpc_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.hub]
}
