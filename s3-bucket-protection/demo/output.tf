output "demo_bucket" {
	value = "s3://${aws_s3_bucket.bucket.id}"
}
output "demo_instance" {
	value = "ec2-user@${aws_instance.amzn_instance.public_ip}"
}