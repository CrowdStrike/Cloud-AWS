resource "aws_security_group" "instance" {
  name        = "${var.name_prefix}-instance"
  description = "Falcon sensor host - egress to CrowdStrike + S3 endpoints. SSM-only by default; SSH optional."
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-instance"
  }

  lifecycle {
    create_before_destroy = true
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
  referenced_security_group_id = aws_security_group.endpoints.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "instance_https_to_s3" {
  security_group_id = aws_security_group.instance.id
  description       = "HTTPS to S3 (sensor bucket + AL2023 dnf repos via S3 gateway endpoint)"
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_security_group" "endpoints" {
  name        = "${var.name_prefix}-endpoints"
  description = "HTTPS from the instance SG into interface endpoints."
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-endpoints"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "endpoints_https_from_instance" {
  security_group_id            = aws_security_group.endpoints.id
  description                  = "HTTPS from instance SG"
  referenced_security_group_id = aws_security_group.instance.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}
