locals {
  ssm_services = ["ssm", "ssmmessages", "ec2messages"]

  cloud_home_region = {
    "us-1" = "us-west-1"
    "us-2" = "us-west-2"
    "eu-1" = "eu-central-1"
  }

  cloud_endpoint_services = {
    "us-1" = {
      sensor_proxy    = "com.amazonaws.vpce.us-west-1.vpce-svc-08744dea97b26db5d"
      download_server = "com.amazonaws.vpce.us-west-1.vpce-svc-0f9d8ca86ddcb7106"
      upload_server   = "com.amazonaws.vpce.us-west-1.vpce-svc-0fa888d7b9e4130f4"
    }
    "us-2" = {
      sensor_proxy    = "com.amazonaws.vpce.us-west-2.vpce-svc-08a5bb05d337fd834"
      download_server = "com.amazonaws.vpce.us-west-2.vpce-svc-0e11def2d8620ae74"
      upload_server   = "com.amazonaws.vpce.us-west-2.vpce-svc-074a82fde584744da"
    }
    "eu-1" = {
      sensor_proxy    = "com.amazonaws.vpce.eu-central-1.vpce-svc-0eb7b6ca4b7271385"
      download_server = "com.amazonaws.vpce.eu-central-1.vpce-svc-0340142b9ab8fc564"
      upload_server   = "com.amazonaws.vpce.eu-central-1.vpce-svc-0148ff0159e9419dd"
    }
  }

  cloud_hostname_slugs = {
    "us-1" = "b"
    "us-2" = "gyr-maverick"
    "eu-1" = "lanner-lion"
  }

  crowdstrike_home_region = local.cloud_home_region[var.falcon_cloud]
  crowdstrike_endpoints   = local.cloud_endpoint_services[var.falcon_cloud]

  # service_region is null when the consumer VPC is already in the Falcon
  # cloud's home region (endpoint service is reachable natively). Otherwise
  # it's set to the home region so the endpoint targets the service hosted
  # there over the AWS backbone.
  effective_service_region = var.region == local.crowdstrike_home_region ? null : local.crowdstrike_home_region

  private_subnet_ids = [for s in aws_subnet.private : s.id]
}

# S3 gateway endpoint — lets instances pull objects from the sensor bucket
# (and regional AWS buckets, e.g. AL2023 dnf repos) without an IGW/NAT.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = {
    Name = "${var.name_prefix}-s3-gw"
  }
}

# SSM interface endpoints — all three are required for Session Manager.
# One ENI per AZ listed in var.availability_zones.
resource "aws_vpc_endpoint" "ssm" {
  for_each = toset(local.ssm_services)

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.private_subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.name_prefix}-${each.value}"
  }
}

# CrowdStrike PrivateLink endpoints, one ENI per AZ. service_region is null
# for native deploys (consumer VPC in the Falcon cloud's home region) and the
# home region for cross-region deploys. Private DNS is not supported for
# these service types — resolution comes from the PHZ in route53.tf.
resource "aws_vpc_endpoint" "crowdstrike" {
  for_each = local.crowdstrike_endpoints

  vpc_id              = aws_vpc.this.id
  service_name        = each.value
  service_region      = local.effective_service_region
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.private_subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = false

  tags = {
    Name = "${var.name_prefix}-cs-${each.key}"
  }
}
