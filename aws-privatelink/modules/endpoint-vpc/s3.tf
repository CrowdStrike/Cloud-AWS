data "aws_caller_identity" "current" {}

resource "random_string" "bucket_suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  bucket_name    = "${var.name_prefix}-sensor-${data.aws_caller_identity.current.account_id}-${random_string.bucket_suffix.result}"
  sensor_rpm_key = "falcon-sensor.rpm"
}

resource "aws_s3_bucket" "sensor" {
  bucket = local.bucket_name

  force_destroy = true

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "sensor" {
  bucket = aws_s3_bucket.sensor.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sensor" {
  bucket = aws_s3_bucket.sensor.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "sensor_rpm" {
  bucket = aws_s3_bucket.sensor.id
  key    = local.sensor_rpm_key
  source = var.sensor_rpm_path
  etag   = filemd5(var.sensor_rpm_path)
}

data "aws_iam_policy_document" "sensor_bucket" {
  count = length(var.authorized_role_arns) > 0 ? 1 : 0

  statement {
    sid    = "AllowConsumerRolesToReadRpm"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.authorized_role_arns
    }

    actions = [
      "s3:GetObject",
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.sensor.arn,
      "${aws_s3_bucket.sensor.arn}/*",
    ]
  }
}

resource "aws_s3_bucket_policy" "sensor" {
  count = length(var.authorized_role_arns) > 0 ? 1 : 0

  bucket = aws_s3_bucket.sensor.id
  policy = data.aws_iam_policy_document.sensor_bucket[0].json
}
