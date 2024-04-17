locals {
  bucket_arns = [for bucket in data.aws_s3_bucket.bucket : "${bucket.arn}/*"]
} 

data "aws_caller_identity" "current" {}
data "aws_iam_policy" "AdministratorAccess" {
  arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
data "aws_iam_policy_document" "lambda_execution_policy_document" {
    statement {
        actions = ["logs:CreateLogGroup"]
        effect = "Allow"
        resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"]
    }
    statement {
      actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
      effect = "Allow"
      resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*"]
    }
}
data "aws_iam_policy_document" "lambda_ssm_policy_document" {
    statement {
        actions = [
            "ssm:GetParameterHistory",
            "ssm:GetParametersByPath",
            "ssm:GetParameters",
            "ssm:GetParameter"
        ]
        effect = "Allow"
        resources = [
            "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/*"
        ]
    }
}
data "aws_iam_policy_document" "lambda_s3_policy_document" {
    statement {
      actions = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:DeleteObject",
          "s3:DeleteObjectVersion"
      ]
      effect = "Allow"
      resources = local.bucket_arns
    }
}
data "aws_iam_policy_document" "lambda_securityhub_policy_document" {
    statement {
      actions = [
          "securityhub:GetFindings"
      ]
      effect = "Allow"
      resources = ["arn:aws:securityhub:${var.region}:${data.aws_caller_identity.current.account_id}:hub/default"]
    }
    statement {
        actions = [
            "securityhub:BatchImportFindings"
        ]
        effect = "Allow"
        resources = ["arn:aws:securityhub:${var.region}:517716713836:product/crowdstrike/*"]
    }
}
# data "aws_iam_policy_document" "ec2_s3_policy_document" {
#     statement {
#       actions = [
#           "s3:*"
#       ]
#       effect = "Allow"
#       resources = [data.aws_s3_bucket.bucket.arn, "${data.aws_s3_bucket.bucket.arn}/*"]
#     }
# }
resource "aws_iam_policy" "lambda_ssm_policy" {
  name        = "${var.lambda_function_name}_ssm_policy"
  policy      = data.aws_iam_policy_document.lambda_ssm_policy_document.json
}
resource "aws_iam_policy" "lambda_execution_policy" {
  name        = "${var.lambda_function_name}_execution_policy"
  policy      = data.aws_iam_policy_document.lambda_execution_policy_document.json
}
resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "${var.lambda_function_name}_s3_policy"
  policy      = data.aws_iam_policy_document.lambda_s3_policy_document.json
}
resource "aws_iam_policy" "lambda_securityhub_policy" {
  name        = "${var.lambda_function_name}_securityhub_policy"
  policy      = data.aws_iam_policy_document.lambda_securityhub_policy_document.json
}
# resource "aws_iam_policy" "ec2_s3_policy" {
#   name        = "${var.instance_name}_s3_policy"
#   policy      = data.aws_iam_policy_document.ec2_s3_policy_document.json
# }
# resource "aws_iam_policy" "ec2_securityhub_policy" {
#   name        = "${var.instance_name}_securityhub_policy"
#   policy      = data.aws_iam_policy_document.lambda_securityhub_policy_document.json
# }
resource "aws_iam_role" "iam_for_lambda" {
  name = "${var.lambda_execution_role_name}" 
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}
# resource "aws_iam_instance_profile" "ec2-ssm-role-profile" {
#   name = "${var.iam_prefix}-role-profile"
#   role = aws_iam_role.ec2-ssm-role-for-mgt.name
# }

# resource "aws_iam_role" "ec2-ssm-role-for-mgt" {
#   name = "${var.iam_prefix}-role" 
#   assume_role_policy = <<EOF
# {
#     "Version": "2012-10-17",
#     "Statement": [
#       {
#         "Effect": "Allow",
#         "Principal": {
#           "Service": "ec2.amazonaws.com"
#         },
#         "Action": "sts:AssumeRole"
#       }
#     ]
# }
# EOF
# }

# resource "aws_iam_role_policy_attachment" "ec2-ssm-role-policy" {
#   role = aws_iam_role.ec2-ssm-role-for-mgt.name
#   policy_arn = aws_iam_policy.ec2_s3_policy.arn
# }
# resource "aws_iam_policy_attachment" "ec2_securityhub_policy_attach" {
# 	name = "ec2-securityhub-policy-attachment"
# 	roles = [aws_iam_role.ec2-ssm-role-for-mgt.name]
# 	policy_arn = aws_iam_policy.ec2_securityhub_policy.arn
# }
resource "aws_iam_policy_attachment" "lambda_ssm_policy_attach" {
	name = "s3x-ssm-policy-attachment"
	roles = [aws_iam_role.iam_for_lambda.name]
	policy_arn = aws_iam_policy.lambda_ssm_policy.arn
}
resource "aws_iam_policy_attachment" "lambda_exec_policy_attach" {
	name = "s3x-lambda-exec-policy-attachment"
	roles = [aws_iam_role.iam_for_lambda.name]
	policy_arn = aws_iam_policy.lambda_execution_policy.arn
}
resource "aws_iam_policy_attachment" "lambda_s3_policy_attach" {
	name = "s3x-lambda-s3-policy-attachment"
	roles = [aws_iam_role.iam_for_lambda.name]
	policy_arn = aws_iam_policy.lambda_s3_policy.arn
}
resource "aws_iam_policy_attachment" "lambda_securityhub_policy_attach" {
	name = "s3x-lambda-securityhub-policy-attachment"
	roles = [aws_iam_role.iam_for_lambda.name]
	policy_arn = aws_iam_policy.lambda_securityhub_policy.arn
}

