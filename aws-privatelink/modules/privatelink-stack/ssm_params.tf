resource "aws_ssm_parameter" "falcon_cid" {
  name        = "/${var.name_prefix}/falcon/cid"
  description = "CrowdStrike Falcon CCID. Read by the sensor host at first boot to register with the correct tenant."
  type        = "SecureString"
  value       = var.falcon_cid
  overwrite   = true
  tier        = "Standard"
}

resource "aws_ssm_parameter" "falcon_cloud" {
  name        = "/${var.name_prefix}/falcon/cloud"
  description = "CrowdStrike cloud (us-1, us-2, eu-1). Passed to falconctl -s --cloud=... at first boot."
  type        = "String"
  value       = var.falcon_cloud
  overwrite   = true
}
