Setup Systems Manager 
=====================

Introduction
------------

CrowdStrike provide a CloudFormation template to assist with the setup
of an account. The CloudFormation template performs three operations

-   Creates an IAM Role CrowdStrike-SSMExecutionRole

The role has the Amazon managed policy AmazonSSMAutomationRole attached
to it

![](.//media/image1.tiff)

-   Adds parameters to the Systems Manager Parameter Store

![](.//media/image2.png)

-   Checks for the existence of an installation token in the falcon
    console

Deploy the cloudformation template
==================================

1\) Download the CloudFormation template from github

Go to
[https://github.com/crowdstrike/cloud-aws/systems-manager/](https://github.com/crowdstrike/cloud-aws/systems-manager/cloudformation)

Download the template *CrowdStrike-ssm-setup.yaml* from the
cloudformation folder*\
*Download the lambda files "createSsmParams.zip" and "layer.zip from the
lambda/staging folder

2\) Create an S3 Bucket in the region where you will be running the
CloudFormation template

Upload the files to the S3 bucket

![](.//media/image3.png)

3\) Create the OAuth2 API keys in the CrowdStrike Console

<https://falcon.crowdstrike.com/support/documentation/93/oauth2-auth-token-apis#get-an-auth-token>

Create an OAuth2 api key pair with permissions to "Read" Installation
Tokens

4\) Load the CloudFormation template

Add the API OAuth2 Client ID and Client secret

![](.//media/image4.png)
5\) Verify that the template has created the resources

![](.//media/image5.png)
