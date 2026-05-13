output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "subnet_ids" {
  description = "Private subnet IDs keyed by AZ. Each subnet holds an interface endpoint ENI."
  value       = { for az, s in aws_subnet.private : az => s.id }
}

output "instance_ids" {
  description = "EC2 sensor host IDs."
  value       = aws_instance.this[*].id
}

output "instance_private_ips" {
  description = "Private IPs of all sensor hosts."
  value       = aws_instance.this[*].private_ip
}

output "ssm_start_session_commands" {
  description = "Copy-paste commands to open an SSM Session Manager shell to each host."
  value       = [for id in aws_instance.this[*].id : "aws ssm start-session --region ${var.region} --target ${id}"]
}

output "verification_commands" {
  description = "Commands to run on each host (inside the SSM session) to verify sensor registration."
  value = [
    "# 1. DNS resolution — must return a VPC-local IP (10.x.x.x) from the PHZ",
    "nslookup ts01-${local.slug}.cloudsink.net",
    "",
    "# 2. TLS handshake over PrivateLink",
    "curl -v https://ts01-${local.slug}.cloudsink.net:443 2>&1 | head -20",
    "",
    "# 3. Sensor AID (populated within ~2-5 min of first boot)",
    "sudo /opt/CrowdStrike/falconctl -g --aid",
    "",
    "# 4. Sensor service status",
    "sudo systemctl status falcon-sensor --no-pager",
    "",
    "# 5. Bootstrap log (full install trace)",
    "sudo cat /var/log/falcon-bootstrap.log",
  ]
}

output "crowdstrike_endpoint_dns" {
  description = "DNS names assigned to each CrowdStrike PrivateLink endpoint."
  value = {
    for k, ep in aws_vpc_endpoint.crowdstrike :
    k => ep.dns_entry
  }
}

output "sensor_bucket" {
  description = "S3 bucket holding the Falcon sensor RPM. Reachable from hosts via the S3 gateway endpoint."
  value       = nonsensitive(local.bucket_name)
}

output "falcon_cloud" {
  description = "CrowdStrike cloud the sensor is configured to register with."
  value       = var.falcon_cloud
}

output "ami_id" {
  description = "AMI ID launched for all sensor hosts. Either the customer-pinned var.ami_id or the latest AL2023 kernel-default AMI resolved via SSM at apply time."
  value       = nonsensitive(local.resolved_ami_id)
}
