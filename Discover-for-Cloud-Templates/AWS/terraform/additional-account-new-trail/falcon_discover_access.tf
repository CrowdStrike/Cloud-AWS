resource "aws_iam_role" "iamRole" {
  name = var.RoleName
  description = "Role assumed by Falcon Discover to Describe API calls"
  path = "/"
  assume_role_policy = data.aws_iam_policy_document.DescribeAPICalls.json
}

data "aws_iam_policy_document" "DescribeAPICalls" {
  statement {

    sid = "FalconDescribeAPICalls"
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
    resources = [
      "*"]
  }
}

data "aws_iam_policy_document" "FalconAssumeRolePolicyDocument" {
  statement {

    sid = "AWSCloudTrailAclCheck20150319"
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
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

resource "aws_iam_role" "iamRole" {
  name = "FalconDiscoverS3AccessRole"
  description = "Role assumed by Falcon Discover to read logs from S3"
  path = "/"
  assume_role_policy = data.aws_iam_policy_document.FalconAssumeRolePolicyDocument.json
}


resource "aws_iam_policy" "DescribeAPICallsRolePolicy" {
  name = "DescribeAPICallsRolePolicy"
  path = "/"
  policy = data.aws_iam_policy_document.DescribeAPICalls.json
}


resource "aws_iam_role_policy_attachment" "iamPolicyDescribeAPICallsAttach" {
  role = aws_iam_role.iamRole.name
  policy_arn = aws_iam_policy.DescribeAPICallsRolePolicy.arn
}


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
  value = aws_iam_role.iamRole.arn
}
output "id" {
  value = var.aws_local_account
}
