# Explicit TGW segmentation — "shared services" pattern. Rather than the
# default TGW route table (auto-associate + auto-propagate everything),
# we use two route tables:
#
#   * hub-rt:   the hub attachment lives here. Its propagations pull in
#               the spoke's VPC CIDR, so the hub can reach all spokes.
#   * spoke-rt: every spoke attachment associates here. Only the hub's
#               VPC CIDR is propagated, so spokes can reach the hub but
#               NOT each other (spoke-to-spoke isolation is the headline
#               before/after for 03's TGW segmentation).
#
# Today there's one spoke, so the pattern looks heavy. Adding the 2nd / Nth
# spoke is a single additional aws_ec2_transit_gateway_vpc_attachment +
# one association row + one propagation row — which is the whole point.

resource "aws_ec2_transit_gateway_route_table" "hub" {
  provider = aws.hub

  transit_gateway_id = aws_ec2_transit_gateway.this.id

  tags = {
    Name = "${local.name_prefix}-hub-rt"
  }
}

resource "aws_ec2_transit_gateway_route_table" "spoke" {
  provider = aws.hub

  transit_gateway_id = aws_ec2_transit_gateway.this.id

  tags = {
    Name = "${local.name_prefix}-spoke-rt"
  }
}

# Hub attachment associations/propagations.
resource "aws_ec2_transit_gateway_route_table_association" "hub" {
  provider = aws.hub

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.hub.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
}

# Hub's RT learns the spoke CIDR so return traffic to the spoke works.
resource "aws_ec2_transit_gateway_route_table_propagation" "spoke_to_hub_rt" {
  provider = aws.hub

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.hub.id
}

# Spoke attachment associations/propagations.
resource "aws_ec2_transit_gateway_route_table_association" "spoke" {
  provider = aws.hub

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.spoke.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke.id
}

# Spoke's RT only learns the hub CIDR (not other spokes).
resource "aws_ec2_transit_gateway_route_table_propagation" "hub_to_spoke_rt" {
  provider = aws.hub

  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.hub.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke.id
}
