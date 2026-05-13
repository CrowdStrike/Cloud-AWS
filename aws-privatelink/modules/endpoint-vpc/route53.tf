locals {
  slug = local.cloud_hostname_slugs[var.falcon_cloud]
  crowdstrike_hostnames = {
    "ts01-${local.slug}"      = "sensor_proxy"
    "lfodown01-${local.slug}" = "download_server"
    "lfoup01-${local.slug}"   = "upload_server"
  }
}

# Private hosted zone for cloudsink.net — overrides public DNS inside this VPC only.
# Shared RAM subnets launch ENIs into this VPC, so consumer workloads inherit
# this PHZ automatically — no cross-account R53 association needed.
# NOTE: This captures ALL queries for *.cloudsink.net inside the VPC. Anything not
# explicitly defined below will return NXDOMAIN.
resource "aws_route53_zone" "cloudsink" {
  name = "cloudsink.net"

  vpc {
    vpc_id = aws_vpc.this.id
  }

  tags = {
    Name = "${var.name_prefix}-cloudsink-private"
  }
}

resource "aws_route53_record" "crowdstrike" {
  for_each = local.crowdstrike_hostnames

  zone_id = aws_route53_zone.cloudsink.zone_id
  name    = "${each.key}.cloudsink.net"
  type    = "A"

  alias {
    name                   = aws_vpc_endpoint.crowdstrike[each.value].dns_entry[0].dns_name
    zone_id                = aws_vpc_endpoint.crowdstrike[each.value].dns_entry[0].hosted_zone_id
    evaluate_target_health = false
  }
}
