![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)
![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)

# CloudFormation deployment example
This example CFT demonstrates deployment of the following:
+ A single VPC with a single subnet and an internet gateway. VPC Flow logging is enabled.
+ A __t2.micro__ AWS Linux 2 instance that pre-installs the Security Hub integration application as a bootstrap.
    - This instance is assigned an elastic IP. This is not a requirement and only included for demo purposes.
+ A SQS queue, dead-letter queue and Lambda trigger for handling detections identified as findings.
+ A Lambda handler that consumes detections posted to the SQS queue and submits findings to AWS Security Hub based.
+ Security Hub is activated for the region deployed.

> Please note: You will need to manual subscribe to CrowdStrike findings in the region after deploying this tempalte.

## Prerequisites
+ Valid CrowdStrike Falcon API credentials allowing access _READ_ to Event Streams, Hosts, and Detections.
+ A _pre-existing_ S3 bucket, created to hold two archives used to create the lambda handler.
    - [sechub-identify-detections_lambda.zip](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Security-Hub/install) (Download the latest)
    - `layer.zip` - A Lambda layer containing the CrowdStrike FalconPy SDK. You can generate one using the latest SDK with the utility provided [here](https://github.com/CrowdStrike/falconpy/blob/main/util/create-lambda-layer.sh).

## Deployment
You will be asked to provide the following parameters:

| Parameter | Description |
| :--- | :--- |
| FalconClientID | CrowdStrike Falcon API Client ID. |
| FalconClientSecret | CrowdStrike Falcon API Client Secret. |
| InstanceTypeParameter | Instance type to use for the Security Hub Integration instance. Defaults to _t2.micro_. |
| Key | SSH key to use for instance access. |
| S3Bucket | The name of the S3 staging bucket holding the archives detailed above for creating the lambda handler. |
| SecHubInstaller | Name of the Security Hub Integration installer archive to use for the deployment. Defaults to the latest. |
| TrustedIp | IP Address to add as an allowed range to the SSH rule for access to the integration instance. |

Total deployment time will run between 5 and 15 minutes.