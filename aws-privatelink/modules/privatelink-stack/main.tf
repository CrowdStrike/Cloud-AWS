resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

locals {
  # AZ name -> subnet CIDR. for_each keyed on AZ keeps plans stable across
  # reorders of var.availability_zones.
  private_subnets = zipmap(var.availability_zones, var.subnet_cidrs)
}

resource "aws_subnet" "private" {
  for_each = local.private_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name_prefix}-private-${each.key}"
  }

  lifecycle {
    precondition {
      condition     = length(var.availability_zones) == length(var.subnet_cidrs)
      error_message = "availability_zones and subnet_cidrs must be the same length (they pair 1:1)."
    }
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
}
