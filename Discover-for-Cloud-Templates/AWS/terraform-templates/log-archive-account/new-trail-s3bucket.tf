//
provider "aws" {
  version = "~> 2.0"
  region = var.aws_region
}

//
resource "aws_s3_bucket" "CloudTrail_bucket" {
  bucket = var.CloudTrailS3BucketName
  acl = "bucket-owner-full-control"
  force_destroy = true
  policy = data.aws_iam_policy_document.s3BucketACLPolicy.json

  region = var.aws_region

  lifecycle_rule {
    id = "bucketlifecycle"
    enabled = true
    expiration {
      days = var.CloudTrailS3LogExpiration
    }
  }
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.CloudTrail_bucket.id

  topic {
    //    Crowdstrike hosts topics in most region has a topic as SNS cannot send notifications across regions
    //    All topics are in account 292230061137 which is set in ${var.CSAccountNumber}
    topic_arn = "arn:aws:sns:${var.aws_region}:${var.CSAccountNumber}:cs-cloudconnect-aws-cloudtrail"
    events = [
      "s3:ObjectCreated:Put"]
  }
}


data "aws_iam_policy_document" "s3BucketACLPolicy" {
  statement {

    sid = "AWSCloudTrailAclCheck20150319"
    effect = "Allow"
    actions = [
      "s3:GetBucketAcl"
    ]
    principals {
      type = "Service"
      identifiers = [
        "cloudtrail.amazonaws.com"]
    }
    resources = [
      "arn:aws:s3:::${var.CloudTrailS3BucketName}"
    ]
  }
  statement {

    sid = "AWSCloudTrailWrite20150319"
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    principals {
      type = "Service"
      identifiers = [
        "cloudtrail.amazonaws.com"]
    }
    resources = [
      "arn:aws:s3:::${var.CloudTrailS3BucketName}/AWSLogs/*/*",
    ]
    condition {
      test = "StringEquals"
      variable = "s3:x-amz-acl"

      values = [
        "bucket-owner-full-control"
      ]
    }
  }
}

//

resource "aws_iam_policy" "ReadS3CloudTrailFiles" {
  name = "iamPolicyFalconDiscoverAccess"
  description = "S3 access policy for role assumed by Falcon Discover"
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
      test = "StringEquals"
      variable = "sts:ExternalId"

      values = [
        var.ExternalID
      ]
    }
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
    resources = [
      "*"]
  }
}

resource "aws_iam_policy" "DescribeAPICallsRolePolicy" {
  name = "DescribeAPICallsRolePolicy"
  path = "/"
  policy = data.aws_iam_policy_document.DescribeAPICalls.json
}

resource "aws_iam_role" "iamRole" {
  name = var.RoleName
  description = "Role assumed by Falcon Discover to read logs from S3"
  path = "/"
  assume_role_policy = data.aws_iam_policy_document.FalconAssumeRolePolicyDocument.json
}

resource "aws_iam_role_policy_attachment" "iamPolicyDescribeAPICallsAttach" {
  role = aws_iam_role.iamRole.name
  policy_arn = aws_iam_policy.DescribeAPICallsRolePolicy.arn
}

resource "aws_iam_role_policy_attachment" "iamPolicyCloudTrailS3AccessAttach" {
  role = aws_iam_role.iamRole.name
  policy_arn = aws_iam_policy.ReadS3CloudTrailFiles.arn
}

resource "aws_cloudtrail" "crwd_trail" {
  name = var.CloudTrailName
  depends_on = [
    aws_s3_bucket.CloudTrail_bucket]
  event_selector {
    read_write_type = "WriteOnly"
    include_management_events = true
  }
  include_global_service_events = true
  enable_logging = true
  is_multi_region_trail = true
  s3_bucket_name = var.CloudTrailS3BucketName
}

//
// Outputs are the inputs for "register_account.py"
//
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
