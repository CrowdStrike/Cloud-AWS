output "deployment" {
  description = "Everything you need to SSM into, verify, and operate the stack."
  value = {
    region                     = var.region
    environment                = var.environment
    instance_ids               = module.sensor_host.instance_ids
    ami_id                     = module.sensor_host.ami_id
    sensor_bucket              = module.endpoint_vpc.sensor_bucket_name
    ssm_start_session_commands = module.sensor_host.ssm_start_session_commands
    verification_commands      = module.sensor_host.verification_commands
    crowdstrike_endpoint_dns   = module.endpoint_vpc.crowdstrike_endpoint_dns
  }
}

output "falcon_cloud" {
  description = "Falcon cloud the deployment is registered against."
  value       = var.falcon_cloud
}
