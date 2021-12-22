![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# Existing bucket configuration
This solution will leverage Terraform to apply CrowdStrike S3 Bucket Protection to an existing bucket.

> Please note: If you use the `existing.sh` helper script provided in the root folder for this integration, you should not need to modify these files unless you want to change the region the solution is deployed to. The default region for this solution is `us-east-2` which should match the region where the bucket resides.

## Contents

+ `bucket.tf` - The configuration details for the bucket and it's event triggers.
+ `iam.tf` - The IAM roles and permissions used by the integration and demonstration.
+ `lambda-function.tf` - The S3 Bucket Protection lambda handler configuration.
+ `region.tf` - The AWS region the demonstration will deploy to. Edit the region variable to change this to another region.
+ `ssm.tf` - The AWS Systems Manager Parameter Store parameters used by the integration.
+ `variables.tf` - User customizable values used by the integration and demonstrations.

## Requirements

+ AWS account access with appropriate CLI keys and permissions already configured.
+ CrowdStrike Falcon API credentials with the following scopes:
    - Quick Scan - `READ`, `WRITE`
    - Sample Uploads - `READ`,`WRITE`
    - You will be asked to provide these credentials when the `existing.sh` script executes.
+ Terraform installed on the machine you are testing from.

## Deploying protection
From the root `s3-bucket-protection` folder execute the following command:

```shell
./existing.sh add
```

You will be asked to provide:
+ Your CrowdStrike API credentials.
    - These values will not display when entered.
+ The name of the S3 bucket to protect

```shell
√ s3-bucket-protection % ./existing.sh add

This script should be executed from the s3-bucket-protection root directory.

CrowdStrike API Client ID:
CrowdStrike API Client SECRET:
Bucket name: BUCKET_NAME
```

If this is the first time you're executing the deployment, Terraform will initialize the working folder after you submit these values. After this process completes, Terraform will begin to deploy protection to the bucket.

Deployment takes approximately 30 seconds, after which you will be presented with the message:

```shell
  __                        _
 /\_\/                   o | |             |
|    | _  _  _    _  _     | |          ,  |
|    |/ |/ |/ |  / |/ |  | |/ \_|   |  / \_|
 \__/   |  |  |_/  |  |_/|_/\_/  \_/|_/ \/ o
```

## Removing the solution
From the same folder where you deployed, execute the command:

```shell
./existing.sh remove
```

You will be asked the name of the bucket that you are removing protection from.

Once protection has been disabled, you will be provided the message:

```shell
 ___                              __,
(|  \  _  , _|_  ,_        o     /  |           __|_ |
 |   ||/ / \_|  /  | |  |  |    |   |  /|/|/|  |/ |  |
(\__/ |_/ \/ |_/   |/ \/|_/|/    \_/\_/ | | |_/|_/|_/o
```

> Please note: This process also removes the Lambda function. If you are wanting to just disable protection without completely removing the solution from your AWS account, you can delete the bucket notification trigger. (Either from the Lambda, or from the bucket in question.)