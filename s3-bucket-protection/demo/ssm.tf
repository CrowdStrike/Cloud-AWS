resource "aws_ssm_parameter" "bucket_scan_client_id" {
	name = "${var.unique_id}_${var.ssm_param_client_id}"
	description = "Falcon client ID used by the Falcon X bucket scan service application."
	type = "SecureString"
	value = var.falcon_client_id
    overwrite = true
}
resource "aws_ssm_parameter" "bucket_scan_client_secret" {
	name = "${var.unique_id}_${var.ssm_param_client_secret}"
	description = "Falcon client secret used by the Falcon X bucket scan service application."
	type = "SecureString"
	value = var.falcon_client_secret
    overwrite = true
}
