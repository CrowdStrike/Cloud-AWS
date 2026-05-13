output "instance_ids" {
  description = "EC2 sensor host IDs."
  value       = aws_instance.this[*].id
}

output "instance_private_ips" {
  description = "Private IPs of all sensor hosts."
  value       = aws_instance.this[*].private_ip
}

output "instance_sg_id" {
  description = "Security group ID attached to the sensor host(s). Pass this to endpoint-vpc.consumer_sg_ids so the endpoints SG lets HTTPS ingress through from here."
  value       = aws_security_group.instance.id
}

output "instance_role_arn" {
  description = "IAM role ARN attached to the sensor host(s) via the instance profile. Pass this to endpoint-vpc.authorized_role_arns to grant cross-account read on the sensor bucket."
  value       = aws_iam_role.instance.arn
}

output "ssm_start_session_commands" {
  description = "Copy-paste commands to open an SSM Session Manager shell to each host. Prepend --profile <workload_profile> when the host is in a different account from the shell's default profile."
  value       = [for id in aws_instance.this[*].id : "aws ssm start-session --region ${var.region} --target ${id}"]
}

output "verification_commands" {
  description = "Commands to run on each host (inside the SSM session) to verify sensor registration."
  value = [
    "# 1. DNS resolution — must return a VPC-local IP from the PHZ",
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

output "ami_id" {
  description = "AMI ID launched for all sensor hosts. Either the caller-pinned var.ami_id or the latest AL2023 kernel-default AMI resolved via SSM at apply time."
  value       = nonsensitive(local.resolved_ami_id)
}
