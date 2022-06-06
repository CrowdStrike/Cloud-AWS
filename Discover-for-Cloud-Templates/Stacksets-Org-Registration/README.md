# Discover Org Registration Templates

The template is supported in the following regions

eu-west-1

us-east-1

us-east-2

us-west-2

ap-southeast-2


## Overview

Creates resources that help with Discover account registration in an AWS Organization. 

Creates a Service Managed StackSet in an account, use this stackset to deploy to your organization / target Organizational Unit(s)
Auto-deployment is currently set to true however does not specify a target so does not deploy until you select Add Stack Instances to StackSets
Optionally creates the Discover Stack in the StackSets master account as a nested stack (needed due to StackSets with Service Managed Permissions skipping the root account by default)

This stack does not setup the CloudTrail notifications for the S3 bucket, please follow the guides from the Falcon Docs to set up notifications from either your CloudTrail or S3 bucket hosting your cloudtrail logs, the stack will automatically create the correct s3 read permissions within the Log Archive account.

## Prerequisites

1) CrowdStrike Falcon API Key with `AWS accounts` `READ` & `WRITE` Scopes

2) Generate an unique string to use as the External ID within the cross account statement (example: use `uuidgen` or use a password generator to create a value). This will be used when registering the accounts within Falcon.

3) Access the AWS Organizations Root Account / CloudFormation StackSets delegated administrator account with the ability to create CloudFormation Stacks/StackSets.

## Instructions

1) Log into your Organizations Root Account / CloudFormation StackSets delegated administrator account.

2) Generate an External ID to be used within the IAM Cross Account Trust Statement. (This can be any value you like)

3) Navigate to the CloudFormation console and create a new CloudFormation stack, select upload a template file and upload the `Discover_setup_delegated_account.yaml` template from the "cft" folder and apply the settings.

4) Once the stack completes, navigate to the CloudFormation StackSets console, select the created stackset and select `Actions` - `Add Stacks to StackSets`

5) Select to either deploy to entire organization or select individual organization units. Specify one of the following regions to deploy the stacks to: `us-east-1`, `us-east-2`, `us-west-2`, `eu-west-1`, `ap-southeast-2`. 

6) Optionally change the deployment concurrency and failure tolerance. Select Next then Submit.

7) View the progress from the `Stack Instances` tab.


## StackSet Details

The above cft creates the StackSet using values from a mapping file.  The following mappings apply: 

|  CSCloud 	|  us1 	|   us2	|   eu	|   	
|---	|---	|---	|---	|
|  CSAssumingRoleName 	| CS-Prod-HG-CsCloudconnectaws  	|   mav-gyr-main-s001-cs-cloudconnectaws	| lion-lanner-main-s001-cs-cloudconnectaws  	|   	
|  CSAccountNumber 	| 292230061137   	|  292230061137 	|  292230061137  	|   






