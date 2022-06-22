# Discover Org Registration Templates

The template is supported in the following regions

eu-west-1

us-east-1

us-east-2

us-west-2

ap-southeast-1

ap-southeast-2


## Overview

Creates resources that help with Discover account registration in an AWS Organization. 

Creates a Service Managed StackSet in an account, use this stackset to deploy to your organization / target Organizational Unit(s)
Auto-deployment is currently set to true however does not specify a target so does not deploy until you select Add Stack Instances to StackSets
Optionally creates the Discover Stack in the StackSets master account as a nested stack (needed due to StackSets with Service Managed Permissions skipping the root account by default)

This stack does not setup the CloudTrail notifications for the S3 bucket, refer to the **S3 CloudTrail - SNS notification setup** section within this README for instructions on setting this up. The stackset instance automatically sets up the relevant permissions on the IAM role in the log archive account in order to read from the bucket.

## Prerequisites

1) CrowdStrike Falcon API Key with `AWS accounts` `READ` & `WRITE` Scopes

2) Access the AWS Organizations Root Account / CloudFormation StackSets delegated administrator account with the ability to create CloudFormation Stacks/StackSets.

3) Knowledge of your AWS Organization structure such as location of your S3 Bucket storing your CloudTrail logs.

## Instructions - StackSet Creation and StackSet instance deployment

1) Log into your Organizations Root Account / CloudFormation StackSets delegated administrator account.

2) Navigate to the CloudFormation console and create a new CloudFormation stack, select upload a template file and upload the `Discover_setup_delegated_account.yaml` template from the "cft" folder.

3) Enter the required parameters within the template and select whether or not you wish to also deploy to Root account, select this if you wish for the stack to be created as a nested stack within StackSets administration / root account. (When using service-managed permissions with StackSets, the root / StackSets administration account is excluded by default)

4) Once the stack completes, navigate to the `CloudFormation - StackSets` console, select the newly created stackset and select `Actions` - `Add Stacks to StackSets`

5) Select to deploy to either `entire organization` or specify individual `organization units`. Specify ONE of the following regions to deploy the stacks to: `us-east-1`, `us-east-2`, `us-west-2`, `eu-west-1`, `ap-southeast-1`, `ap-southeast-2`. 

6) Optionally change the deployment concurrency and failure tolerance. Select Next then Submit.

7) View the progress from the `Stack Instances` tab.

8) Proceed to setup bucket notifications on your cloudtrail log bucket. (Manual steps - see below)

## S3 CloudTrail - SNS notification setup

1) Log into the AWS account which is hosting your S3 bucket storing all of your Cloudtrail logs.

2) Navigate to the S3 console and select the bucket that contains your CloudTrail logs.

3) Select Properties Tab and under Event notifications select `Create event notification`.

4) Use the following settings the event setup:
    - Name: `crowdstrike-discover-integration`
    - Suffix: `.json.gz`
    - Event types: Select `Put` under Object creation.
    - Destination: `SNS Topic` - `Enter SNS Topic ARN`
    - SNS Topic Value: Input the SNS topic depending on your Falcon Cloud location. (Replace the REGION value with the aws region code where your S3 bucket is hosted. Crowdstrike supports US, EU, ME, CA and APAC AWS regions).
        - US-1: `arn:aws:sns:<REGION>:292230061137:cs-cloudconnect-aws-cloudtrail`
        - US-2: `arn:aws:sns:<REGION>:292230061137:cs-us2-cloudconnect-aws-cloudtrail`
        - EU-1: `arn:aws:sns:<REGION>:292230061137:cs-lion-cloudconnect-aws-cloudtrail`
    - Select `Save changes`.

## StackSet Details

The above cft creates the StackSet using values from a mapping file.  The following mappings apply: 

|  CSCloud 	|  us1 	|   us2	|   eu	|   	
|---	|---	|---	|---	|
|  CSAssumingRoleName 	| CS-Prod-HG-CsCloudconnectaws  	|   mav-gyr-main-s001-cs-cloudconnectaws	| lion-lanner-main-s001-cs-cloudconnectaws  	|   	
|  CSAccountNumber 	| 292230061137   	|  292230061137 	|  292230061137  	|   






