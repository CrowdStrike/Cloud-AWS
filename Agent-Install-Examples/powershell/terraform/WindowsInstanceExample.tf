provider "aws" {
        region = var.region
}

variable "region" {
        type = string
        default = "AWS_REGION_NAME_HERE"
}

variable "instance_name" {
	type = string
	default = "WindowsInstanceExample"
}

variable "security_group_name" {
    type = string
    default = "WindowsExampleSecurityGroup"
}
variable "instance_type" {
	type = string
	default = "AWS_INSTANCE_SIZE_HERE"
}

variable "key_name" {
	type = string
	default = "KEY_PAIR_NAME_HERE"
}

variable "subnet_id" {
	type = string
	default = "SUBNET_ID_HERE"
}

variable "client_id_ssm_name" {
	type = string
	default = "CLIENT_ID_SSM_PARAMETER_NAME_HERE"
}

variable "client_secret_ssm_name" {
	type = string
	default = "CLIENT_SECRET_SSM_PARAMETER_NAME_HERE"
}

variable "trusted_ip" {
    type = string
    default = "IP_ADDRESS_HERE/32"
}

variable "vpc_id"{
    type = string
    default = "VPC_ID_HERE"
}

#### EDITS SHOULD NOT BE REQUIRED BELOW THIS LINE
data "aws_ami" "windows"{
    most_recent = true
    owners = ["801119661308"]
    filter {
        name = "name"
        values = ["Windows_Server-2019-English-Full-Base-*"]
    }
    filter {
        name = "virtualization-type"
        values = ["hvm"]
    }
}

data "aws_ssm_parameter" "falcon_client_id" {
    name = var.client_id_ssm_name
}

data "aws_ssm_parameter" "falcon_client_secret" {
    name = var.client_secret_ssm_name
}

resource "aws_security_group" "windows_example_security_group" {
    name = var.security_group_name
    description = "Allowed RDP traffic from trusted IP"
    vpc_id = var.vpc_id
    ingress {
        from_port = 3389
        to_port = 3389
        protocol = "tcp"
        cidr_blocks = [var.trusted_ip]
    }
    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }    
}

resource "aws_instance" "windows_example_instance" {
	ami = data.aws_ami.windows.id
	instance_type = var.instance_type
	key_name = var.key_name
	vpc_security_group_ids = [aws_security_group.windows_example_security_group.id]
	subnet_id = var.subnet_id
    user_data = <<EOF
<powershell>
$client = new-object System.Net.WebClient
$client.DownloadFile("https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/powershell/sensor_install.ps1","C:\Windows\Temp\sensor.ps1")
C:\Windows\Temp\sensor.ps1 ${data.aws_ssm_parameter.falcon_client_id.value} ${data.aws_ssm_parameter.falcon_client_secret.value}
Remove-Item C:\Windows\Temp\sensor.ps1
Remove-Item C:\Windows\Temp\UserScript.ps1
</powershell>
EOF
    tags = {
        Name = var.instance_name
    }
}

output "windows_example_instance_external_ip" {
	value = "Demonstration RDP address: ${aws_instance.windows_example_instance.public_ip}\nRetrieve the Administrator password from the AWS console."
}