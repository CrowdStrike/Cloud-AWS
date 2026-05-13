resource "aws_security_group" "instance" {
  name        = "${var.name_prefix}-instance"
  description = "Falcon sensor host - egress to CrowdStrike + S3 endpoints. SSM-only by default; SSH optional."
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-instance"
  }
}

# SSH is only wired up if both a key pair and an allowed CIDR are supplied.
# For SSM-only deployments (recommended), leave key_name + ssh_allowed_cidr null.
resource "aws_vpc_security_group_ingress_rule" "instance_ssh" {
  count = var.key_name != null && var.ssh_allowed_cidr != null ? 1 : 0

  security_group_id = aws_security_group.instance.id
  description       = "SSH from on-prem (reaches VPC via existing VPN/TGW/peering)"
  cidr_ipv4         = var.ssh_allowed_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "instance_https_to_endpoints" {
  security_group_id            = aws_security_group.instance.id
  description                  = "HTTPS to CrowdStrike + SSM interface endpoints"
  referenced_security_group_id = var.endpoints_sg_id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "instance_https_to_s3" {
  security_group_id = aws_security_group.instance.id
  description       = "HTTPS to S3 (sensor bucket + AL2023 dnf repos via S3 gateway endpoint)"
  prefix_list_id    = var.s3_prefix_list_id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# HTTPS egress to arbitrary CIDRs (TGW / peering reach). Used by 03 to let
# the spoke instance reach the hub's CrowdStrike endpoints across the TGW.
resource "aws_vpc_security_group_egress_rule" "instance_https_to_cidrs" {
  for_each = toset(var.egress_cidr_blocks)

  security_group_id = aws_security_group.instance.id
  description       = "HTTPS to ${each.value}"
  cidr_ipv4         = each.value
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}
