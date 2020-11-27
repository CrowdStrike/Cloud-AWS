resource "aws_iam_role" "fig_instance_role" {
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

resource "aws_iam_policy_attachment" "fig_policy_attach1" {
	name = "fig-policy-attachment1"
	roles = [aws_iam_role.fig_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonSQSFullAccess.arn
}

resource "aws_iam_policy_attachment" "fig_policy_attach2" {
	name = "fig-policy-attachment2"
	roles = [aws_iam_role.fig_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonEC2RoleforSSM.arn
}

resource "aws_iam_policy_attachment" "fig_policy_attach3" {
	name = "fig-policy-attachment3"
	roles = [aws_iam_role.fig_instance_role.name]
	policy_arn = data.aws_iam_policy.AmazonSSMManagedInstanceCore.arn
}

resource "aws_iam_instance_profile" "fig_profile" {
	name = "fig_profile"
	role = aws_iam_role.fig_instance_role.name
}

resource "aws_instance" "fig_instance" {
	ami = var.ami_id
	instance_type = var.instance_type
	key_name = var.key_name
	vpc_security_group_ids = var.vpc_security_groups
	subnet_id = var.subnet_id
	iam_instance_profile = aws_iam_instance_profile.fig_profile.name
	user_data = <<-EOF
		#!/bin/bash
		cd /var/tmp
		wget -O fig-2.0.latest-install.run https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Falcon-Integration-Gateway/install/fig-2.0.latest-install.run
		chmod 755 fig-2.0.latest-install.run
		./fig-2.0.latest-install.run --target /usr/share/fig
		EOF

 tags = {
	Name = var.instance_name
  }
}
