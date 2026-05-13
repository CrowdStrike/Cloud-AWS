data "aws_caller_identity" "current" {}

locals {
  sensor_bucket_arn = "arn:aws:s3:::${var.sensor_bucket_name}"

  cloud_hostname_slugs = {
    "us-1" = "b"
    "us-2" = "gyr-maverick"
    "eu-1" = "lanner-lion"
  }
  slug = local.cloud_hostname_slugs[var.falcon_cloud]
}
