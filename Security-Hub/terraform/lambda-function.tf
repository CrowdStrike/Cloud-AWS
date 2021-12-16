resource "aws_iam_role" "sechub_lambda_role" {
  name = "${var.lambda_function_name}_execution_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "sechub_lambda_execution_policy_document" {
    statement {
        actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        effect = "Allow"
        resources = ["arn:aws:logs:::log-group:/aws/lambda/${var.lambda_function_name}:*"]
    }
}

data "aws_iam_policy_document" "sechub_lambda_securityhub_policy_document" {
    statement {
        actions = ["securityhub:*"]
        effect = "Allow"
        resources = [
            "arn:aws:securityhub:*:*:hub/default", 
            "arn:aws:securityhub:*:*:product/crowdstrike/crowdstrike-falcon",
            "arn:aws:securityhub:*:*:/findings"  
        ]
    }
}

data "aws_iam_policy_document" "sechub_lambda_ec2_policy_document" {
    statement {
        actions = ["ec2:Describe*"]
        effect = "Allow"
        resources = ["*"]
    }
}
data "aws_iam_policy" "AmazonEC2ReadOnlyAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

data "aws_iam_policy" "AWSLambdaSQSQueueExecutionRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_iam_policy" "sechub_lambda_execution_policy" {
  name        = "${var.lambda_function_name}_execution_policy_mssp"
  policy      = data.aws_iam_policy_document.sechub_lambda_execution_policy_document.json
}

resource "aws_iam_policy" "sechub_lambda_securityhub_policy" {
  name        = "${var.lambda_function_name}_securityhub_policy_mssp"
  policy      = data.aws_iam_policy_document.sechub_lambda_securityhub_policy_document.json
}

resource "aws_iam_policy" "sechub_lambda_ec2_policy" {
  name        = "${var.lambda_function_name}_ec2_policy_mssp"
  policy      = data.aws_iam_policy_document.sechub_lambda_ec2_policy_document.json
}

resource "aws_iam_policy_attachment" "sechub_lambda_policy_attach1" {
	name = "sechub-policy-attachment1"
	roles = [aws_iam_role.sechub_lambda_role.name]
	policy_arn = data.aws_iam_policy.AmazonEC2ReadOnlyAccess.arn
}

resource "aws_iam_policy_attachment" "sechub_lambda_policy_attach2" {
	name = "sechub-policy-attachment2"
	roles = [aws_iam_role.sechub_lambda_role.name]
	policy_arn = data.aws_iam_policy.AWSLambdaSQSQueueExecutionRole.arn
}

resource "aws_iam_policy_attachment" "sechub_lambda_policy_attach3" {
	name = "sechub-policy-attachment3"
	roles = [aws_iam_role.sechub_lambda_role.name]
	policy_arn = aws_iam_policy.sechub_lambda_execution_policy.arn
}

resource "aws_iam_policy_attachment" "sechub_lambda_policy_attach4" {
	name = "sechub-policy-attachment4"
	roles = [aws_iam_role.sechub_lambda_role.name]
	policy_arn = aws_iam_policy.sechub_lambda_securityhub_policy.arn
}

resource "aws_iam_policy_attachment" "sechub_lambda_policy_attach5" {
	name = "sechub-policy-attachment5"
	roles = [aws_iam_role.sechub_lambda_role.name]
	policy_arn = aws_iam_policy.sechub_lambda_ec2_policy.arn
}

resource "aws_lambda_function" "sechub_example_lambda" {
  function_name = var.lambda_function_name
  handler = "main.lambda_handler"
  role = aws_iam_role.sechub_lambda_role.arn
  runtime = "python3.7"

  filename = var.lambda_filename
  source_code_hash = filesha256(var.lambda_filename)

  timeout = 30
  memory_size = 128

  environment {
      variables = {
          DEBUG = "False"
          CONFIRM_INSTANCES = "True"
      }
  }
}
