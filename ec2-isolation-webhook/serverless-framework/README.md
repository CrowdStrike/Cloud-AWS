# Deploying with Serverless Framework

## Prerequisites

1. Install Serverless Framework: `npm install -g serverless`

## Instructions

1. Open `config.yml` and update `TARGET_EXECUTION_ROLE_NAME` with the name of the IAM Role the Lambda will use to assume into the target account to execute the isolation. For more information, read [IAM Role in target account](../README.md#iam-role-in-target-account).

2. Export the AWS profile into your environment where you'll deploy the service: `export AWS_PROFILE={profile-name}`
   1. If you want to leverage another to setup your credentials in Serverless Framework, visit [AWS Credentials](https://www.serverless.com/framework/docs/providers/aws/guide/credentials) for more options.

3. Deploy the service: `sls deploy -r {region} -s {stage}`
   1. Make sure to replace `{region}` and `{stage}` with your respective values.

4. Once deployed, the values of your API URL and API Key will be displayed in the terminal.
