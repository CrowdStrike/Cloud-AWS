![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# CrowdStrike Falcon S3 Bucket Protection

+ [Overview](#overview)
+ [Integration components](#integration-components)
+ [Demonstration](DEMO.md)

## Overview
This solution integrates CrowdStrike Falcon Quick Scan with AWS S3, AWS Security Hub and AWS Systems Manager (Parameter Store), allowing for files to be scanned and threats remediated as objects are added to the bucket.

### Process diagram
![Process Diagram](../docs/img/s3-bucket-protection-process-diagram.png)

1. Files are uploaded to the bucket
2. Bucket triggers the lambda function
3. Lambda function reads in Falcon API credentials from Systems Manager Parameter Store
4. Lambda function uploads file to Falcon X Sandbox for analysis
5. Lambda function retrieves the scan results
6. Malicious files are immediately removed from the bucket
7. A finding is generated in Security Hub for all malicious uploads

> All lambda activity is also logged to Amazon CloudWatch


## Integration components
This solution leverages an S3 bucket trigger to call AWS Lambda for processing. 
The serverless lambda function leverages the CrowdStrike [FalconPy SDK](https://github.com/CrowdStrike/falconpy) to
interact with the CrowdStrike Falcon API to scan the files as the are uploaded to the bucket.

+ [AWS S3](#aws-s3)
+ [AWS Lambda](#aws-lambda-function)
+ [AWS IAM](#aws-iam)
+ [AWS Systems Manager](#aws-systems-manager)

### AWS S3 
- Bucket
- Bucket notification `s3:ObjectCreated:*` -> Lambda trigger

### AWS Lambda function
- Python 3
- `crowdstrike-falconpy` layer
- Policy statement
    - Statement ID: `AllowExecutionFromS3Bucket`
    - Principal: `s3.amazonaws.com`
    - Effect: `Allow`
    - Action: `lambda:InvokeFunction`
    - Conditions
      ```json
      {
        "ArnLike": {
            "AWS:SourceArn": "arn:aws:s3:::{LAMBDA_FUNCTION_NAME}"
        }
      }
      ```
- Execution Role (detailed in IAM section below)
- Environment variables
    - `base_url`: CrowdStrike API base URL (only required for GovCloud users.)
    - `CLIENT_ID_PARAM`: Name of the Parameter store parameter containing the CrowdStrike API Key.
    - `CLIENT_SECRET_PARAM`: Name of the Parameter store parameter containing the CrowdStrike API Secret.

### AWS IAM
- Lambda execution role
    - Security Hub policy
      ```json
      {
        "Statement": [
            {
                "Action": "securityhub:GetFindings",
                "Effect": "Allow",
                "Resource": "arn:aws:securityhub:{REGION}:{ACCOUNT_ID}:hub/default",
                "Sid": ""
            },
            {
                "Action": "securityhub:BatchImportFindings",
                "Effect": "Allow",
                "Resource": "arn:aws:securityhub:{REGION}:517716713836:product/crowdstrike/*",
                "Sid": ""
            }
        ],
        "Version": "2012-10-17"
      }
      ```
    - S3 policy
      ```json
      {
        "Statement": [
            {
                "Action": [
                    "s3:GetObjectVersion",
                    "s3:GetObject",
                    "s3:DeleteObjectVersion",
                    "s3:DeleteObject"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:s3:::{BUCKET_NAME}/*",
                "Sid": ""
            }
        ],
        "Version": "2012-10-17"
      }
      ```
    - SSM policy
      ```json
      {
        "Statement": [
            {
                "Action": [
                    "ssm:GetParametersByPath",
                    "ssm:GetParameters",
                    "ssm:GetParameterHistory",
                    "ssm:GetParameter"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:ssm:{REGION}:{ACCOUNT_ID}:parameter/*",
                "Sid": ""
            }
        ],
        "Version": "2012-10-17"
      }
      ```
    - Execution policy
      ```json
      {
        "Statement": [
            {
                "Action": "logs:CreateLogGroup",
                "Effect": "Allow",
                "Resource": "arn:aws:logs:{REGION}:{ACCOUNT_ID}:*",
                "Sid": ""
            },
            {
                "Action": [
                    "logs:PutLogEvents",
                    "logs:CreateLogStream"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/lambda/{LAMBDA_FUNCTION_NAME}:*",
                "Sid": ""
            }
        ],
        "Version": "2012-10-17"
      }
      ```

### AWS Systems Manager
- Parameter Store parameters
    - CrowdStrike API Key (SecureString)
    - CrowdStrike API Secret (SecureString)

---

