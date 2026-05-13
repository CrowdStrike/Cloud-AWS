output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "subnet_ids" {
  description = "Private subnet IDs keyed by AZ. Each subnet holds an interface endpoint ENI. Consumer workloads launch ENIs here too (via the RAM share when enabled)."
  value       = { for az, s in aws_subnet.private : az => s.id }
}

output "subnet_ids_list" {
  description = "Private subnet IDs as an ordered list (same order as var.availability_zones). Convenience for consumers that want a flat list."
  value       = [for az in var.availability_zones : aws_subnet.private[az].id]
}

output "phz_id" {
  description = "Zone ID of the cloudsink.net PHZ. Attached to this VPC; consumers inherit it via the shared subnets."
  value       = aws_route53_zone.cloudsink.zone_id
}

output "route_table_id" {
  description = "Route table ID for the private subnets. Exposed so the TGW topology (03) can add a spoke-CIDR route pointing at its TGW attachment."
  value       = aws_route_table.private.id
}

output "endpoints_sg_id" {
  description = "Security group ID on all interface endpoints. Consumer SGs must be listed in var.consumer_sg_ids to get HTTPS ingress, and must reference this SG in their own egress rules."
  value       = aws_security_group.endpoints.id
}

output "s3_prefix_list_id" {
  description = "Prefix list ID of the S3 gateway endpoint. Consumer instance SGs reference this to allow HTTPS egress to S3 (the sensor bucket + AL2023 dnf repos)."
  value       = aws_vpc_endpoint.s3.prefix_list_id
}

output "sensor_bucket_name" {
  description = "S3 bucket holding the Falcon sensor RPM. Reachable from consumer hosts via the S3 gateway endpoint + the bucket policy (cross-account) or the consumer's IAM role (same-account)."
  value       = aws_s3_bucket.sensor.bucket
}

output "sensor_bucket_arn" {
  description = "ARN of the sensor bucket."
  value       = aws_s3_bucket.sensor.arn
}

output "sensor_bucket_rpm_key" {
  description = "S3 key of the uploaded sensor RPM object inside the sensor bucket."
  value       = aws_s3_object.sensor_rpm.key
}

output "crowdstrike_endpoint_dns" {
  description = "DNS names assigned to each CrowdStrike PrivateLink endpoint. Diagnostic output — consumer workloads use the PHZ aliases instead."
  value = {
    for k, ep in aws_vpc_endpoint.crowdstrike :
    k => ep.dns_entry
  }
}

output "falcon_cloud" {
  description = "CrowdStrike cloud this endpoint VPC targets. Consumers must pass the same value to sensor-host so SSM params + user_data line up."
  value       = var.falcon_cloud
}
