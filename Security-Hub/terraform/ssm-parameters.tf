resource "aws_ssm_parameter" "sechub_falcon_client_id" {
	name = "FIG_FALCON_CLIENT_ID"
	description = "Falcon client ID used by the Security Hub integration service application."
	type = "SecureString"
	value = var.falcon_client_id
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_falcon_client_secret" {
	name = "FIG_FALCON_CLIENT_SECRET"
	description = "Falcon client secret used by the Security Hub integration service application."
	type = "SecureString"
	value = var.falcon_client_secret
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_app_id" {
	name = "FIG_APP_ID"
	description = "Application ID used to connect to the event stream."
	type = "String"
	value = var.app_id
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_severity_threshold" {
	name = "FIG_SEVERITY_THRESHOLD"
	description = "Severity threshold to meet before submitting a detection."
	type = "String"
	value = var.severity_threshold
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_sqs_queue_name" {
	name = "FIG_SQS_QUEUE_NAME"
	description = "Name of the SQS queue used by the Security Hub integration service application."
	type = "String"
	value = var.sqs_queue_name
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_ssl_verify" {
	name = "FIG_SSL_VERIFY"
	description = "Enable / Disable SSL verification boolean"
	type = "String"
	value = var.ssl_verify
	overwrite = true
}

resource "aws_ssm_parameter" "sechub_base_url" {
	name = "FIG_API_BASE_URL"
	description = "CrowdStrike Base URL"
	type = "String"
	value = var.base_url
	overwrite = true
}