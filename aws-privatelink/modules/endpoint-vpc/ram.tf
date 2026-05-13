# AWS RAM: share the private subnets with consumer accounts so their instances
# can launch ENIs directly into this VPC. The PHZ attaches to the VPC (not the
# subnet), so DNS for cloudsink.net "just works" for any workload in these
# shared subnets — no cross-account R53 plumbing needed.
#
# Empty var.ram_principals disables the share entirely (01-per-vpc single-
# account case). The count-gating keeps plans clean for that path.

locals {
  enable_ram = length(var.ram_principals) > 0
}

resource "aws_ram_resource_share" "subnets" {
  count = local.enable_ram ? 1 : 0

  name                      = "${var.name_prefix}-subnets"
  allow_external_principals = false # stays within the AWS org

  tags = {
    Name = "${var.name_prefix}-subnets"
  }
}

resource "aws_ram_principal_association" "consumers" {
  for_each = local.enable_ram ? toset(var.ram_principals) : toset([])

  principal          = each.value
  resource_share_arn = aws_ram_resource_share.subnets[0].arn
}

resource "aws_ram_resource_association" "subnets" {
  for_each = local.enable_ram ? aws_subnet.private : {}

  resource_arn       = each.value.arn
  resource_share_arn = aws_ram_resource_share.subnets[0].arn
}
