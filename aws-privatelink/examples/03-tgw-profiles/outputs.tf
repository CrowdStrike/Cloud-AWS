output "deployment" {
  description = "Everything you need to SSM into, verify, and operate the stack. SSM commands target the spoke account — prepend --profile $spoke_profile on the workstation."
  value = {
    region                     = var.region
    hub_profile                = var.hub_profile
    spoke_profile              = var.spoke_profile
    spoke_account_id           = var.spoke_account_id
    hub_vpc_id                 = module.endpoint_vpc.vpc_id
    spoke_vpc_id               = aws_vpc.spoke.id
    tgw_id                     = aws_ec2_transit_gateway.this.id
    profile_id                 = aws_route53profiles_profile.cloudsink.id
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
