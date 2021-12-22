![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# Demonstration environment configuration
The demonstration that is provided with this integration leverages Terraform to deploy the example environment.

> Please note: If you use the `demo.sh` helper script provided in the root folder for this integration, you should not need to modify these files unless you want to change the region the demonstration is deployed to. The default region for this demonstration is `us-east-2`.

## Contents

+ `bucket.tf` - The configuration details for the bucket and it's event triggers.
+ `iam.tf` - The IAM roles and permissions used by the integration and demonstration.
+ `instance.tf` - The demonstration instance configuration.
+ `lambda-function.tf` - The S3 Bucket Protection lambda handler configuration.
+ `output.tf` - The values output by Terraform after the stand-up process completes.
+ `region.tf` - The AWS region the demonstration will deploy to. Edit the region variable to change this to another region.
+ `ssm.tf` - The AWS Systems Manager Parameter Store parameters used by the integration.
+ `variables.tf` - User customizable values used by the integration and demonstrations.
+ `vpc.tf` - The AWS VPC configuration for the demonstration environment.