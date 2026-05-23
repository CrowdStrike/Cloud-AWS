# Spoke account — VPC, subnets, local SSM + S3 gw endpoints, TGW
# attachment, sensor host. Kept inline (not a module) because this VPC
# shape is unique to 03 (no CrowdStrike endpoints locally, has a TGW
# attachment) and adding a third module for one example isn't worth it.

resource "aws_vpc" "spoke" {
  provider = aws.spoke

  cidr_block           = local.spoke_vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.environment}-spoke"
  }
}

resource "aws_subnet" "spoke" {
  provider = aws.spoke

  for_each = { for idx, az in local.azs : az => local.spoke_subnet_cidrs[idx] }

  vpc_id            = aws_vpc.spoke.id
  availability_zone = each.key
  cidr_block        = each.value

  tags = {
    Name = "${var.environment}-spoke-${each.key}"
  }
}

resource "aws_route_table" "spoke" {
  provider = aws.spoke

  vpc_id = aws_vpc.spoke.id

  tags = {
    Name = "${var.environment}-spoke"
  }
}

resource "aws_route_table_association" "spoke" {
  provider = aws.spoke

  for_each = aws_subnet.spoke

  subnet_id      = each.value.id
  route_table_id = aws_route_table.spoke.id
}

resource "aws_route" "spoke_to_hub" {
  provider = aws.spoke

  route_table_id         = aws_route_table.spoke.id
  destination_cidr_block = local.hub_vpc_cidr
  transit_gateway_id     = aws_ec2_transit_gateway.this.id

  depends_on = [aws_ec2_transit_gateway_vpc_attachment.spoke]
}

resource "aws_ec2_transit_gateway_vpc_attachment" "spoke" {
  provider = aws.spoke

  transit_gateway_id = aws_ec2_transit_gateway.this.id
  vpc_id             = aws_vpc.spoke.id
  subnet_ids         = [for s in aws_subnet.spoke : s.id]

  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false

  tags = {
    Name = "${var.environment}-spoke-attach"
  }

  depends_on = [aws_ram_principal_association.tgw]
}

resource "aws_vpc_endpoint" "spoke_s3" {
  provider = aws.spoke

  vpc_id            = aws_vpc.spoke.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.spoke.id]

  tags = {
    Name = "${var.environment}-spoke-s3"
  }
}

locals {
  spoke_ssm_services = ["ssm", "ssmmessages", "ec2messages"]
}

resource "aws_security_group" "spoke_endpoints" {
  provider = aws.spoke

  name        = "${var.environment}-spoke-endpoints"
  description = "HTTPS from the spoke instance SG into the spoke's local SSM endpoints"
  vpc_id      = aws_vpc.spoke.id

  tags = {
    Name = "${var.environment}-spoke-endpoints"
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
    Name = "${var.environment}-spoke-${each.key}"
  }
}

resource "aws_route53profiles_association" "spoke" {
  provider = aws.spoke

  name        = "${var.environment}-spoke"
  profile_id  = aws_route53profiles_profile.cloudsink.id
  resource_id = aws_vpc.spoke.id

  depends_on = [aws_ram_principal_association.profile]
}

module "sensor_host" {
  source = "../../modules/sensor-host"

  providers = {
    aws = aws.spoke
  }

  region      = var.region
  name_prefix = var.environment

  vpc_id     = aws_vpc.spoke.id
  subnet_ids = [for s in aws_subnet.spoke : s.id]

  endpoints_sg_id    = aws_security_group.spoke_endpoints.id
  s3_prefix_list_id  = aws_vpc_endpoint.spoke_s3.prefix_list_id
  egress_cidr_blocks = [local.hub_vpc_cidr]

  sensor_bucket_name    = module.endpoint_vpc.sensor_bucket_name
  sensor_bucket_rpm_key = module.endpoint_vpc.sensor_bucket_rpm_key

  falcon_cloud  = var.falcon_cloud
  falcon_cid    = local.fetched_cid
  instance_type = var.instance_type
  ami_id        = var.ami_id
}
