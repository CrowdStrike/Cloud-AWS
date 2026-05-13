# Spoke account — VPC, subnets, local SSM + S3 gw endpoints, TGW
# attachment, sensor host. Kept inline (not a module) because this VPC
# shape is unique to 03 (no CrowdStrike endpoints locally, has a TGW
# attachment) and adding a third module for one example isn't worth it.

resource "aws_vpc" "spoke" {
  provider = aws.spoke

  cidr_block           = var.spoke_vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_prefix}-spoke"
  }
}

resource "aws_subnet" "spoke" {
  provider = aws.spoke

  for_each = { for idx, az in var.availability_zones : az => var.spoke_subnet_cidrs[idx] }

  vpc_id            = aws_vpc.spoke.id
  availability_zone = each.key
  cidr_block        = each.value

  tags = {
    Name = "${local.name_prefix}-spoke-${each.key}"
  }
}

resource "aws_route_table" "spoke" {
  provider = aws.spoke

  vpc_id = aws_vpc.spoke.id

  tags = {
    Name = "${local.name_prefix}-spoke"
  }
}

resource "aws_route_table_association" "spoke" {
  provider = aws.spoke

  for_each = aws_subnet.spoke

  subnet_id      = each.value.id
  route_table_id = aws_route_table.spoke.id
}

# Spoke -> Hub reach for CrowdStrike traffic. Spoke instance egresses on
# 443 to hub_vpc_cidr, TGW routes the packet to the hub attachment, hub
# VPC RT delivers it to the CS endpoint ENIs.
resource "aws_route" "spoke_to_hub" {
  provider = aws.spoke

  route_table_id         = aws_route_table.spoke.id
  destination_cidr_block = var.hub_vpc_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.spoke]
}

# TGW attachment lives in the spoke account. auto_accept_shared_attachments
# on the hub TGW means this attachment is accepted implicitly — no
# matching accepter resource on the hub side.
resource "aws_ec2_transit_gateway_vpc_attachment" "spoke" {
  provider = aws.spoke

  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = aws_vpc.spoke.id
  subnet_ids         = [for s in aws_subnet.spoke : s.id]

  # Associations/propagations are managed from the hub (tgw_route_tables.tf).
  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false

  tags = {
    Name = "${local.name_prefix}-spoke-attach"
  }

  depends_on = [aws_ram_principal_association.tgw]
}

# Local S3 gateway endpoint — gateway endpoints can't traverse TGW, so
# each spoke needs its own. Cheap (no ENIs, no hourly charge).
resource "aws_vpc_endpoint" "spoke_s3" {
  provider = aws.spoke

  vpc_id            = aws_vpc.spoke.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.spoke.id]

  tags = {
    Name = "${local.name_prefix}-spoke-s3"
  }
}

# Local SSM interface endpoints. SSM private DNS is VPC-scoped, so sharing
# SSM endpoints across VPCs via TGW doesn't work cleanly — the SSM agent
# resolves ssm.us-east-2.amazonaws.com via public DNS, which wouldn't hit
# the hub's endpoint. Keeping SSM local is the simple, boring answer.
locals {
  spoke_ssm_services = ["ssm", "ssmmessages", "ec2messages"]
}

resource "aws_security_group" "spoke_endpoints" {
  provider = aws.spoke

  name        = "${local.name_prefix}-spoke-endpoints"
  description = "HTTPS from the spoke instance SG into the spoke's local SSM endpoints"
  vpc_id      = aws_vpc.spoke.id

  tags = {
    Name = "${local.name_prefix}-spoke-endpoints"
  }
}

resource "aws_vpc_security_group_ingress_rule" "spoke_endpoints_from_instance" {
  provider = aws.spoke

  security_group_id            = aws_security_group.spoke_endpoints.id
  description                  = "HTTPS from spoke instance SG"
  referenced_security_group_id = module.sensor_host.instance_sg_id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_endpoint" "spoke_ssm" {
  provider = aws.spoke

  for_each = toset(local.spoke_ssm_services)

  vpc_id              = aws_vpc.spoke.id
  service_name        = "com.amazonaws.${var.region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [for s in aws_subnet.spoke : s.id]
  security_group_ids  = [aws_security_group.spoke_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-spoke-${each.key}"
  }
}

# Associate the RAM-shared R53 Profile with the spoke VPC. This gives the
# spoke VPC visibility into cloudsink.net -> the hub's CS endpoint ENIs
# with zero per-VPC R53 grant plumbing.
resource "aws_route53profiles_association" "spoke" {
  provider = aws.spoke

  name        = "${local.name_prefix}-spoke"
  profile_id  = aws_route53profiles_profile.cloudsink.id
  resource_id = aws_vpc.spoke.id

  depends_on = [aws_ram_principal_association.profile]
}

# Sensor host. Same module as 01/02, but:
#   * endpoints_sg_id points at the spoke's LOCAL SSM endpoints SG
#     (not the hub's CS endpoints SG — that's reached via CIDR egress).
#   * egress_cidr_blocks = [hub_vpc_cidr] opens HTTPS to the hub for CS
#     endpoint reach over the TGW.
#   * s3_prefix_list_id points at the spoke's LOCAL S3 gw endpoint.
module "sensor_host" {
  source = "../../modules/sensor-host"

  providers = {
    aws = aws.spoke
  }

  region      = var.region
  name_prefix = local.name_prefix

  vpc_id     = aws_vpc.spoke.id
  subnet_ids = [for s in aws_subnet.spoke : s.id]

  endpoints_sg_id    = aws_security_group.spoke_endpoints.id
  s3_prefix_list_id  = aws_vpc_endpoint.spoke_s3.prefix_list_id
  egress_cidr_blocks = [var.hub_vpc_cidr]

  sensor_bucket_name    = module.endpoint_vpc.sensor_bucket_name
  sensor_bucket_rpm_key = module.endpoint_vpc.sensor_bucket_rpm_key

  falcon_cloud = var.falcon_cloud
  falcon_cid   = local.fetched_cid
}
