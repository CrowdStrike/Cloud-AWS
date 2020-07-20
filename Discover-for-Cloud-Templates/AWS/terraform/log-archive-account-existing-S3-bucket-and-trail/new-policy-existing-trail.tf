//
provider "aws" {
  version = "~> 2.0"
  region  = var.aws_region
}


//
// Add the bucket notification to the existing log archive bucket
//
//resource "aws_s3_bucket_notification" "bucket_notification" {
//  bucket = aws_s3_bucket.CloudTrail_bucket.id
//
//  topic {
//    topic_arn = "arn:aws:sns:${var.aws_region}:${var.CSAccountNumber}:cs-cloudconnect-aws-cloudtrail"
//    events        = ["s3:ObjectCreated:Put"]
//  }
//}



resource "aws_iam_policy" "ReadS3CloudTrailFiles" {
  name                          = "iamPolicyFalconDiscoverAccess"
  description                   = "S3 access policy for role assumed by Falcon Discover"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
              "Action": [
                "s3:GetObject"

              ],
              "Effect": "Allow",
              "Resource": "arn:aws:s3:::${var.CloudTrailS3BucketName}/*",
              "Sid": ""
            }
  ]
}
EOF
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
      test     = "StringEquals"
      variable = "sts:ExternalId"

      values = [
        var.ExternalID
      ]
    }
//    resources = [
//      "arn:aws:s3:::${var.CloudTrailS3BucketName}"
//    ]
  }
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
      resources = ["*"]
  }
    }

resource "aws_iam_policy" "DescribeAPICallsRolePolicy" {
  name   = "DescribeAPICallsRolePolicy"
  path   = "/"
  policy = data.aws_iam_policy_document.DescribeAPICalls.json
}

resource "aws_iam_role" "iamRole" {
  name = var.RoleName
  description                   = "Role assumed by Falcon Discover to read logs from S3"
  path = "/"
  assume_role_policy = data.aws_iam_policy_document.FalconAssumeRolePolicyDocument.json
}

resource "aws_iam_role_policy_attachment" "iamPolicyDescribeAPICallsAttach" {
  role                      = aws_iam_role.iamRole.name
  policy_arn                = aws_iam_policy.DescribeAPICallsRolePolicy.arn
}

resource "aws_iam_role_policy_attachment" "iamPolicyCloudTrailS3AccessAttach" {
  role                      = aws_iam_role.iamRole.name
  policy_arn                = aws_iam_policy.ReadS3CloudTrailFiles.arn
}



output "cloudtrail_bucket_owner_id" {
  value = var.aws_local_account
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
output "local_account" {
  value = var.aws_local_account
}
