![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)

# SSM Distributor package generator
```shell
./create-package.sh [FALCON_CLIENT_ID] [FALCON_CLIENT_SECRET] [AWS_REGION] [SSM PACKAGE NAME] [S3 BUCKET NAME]
```

## Requirements
The following packages are required to execute this helper utility.

- `boto3` - AWS Python SDK
- `crowdstrike-falconpy` - CrowdStrike Python SDK
- `tabulate` - Table formatting library


### More detail
For more details regarding the SSM distributor package utility, please see the setup guide [here](https://github.com/CrowdStrike/Cloud-AWS/blob/master/systems-manager/documentation/AWS-Systems-Manager-Intro.md#option-a---creating-a-package-with-the-installer).