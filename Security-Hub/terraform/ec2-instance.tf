data "aws_ami" "amazon-linux-2" {
 most_recent = true
 owners = ["amazon"]

 filter {
   name   = "owner-alias"
   values = ["amazon"]
 }

 filter {
   name   = "name"
   values = ["amzn2-ami-hvm*"]
 }
}

resource "aws_iam_role" "sechub_instance_role" {
	name = var.iam_role_name
	assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "aws_iam_policy" "AmazonSQSFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

data "aws_iam_policy" "AmazonEC2RoleforSSM" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
}

data "aws_iam_policy" "AmazonSSMManagedInstanceCore" {
  arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_policy_attachment" "sechub_policy_attach1" {
	name = "cs_sechub_int-policy-attachment1"
	roles = [aws_iam_role.sechub_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonSQSFullAccess.arn
}

resource "aws_iam_policy_attachment" "sechub_policy_attach2" {
	name = "cs_sechub_int-policy-attachment2"
	roles = [aws_iam_role.sechub_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonEC2RoleforSSM.arn
}

resource "aws_iam_policy_attachment" "sechub_policy_attach3" {
	name = "cs_sechub_int-policy-attachment3"
	roles = [aws_iam_role.sechub_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonSSMManagedInstanceCore.arn
}

resource "aws_iam_instance_profile" "sechub_profile" {
	name = "cs_sechub_int_mssp_profile"
	role = aws_iam_role.sechub_instance_role.name
}

resource "aws_instance" "sechub_instance" {
	ami = data.aws_ami.amazon-linux-2.id
	instance_type = var.instance_type
	key_name = var.key_name
	vpc_security_group_ids = [aws_security_group.sg_22.id]
	subnet_id = aws_subnet.subnet_public.id
	iam_instance_profile = aws_iam_instance_profile.sechub_profile.name
	user_data = <<-EOF
		#!/bin/bash
		cd /var/tmp
		wget -O sechub-2.0.latest-install.run https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Security-Hub/install/sechub-2.0.latest-install.run
		chmod 755 sechub-2.0.latest-install.run
		./sechub-2.0.latest-install.run --target /usr/share/fig
		EOF

 tags = {
	Name = var.instance_name
  }
}
