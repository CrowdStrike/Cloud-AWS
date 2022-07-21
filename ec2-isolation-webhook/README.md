# EC2 Isolation Webhook

A webhook powered by AWS Lambda and API Gateway to automate network and permission isolation of a potentially-compromised EC2 instance for incident response.

Inspired by [Automate Amazon EC2 instance isolation by using tags](https://aws.amazon.com/blogs/security/automate-amazon-ec2-instance-isolation-by-using-tags/), this solution improves on the foundation by:

- Wrapping this into a webhook to enable DevSecOps teams to incorporate it in their security workflows.
- Ability to assume and execute within accounts in your AWS Organization.
- Improved logging, error handling, and deals with eventual consistency when creating and attaching IAM instance profiles.

## Table of Contents

- [Architectural Overview](#architectural-overview)
  - [Workflow process](#workflow-process)
  - [Permissions](#permissions)
- [Prerequisites and assumptions](#prerequisites-and-assumptions)
  - [IAM Role in target account](#iam-role-in-target-account)
- [Deployment methods](#deployment-methods)
- [Contribution Notes](#contribution-notes)

## Architectural Overview

### Workflow process

1. A user or an automation invokes the webhook enabled by Amazon API Gateway via POST call to URL with details of instance to isolate.
2. Amazon API Gateway invokes Lambda function.
3. The function assumes into the target account.
4. The function creates an isolation Instance Profile if it doesn't exist and attaches it to the target EC2 instance.
5. The function creates an isolation Security Group if it doesn't exist and replaces all attached Security Groups with the isolation Security Group.

### Permissions

The webhook is designed to be deployed into your designated operational or security account. From this account, the webhook would leverage an IAM Role that's delegated to access resources in a another account. This allows the webhook to be deployed once and act on resources across your environment from one location. Visit AWS's documentation to learn more about cross-account roles: [IAM tutorial: Delegate access across AWS accounts using IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html).

## Prerequisites and assumptions

### IAM Role in target account

As mentioned in [Design](#design), a target execution role is required for the Lambda to assume into and execute the isolation. Most organizations managing AWS accounts at scale will likely have such a role provisioned in their child accounts as part of their account factory. If that's the case, then pass the name of the role into the `TargetExecutionRoleName` parameter if you're using CloudFormation or update the `TARGET_EXECUTION_ROLE_NAME` variable in the configuration file if you're deploying with Serverless Framework.

If you don't have such a role created in your environment, you can reference the CloudFormation template `iam-execution-role.yml` and deploy it as a CloudFormation StackSet across your accounts/organization.

The least-privilege IAM Policy that's required for this to work is the following:

```yaml
PolicyDocument:
    Version: "2012-10-17"
    Statement:
        - Effect: Allow
        Resource: '*'
        Action:
            - ec2:RevokeSecurityGroupEgress
            - ec2:ModifyInstanceAttribute
            - ec2:DescribeInstances
            - ec2:CreateSecurityGroup
            - ec2:AssociateIamInstanceProfile
            - ec2:DescribeIamInstanceProfileAssociations
            - ec2:DisassociateIamInstanceProfile
            - ec2:DescribeSecurityGroups
            - ec2:CreateTags
            - iam:CreateRole
            - iam:CreateInstanceProfile
            - iam:GetInstanceProfile
            - iam:AttachRolePolicy
            - iam:AddRoleToInstanceProfile
```

## Deployment methods

This project is deployable as a CloudFormation stack or using [Serverless Framework](https://serverless.com). Please refer to the respective instructions for each deployment method:

- [CloudFormation](cloudformation/)
- [Serverless Framework](serverless-framework/)

## Usage

Sample `curl` command to invoke the webhook (make sure to replace the values with your environment):

```curl
curl --location --request POST 'https://{{api-gw-url}}/{{stage}}/isolate' \
--header 'x-api-key: {{api-key}}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "instance_id": "{{instance-id}}",
  "account_id": "{{aws-account-id}}",
  "region": "{{aws-region}}"
}'
```

If invoked successfully, the API should respond with a status code `200`. Do note that you'll need to monitor your lambda function to ensure everything executed properly downstream.

## Contribution Notes

> **Note** <br>
> For ease of deployment via CloudFormation and not introducing any custom resources or manual steps to seed the package in an S3 bucket, the code is embedded in the CloudFormation template and is zip'ed automatically by CloudFormation. This is mentioned to remind any contributors to update both references of the Lambda code where applicable.
