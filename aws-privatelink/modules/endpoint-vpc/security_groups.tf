resource "aws_security_group" "endpoints" {
  name        = "${var.name_prefix}-endpoints"
  description = "HTTPS from consumer SGs into interface endpoints. Cross-account SG references are supported when both SGs live in the same VPC."
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-endpoints"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# One ingress rule per consumer SG. Keys are plan-time literals (stable);
# values are apply-time SG IDs from the consumer module's output. This is
# what breaks the module cycle without a depends_on.
resource "aws_vpc_security_group_ingress_rule" "endpoints_https_from_consumers" {
  for_each = var.consumer_sg_ids

  security_group_id            = aws_security_group.endpoints.id
  description                  = "HTTPS from ${each.key}"
  referenced_security_group_id = each.value
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

# CIDR-based ingress for consumers that live in a different VPC (reached
# via TGW / peering). SG references can't cross VPCs, so the TGW topology
# (03) passes spoke CIDRs here instead of SG IDs.
resource "aws_vpc_security_group_ingress_rule" "endpoints_https_from_cidrs" {
  for_each = toset(var.consumer_cidr_blocks)

  security_group_id = aws_security_group.endpoints.id
  description       = "HTTPS from ${each.value}"
  cidr_ipv4         = each.value
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}
