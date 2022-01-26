![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)

# AWS Distributor Falcon deployment package generator
This folder contains an example for generating a AWS Distributor package for deploying the CrowdStrike Falcon agent.

This example creates a package that can be installed via automation on Amazon Linux 2 and Microsoft Windows instances.

## Requirements
You will need the AWS CLI installed and configured to communicate with the AWS account you are deploying to.
`curl` is used to download helper scripts from CrowdStrike repositories on GitHub.

The following Python packages are required to execute this helper utility.

- `boto3` - AWS Python SDK
- `crowdstrike-falconpy` - CrowdStrike Python SDK
- `tabulate` - Table formatting library

## Usage
The included BASH script `create-package.sh` will download the necessary scripts to create and upload the package for you.
This includes downloading the necessary versions of the CrowdStrike Falcon agent, and bundling these binaries within the distribution archive.

### Command line
The following command line will initiate a package build. All inputs are required.

| Argument | Description |
| :--- | :--- |
| `FALCON_CLIENT_ID` | CrowdStrike Falcon API client ID. |
| `FALCON_CLIENT_SECRET` | CrowdStrike Falcon API client secret. |
| `AWS_REGION` | AWS region to deploy this package to. |
| `SSM PACKAGE NAME` | Name to use for the package you are creating. This name will be provided to the CFT used to stand up the rest of this solution. |
| `S3_BUCKET_NAME` | Name of the S3 bucket to use for the distributor package. This should be the same bucket you upload the `agent-handler.zip` file to as part of the solution deployment. You will provide this name to the CFT when you stand up the rest of this solution. |

#### Example
```shell
./create-package.sh [FALCON_CLIENT_ID] [FALCON_CLIENT_SECRET] [AWS_REGION] [SSM PACKAGE NAME] [S3 BUCKET NAME]
```

### Downloaded scripts
The following two scripts are downloaded and used to perform this operation.

| Name | Description |
| :--- | :--- |
| [`packager.py`](https://github.com/CrowdStrike/Cloud-AWS/blob/main/systems-manager/Packaging-utilities/examples/linux-sensor-binary/packager.py) | Python script for creating an AWS Distributor package based off of a index file (`agent-list.json`) that describes the instance types to target. |
| [`download_sensor.py`](https://github.com/CrowdStrike/falconpy/blob/main/samples/sensor_download/download_sensor.py) | [CrowdStrike Python SDK](https://github.com/CrowdStrike/falconpy) sample for listing and downloading Falcon agents based upon requested operating system and version. |


## More detail
For more details regarding the SSM distributor package utility, please review the documentation located [here](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/AWS-Systems-Manager-Intro.md#option-a---creating-a-package-with-the-installer).