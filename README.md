# Cloud-AWS
A collection of projects supporting AWS Integration

## Control Tower
Cloud Formation Templates and lambda functions to integrate Falcon Discover with AWS Control Tower

[Implementation Guide](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Control-Tower/documentation/implementation-guide.md)

[Files](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower)


## Discover for Cloud

Assumes CloudTrail will write to a single S3 bucket. 

[Terraform templates for the log archive account creating new bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-new-S3-bucket-with-new-trail)

[Terraform templates for the log archive account using an existing bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-existing-S3-bucket-and-trail)

[Terraform templates for additional accounts creating new CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-new-trail)

[Terraform templates for additional accounts using and existing CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-existing-trail)

The python script "register_account.py" is included as an example of a script that should be run at the end of the terraform apply to register the AWS account with Crowdstrike.  The script may be run as part of a pipeline or as a local-exec process.