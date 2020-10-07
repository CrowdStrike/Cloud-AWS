# Cloud-AWS
A collection of projects supporting AWS Integration

## Control Tower
Cloud Formation Templates and lambda functions to integrate Falcon Discover with AWS Control Tower

[Implementation Guide](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Control-Tower/documentation/implementation-guide.md)

[Files](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower)

[Multiple Providers Require SNS notifications](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower/multiple-sns)

## Discover for Cloud

This folder contains a number of templates for setting up AWS accounts with Discover.  The scripts all assument that you are using CloudTrail to write to an S3 bucket in a shared log Archive account. 

### Terraform

[Terraform templates for the log archive account creating new bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-new-S3-bucket-with-new-trail)

[Terraform templates for the log archive account using an existing bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-existing-S3-bucket-and-trail)

[Terraform templates for additional accounts creating new CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-new-trail)

[Terraform templates for additional accounts using and existing CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-existing-trail)

The python script "register_account.py" is included as an example of a script that should be run at the end of the terraform apply to register the AWS account with Crowdstrike.  The script may be run as part of a pipeline or as a local-exec process.

### CloudFormation

[See the README.md file here](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/cloudformation-templates)
