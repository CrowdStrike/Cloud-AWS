#The name of our EC2 instance
variable "instance_name" {
	type = string
	default = "FIG-TERRAFORM-EXAMPLE"
}

#Instance size
variable "instance_type" {
	type = string
	default = "t2.micro"
}

#This should refer to the AMI ID of the AWS Linux 2
#public image available in your region. The ID listed
#below will only work in the us-east-2 region.
variable "ami_id" {
	type = string
	default = "ami-000279759c4819ddf"
}

#The name of the keypair used to create the instance
variable "key_name" {
	type = string
	default = "<<KEY_NAME_HERE>>"
}

#List of security groups to attach. There must be at 
#least one.  Use the "default" group for your vpc
#environment if you do not have another group to use.
variable "vpc_security_groups" {
	type = list(string)
	default = [
		"<<SECURITY_GROUP_ID_HERE>>"
	]
}

#The ID of the subnet where you wish to deploy your instance
#This will determine the VPC and if your instance has a route
#to the Internet.
variable "subnet_id" {
	type = string
	default = "<<SUBNET_ID_HERE>>"
}

#The name of the FIG instance IAM role used for your instance
variable "iam_role_name" {
	type = string
	default = "fig-example-instance-role"
}

#The name of the custom policy attached to the role for this instance
variable "iam_policy_name" {
	type = string
	default = "fig-example-instance-policy"
}