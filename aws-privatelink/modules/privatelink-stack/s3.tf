data "aws_caller_identity" "current" {}

resource "random_string" "bucket_suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  create_bucket = var.sensor_bucket_name == null
  bucket_name   = var.sensor_bucket_name != null ? var.sensor_bucket_name : "${var.name_prefix}-sensor-${data.aws_caller_identity.current.account_id}-${random_string.bucket_suffix.result}"
  bucket_arn    = var.sensor_bucket_name != null ? "arn:aws:s3:::${var.sensor_bucket_name}" : aws_s3_bucket.sensor[0].arn

  sensor_rpm_key = "falcon-sensor.rpm"
}

resource "aws_s3_bucket" "sensor" {
  count  = local.create_bucket ? 1 : 0
  bucket = local.bucket_name

  force_destroy = true

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "sensor" {
  count  = local.create_bucket ? 1 : 0
  bucket = aws_s3_bucket.sensor[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sensor" {
  count  = local.create_bucket ? 1 : 0
  bucket = aws_s3_bucket.sensor[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "sensor_rpm" {
  bucket = local.bucket_name
  key    = local.sensor_rpm_key
  source = var.sensor_rpm_path
  etag   = filemd5(var.sensor_rpm_path)

  depends_on = [aws_s3_bucket.sensor]
}
