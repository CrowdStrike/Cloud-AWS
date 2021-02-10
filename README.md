# Cloud-AWS
A collection of projects supporting AWS Integration

## AWS Network Firewall Integration
[About the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/overview.md)

[Setting up the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/deployment.md)

[Running the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/testing.md)

## Agent Install Examples
[AWS Terraform BootStrap S3](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Agent-Install-Examples/Terraform-bootstrap-s3)

[AWS Autoscale](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Agent-Install-Examples/Cloudformation/autoscale)

## Control Tower
Cloud Formation Templates and lambda functions to integrate Falcon Discover with AWS Control Tower

[Implementation Guide](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Control-Tower/documentation/implementation-guide.md)

[Files](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower)

[Multiple Providers Require SNS notifications](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower/multiple-sns)

## AWS Security Hub Integration/ Falcon Integration Gateway
[CrowdStrike FIG](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Falcon-Integration-Gateway)

## Discover for Cloud

This folder contains a number of templates for setting up AWS accounts with Discover.  The scripts all assume that you are using CloudTrail to write to an S3 bucket in a shared log Archive account. 

### Terraform

[Terraform templates for the log archive account creating new bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-new-S3-bucket-with-new-trail)

[Terraform templates for the log archive account using an existing bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-existing-S3-bucket-and-trail)

[Terraform templates for additional accounts creating new CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-new-trail)

[Terraform templates for additional accounts using and existing CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-existing-trail)

The python script "register_account.py" is included as an example of a script that should be run at the end of the terraform apply to register the AWS account with Crowdstrike.  The script may be run as part of a pipeline or as a local-exec process.

### CloudFormation

[See the README.md file here](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/cloudformation-templates)
