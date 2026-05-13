# Route 53 Profiles (Nov 2024) — the secondary upgrade over the classic
# "cross-account PHZ association" treadmill. The PHZ lives on the hub's
# endpoint VPC (created by the endpoint-vpc module). A Profile is a
# container that can hold multiple PHZs; we associate cloudsink.net with
# it, RAM-share it to the spoke account, and the spoke associates the
# profile with its own VPC. All DNS resolution for *.cloudsink.net in the
# spoke VPC then resolves to the hub's endpoint ENI IPs.
#
# Key properties vs classic PHZ associations:
#   * No per-VPC cross-account Route 53 grant (no auth-plus-associate
#     dance through aws_route53_vpc_association_authorization).
#   * One profile can hold N zones — future work (CloudTrail, STS, etc.)
#     just adds more profile-resource associations; spokes pick them up
#     automatically.
#   * Profiles are region-scoped. For multi-region reach, create one
#     profile per region and share each.

resource "aws_route53profiles_profile" "cloudsink" {
  provider = aws.hub

  name = "${local.name_prefix}-profile"

  tags = {
    Name = "${local.name_prefix}-profile"
  }
}

# Add cloudsink.net (PHZ owned by the endpoint-vpc module) to the profile.
resource "aws_route53profiles_resource_association" "cloudsink_phz" {
  provider = aws.hub

  name         = "${local.name_prefix}-cloudsink"
  profile_id   = aws_route53profiles_profile.cloudsink.id
  resource_arn = "arn:aws:route53:::hostedzone/${module.endpoint_vpc.phz_id}"
}

# Share the profile with the spoke account. Spoke picks it up via its own
# aws_route53profiles_association pointing at its VPC.
resource "aws_ram_resource_share" "profile" {
  provider = aws.hub

  name                      = "${local.name_prefix}-profile"
  allow_external_principals = false

  tags = {
    Name = "${local.name_prefix}-profile"
  }
}

resource "aws_ram_resource_association" "profile" {
  provider = aws.hub

  resource_arn       = aws_route53profiles_profile.cloudsink.arn
  resource_share_arn = aws_ram_resource_share.profile.arn
}

resource "aws_ram_principal_association" "profile" {
  provider = aws.hub

  principal          = var.spoke_account_id
  resource_share_arn = aws_ram_resource_share.profile.arn
}
