resource "aws_iam_role" "instance" {
  name = "${var.name_prefix}-ec2-ssm"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.name_prefix}-ec2-ssm"
  role = aws_iam_role.instance.name
}

# S3 read/write on the sensor bucket — instance pulls the sensor RPM on first boot.
resource "aws_iam_role_policy" "instance_s3" {
  name = "${var.name_prefix}-s3-sensor"
  role = aws_iam_role.instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetBucketLocation"]
        Resource = local.bucket_arn
      },
      {
        Sid      = "ReadWriteObjects"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${local.bucket_arn}/*"
      },
    ]
  })
}

# SSM Parameter Store reads — instance pulls the Falcon CID + cloud at first boot.
# kms:Decrypt covers the default SSM-managed KMS key for SecureString parameters.
resource "aws_iam_role_policy" "instance_ssm_params" {
  name = "${var.name_prefix}-ssm-params"
  role = aws_iam_role.instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadFalconParams"
        Effect = "Allow"
        Action = ["ssm:GetParameter", "ssm:GetParameters"]
        Resource = [
          aws_ssm_parameter.falcon_cid.arn,
          aws_ssm_parameter.falcon_cloud.arn,
        ]
      },
      {
        Sid      = "DecryptSecureString"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ssm.${var.region}.amazonaws.com"
          }
        }
      },
    ]
  })
}
