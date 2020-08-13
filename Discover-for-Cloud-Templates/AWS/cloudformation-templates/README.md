## Log archive directory
Contains a template that will add an event that will send an SNS notification to the CrowdStrike SNS topic and add the required IAM role and permissions for CrowdStrike to read the CloudTrail log files.

## New account existing trail
Assumes the account has already been created and is sending CloudTrail logs to the log archive account S3 bucket.   The template will add a IAM role and permissions to perform API calls to gather details about the resources created.

## New account new trail
Configures CloudTrail to write logs to the central log archive account S3 bucket and creates the IAM role and permissions to perform API calls to gather details about the resources created.

## Lambda-functions
Contains lambda functions for setting up SNS notification on the S3 bucket and for registering the account with the CrowdStrike API
