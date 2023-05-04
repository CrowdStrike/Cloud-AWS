resource "null_resource" "archive_delay" {
    triggers = {
        index = "${filebase64sha256("${path.cwd}/lambda/${var.falconpy_layer_filename}")}"
    }
}

locals {
    archive_delay_id = "${null_resource.archive_delay.id}"
    source_dir = "${path.cwd}/lambda"
}

# Package archive
data "archive_file" "lambda_archive" {
  type        = "zip"
  output_path = "${path.cwd}/lambda/${var.lambda_function_filename}"
  source_dir  = "${local.source_dir}"
  excludes = [
    var.falconpy_layer_filename,
    "s3-bucket-protection.zip",
    var.lambda_function_filename
    ]
}
variable "python_tools_layer_name" {
    type = string
    default = "AWSLambdaPowertoolsPythonV2"
}
data "aws_lambda_layer_version" "pythontools" {
    layer_name = "arn:aws:lambda:${var.region}:017000801446:layer:${var.python_tools_layer_name}"
    version = 30
}

resource "aws_lambda_layer_version" "falconpy" {
  filename      = "${path.cwd}/lambda/${var.falconpy_layer_filename}"
  layer_name    = "${var.unique_id}_${var.falconpy_layer_name}"
  compatible_runtimes = ["python3.10"]
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.func.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bucket.arn
}

resource "aws_lambda_function" "func" {
  filename      = "${path.cwd}/lambda/${var.lambda_function_filename}"
  function_name = "${var.unique_id}_${var.lambda_function_name}"
  description   = var.lambda_description
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "lambda_function.lambda_handler"
  layers        = [data.aws_lambda_layer_version.pythontools.arn, aws_lambda_layer_version.falconpy.arn]
  runtime       = "python3.10"
  timeout       = 30
  depends_on = [data.archive_file.lambda_archive]
  environment {
    variables = {
        "CLIENT_ID_PARAM" = "${var.unique_id}_${var.ssm_param_client_id}"
        "CLIENT_SECRET_PARAM" = "${var.unique_id}_${var.ssm_param_client_secret}"
        "BASE_URL" = "${var.base_url}"
        "MITIGATE_THREATS" = "${var.lambda_mitigate_threats}"
    }
  }
}

