# Deploying with CloudFormation

## Instructions

1. Deploy the CloudFormation template `infrastructure.yml` in your dedicated operational/security account.

    This CloudFormation template consumes the following parameters:

    | Parameter | Description |
    |:-|:-|
    | ServiceName | Name of the service you're deploying |
    | Stage | Stage of deployment (dev/stage/prod) |
    | TargetExecutionRoleName | Name of the IAM Role that Lambda will assume into in target account to perform isolation

2. Retrieve your API URL by looking at the CloudFormation Stack's Outputs and searching for `WebhookURL`.
   1. *Example value*: `https://abc123001.execute-api.us-east-1.amazonaws.com/dev/isolate`
3. Retrieve your API key value by looking at the CloudFormation Stack's Outputs and searching for `APIKeyId`. Once you have the value, go to `API Gateway -> {name of your api} -> API Keys (sidebar) -> Search for your API key`
