# IAM Role used by CrowdStrike Discover 
resource "aws_iam_role" "CrowdStrike_Discover_Role" {
  name               = var.RoleName
  description = "Role assumed by Falcon Discover to Describe API calls"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.CrowdStrikeDiscoverAssumeRolePolicyDocument.json
}
# Resources queried by CrowdStrike Discover
data "aws_iam_policy_document" "DescribeAPICalls" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeInstances",
      "ec2:DescribeImages",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeVolumes",
      "ec2:DescribeVpcs",
      "ec2:DescribeRegions",
      "ec2:DescribeSubnets",
      "ec2:DescribeNetworkAcls",
      "ec2:DescribeSecurityGroups",
      "iam:ListAccountAliases"
    ]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "CrowdStrikeDiscoverAssumeRolePolicyDocument" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${var.CSAccountNumber}:role/${var.CSAssumingRoleName}"
      ]
    }
    condition {
      test = "StringEquals"
      variable = "sts:ExternalId"

      values = [
        var.ExternalID
      ]
    }
  }
}

resource "aws_iam_policy" "DescribeAPICallsRolePolicy" {
  name = "DescribeAPICallsRolePolicy"
  path = "/"
  policy = data.aws_iam_policy_document.DescribeAPICalls.json
}


resource "aws_iam_role_policy_attachment" "iamPolicyDescribeAPICallsAttach" {
  role = aws_iam_role.CrowdStrike_Discover_Role.name
  policy_arn = aws_iam_policy.DescribeAPICallsRolePolicy.arn
}

# Each account will required registering via the CrowdStrike API
# These outputs are required to register the account using fd_accounts.py
# https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/troubleshooting/scripts
# See registering an account
# $ python3 fd_accounts.py -f CLIENT_ID -s CLIENT_SECRET -c register --external_id IwXs93to8iHEkl0 -a 123456789012 -r eu-west-1 -o 123456789012 -i arn:aws:iam::123456789012:role/FalconDiscover
output "cloudtrail_bucket_owner_id" {
  value = var.CloudTrailS3BucketAccountNumber
}
output "cloudtrail_bucket_region" {
  value = var.aws_region
}

output "external_id" {
  value = var.ExternalID
}

output "iam_role_arn" {
  value = aws_iam_role.CrowdStrike_Discover_Role.arn
}
output "id" {
  value = var.aws_local_account
}
