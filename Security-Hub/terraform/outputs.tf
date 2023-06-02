# Output the public IP address of the instance
output "public_ip" {
  value = aws_instance.sechub_instance.public_ip
}
