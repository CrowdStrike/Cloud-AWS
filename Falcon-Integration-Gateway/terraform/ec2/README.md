# FIG - EC2 Instance deployment
This folder contains the necessary Terraform files to deploy a FIG instance running on Amazon Linux 2 to EC2. 

## Components created
+ t2.micro instance running Amazon Linux 2 
    + Python 3 is installed
    + Boto3 and requests packages are installed
    + FIG service is deployed and started
+ IAM instance role and policy

## First run
After downloading the Terraform files (*.tf) you must execute _terraform init_ in order to download the necessary resources for Terraform to function. More information regarding Terraform and how it can be leveraged to expedite infrastructure deployments can be found [here](https://learn.hashicorp.com/tutorials/terraform/aws-build?in=terraform/aws-get-started).

## Variables
The necessary Terraform variables for this deployment are contained within the file _ec2-variables.tf_ and define different aspects of the deployment. Several of these values must be updated
before you will be able to proceed.

> Please note: The __*region*__ variable is not stored within _ec2-variables.tf_ and instead resides in _region.tf_. This value __must be__ updated to reflect the appropriate region before you
proceed.

## Required variables
The following variables __must be__ changed to the correct values reflecting your environment before deploying.
+ `region` - The AWS region we are deploying to.
+ `ami_id` - The AMI ID for the most recent Amazon Linux 2 build. This ID is specific to your region and can be retrieved from the AWS console.
+ `key_name` - The name of the SSH key pair used to secure the instance. You must have access to this key in order to connect to your FIG instance remotely.
+ `vpc_security_groups` - A _list_ of security groups to attach to the instance deployed. If no external security permissions are required, set this value
to reflect the ID of the default security group for the VPC.
+ `subnet_id` - The ID of the subnet to deploy this instance to. This value will control which VPC your instance is deployed to as well.

## Optional variables
The following variables _can be_ changed to reflect desired values within your environment.
+ `instance_name` - The string value to use as a name for this instance within the AWS console.
+ `instance_type` - The type and size of instance to use for this deployment. Defaults to t2.micro.
+ `iam_role_name` - The string value to use as the name for the IAM role assigned to the instance.
+ `iam_policy_name` - The string value to use as the name for the policy attached to the instance IAM role.

## Confirming the deployment
Before deploying, confirm you've set the appropriate variable values by executing the following command.
```bash
$ terraform plan
```

## Executing the deployment
You may deploy the infrastructure defined within this folder by issuing the following command.
```bash
$ terraform apply
```
