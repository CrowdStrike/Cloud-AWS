variable "instance_name" {
	type = string
	default = "CS-SECHUB-INT-TERRAFORM-EXAMPLE"
}

variable "instance_type" {
	type = string
	default = "t2.micro"
}

variable "key_name" {
	type = string
	default = "PEM-KEY-NAME-HERE"
}

variable "iam_role_name" {
	type = string
	default = "CS-SECHUB-INT-example-instance-role"
}

variable "role_policy_file_name" {
	type = string
	default = "instance_role_policy.json"
}

variable "iam_policy_name" {
	type = string
	default = "CS-SECHUB-INT-example-instance-policy"
}

variable "policy_file_name" {
	type = string
	default = "instance_policy.json"
}

variable "cidr_vpc" {
    description = "CIDR block for the VPC"
    default     = "10.199.0.0/16"
}

variable "cidr_subnet" {
    description = "CIDR block for the subnet"
    default     = "10.199.10.0/24"
}

variable "trusted_ip" {
    description = "Trusted IP address to access the test bastion"
    type        = string
    default     = "1.1.1.1/32"
}

variable "ssh_group_name" {
    description = "Name of the security group allowing inbound SSH from the Trusted IP"
    type        = string
    default     = "CS-SECHUB-INT-TRUSTED-ADMIN"
}
