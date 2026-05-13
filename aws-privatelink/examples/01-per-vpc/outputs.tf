output "deployment" {
  description = "Everything you need to SSM into, verify, and operate the stack."
  value = {
    region                     = var.region
    instance_ids               = module.privatelink.instance_ids
    ami_id                     = module.privatelink.ami_id
    sensor_bucket              = module.privatelink.sensor_bucket
    ssm_start_session_commands = module.privatelink.ssm_start_session_commands
    verification_commands      = module.privatelink.verification_commands
    crowdstrike_endpoint_dns   = module.privatelink.crowdstrike_endpoint_dns
  }
}

output "falcon_cloud" {
  description = "Falcon cloud the deployment is registered against."
  value       = var.falcon_cloud
}
