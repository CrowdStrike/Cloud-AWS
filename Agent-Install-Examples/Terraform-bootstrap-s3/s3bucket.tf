# Create a BootStrap S3 Bucket


resource "aws_s3_bucket" "sensor-file-bucket" {
  #bucket_prefix = "${var.bucket_prefix}"
  #bucket        = "sec-frame-jenkins-${lower(random_id.bucket_prefix.hex)}"
  bucket = var.bucket_name
  acl = "private"
  force_destroy = true
}

resource "aws_s3_bucket_object" "sensor-file" {
  depends_on = [
    aws_s3_bucket.sensor-file-bucket]
  bucket = var.bucket_name
  acl = "private"
  key = "sensor/${var.crwd_sensor}"
  source = "bootstrap/${var.crwd_sensor}"
}

resource "aws_s3_bucket_policy" "sensor-bucket-policy" {
  bucket = aws_s3_bucket.sensor-file-bucket.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "MYBUCKETPOLICY",
  "Statement": [
    {
      "Sid": "IPAllow",
      "Effect": "Allow",

      "Principal": {

                "AWS": "${aws_iam_role.workload-role.arn}"
            },
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.sensor-file-bucket.bucket}/*"

    }
  ]
}
POLICY
}