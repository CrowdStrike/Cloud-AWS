data "aws_ssm_parameter" "al2023_ami" {
  # Default AMI source: AWS's public SSM parameter for the latest Amazon
  # Linux 2023 kernel-default AMI in this region, per-arch. AWS updates
  # this pointer whenever they publish a new AL2023 image, so we always
  # get the current one at plan time. Skipped when var.ami_id is pinned.
  count = var.ami_id == null ? 1 : 0
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-${var.sensor_architecture}"
}

locals {
  resolved_ami_id = var.ami_id != null ? var.ami_id : data.aws_ssm_parameter.al2023_ami[0].value

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    bucket         = local.bucket_name
    sensor_rpm_key = local.sensor_rpm_key
    ssm_cid_name   = aws_ssm_parameter.falcon_cid.name
    ssm_cloud_name = aws_ssm_parameter.falcon_cloud.name
    region         = var.region
  })
}

resource "aws_instance" "this" {
  count = var.instance_count

  ami                         = local.resolved_ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.private[var.availability_zones[0]].id
  vpc_security_group_ids      = [aws_security_group.instance.id]
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  key_name                    = var.key_name
  associate_public_ip_address = false

  user_data                   = local.user_data
  user_data_replace_on_change = true

  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 2
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  # Keep existing instances stable if the SSM parameter advances to a newer AMI.
  lifecycle {
    ignore_changes = [ami]
  }

  tags = {
    Name = "${var.name_prefix}-sensor-host-${count.index}"
  }

  depends_on = [
    aws_vpc_endpoint.s3,
    aws_vpc_endpoint.ssm,
    aws_vpc_endpoint.crowdstrike,
    aws_s3_object.sensor_rpm,
    aws_ssm_parameter.falcon_cid,
    aws_ssm_parameter.falcon_cloud,
    aws_iam_role_policy.instance_s3,
    aws_iam_role_policy.instance_ssm_params,
  ]
}
