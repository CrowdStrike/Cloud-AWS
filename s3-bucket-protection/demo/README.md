![CrowdStrike](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/cs-logo.png)

[![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)](https://twitter.com/CrowdStrike)

# S3 Bucket Protection demonstration
This demonstration leverages Terraform to provide a functional demonstration of this integration.
All of the necessary resources for using this solution to protect an AWS S3 bucket are implemented for you
as part of the environment configuration process, including sample files and command line helper scripts.

+ [Contents](#contents)
+ [Requirements](#requirements)
+ [Additional Components](#additional-components)
+ [Standing up the demonstration](#standing-up-the-demonstration)
+ [Using the demonstration](#using-the-demonstration)
+ [Tearing down the demonstration](#tearing-down-the-demonstration)

## Contents

+ `bucket.tf` - The configuration details for the bucket and it's event triggers.
+ `iam.tf` - The IAM roles and permissions used by the integration and demonstration.
+ `instance.tf` - The demonstration instance configuration.
+ `lambda-function.tf` - The S3 Bucket Protection lambda handler configuration.
+ `output.tf` - The values output by Terraform after the stand-up process completes.
+ `region.tf` - The AWS region the demonstration will deploy to. Edit the region variable to change this to another region.
+ `ssm.tf` - The AWS Systems Manager Parameter Store parameters used by the integration.
+ `variables.tf` - User customizable values used by the integration and demonstrations.
+ `vpc.tf` - The AWS VPC configuration for the demonstration environment.

> Please note: If you use the `demo.sh` helper script provided in the root folder for this integration, you should not need to modify these files unless you want to change the region the demonstration is deployed to. The default region for this demonstration is `us-east-2`.

## Requirements

+ AWS account access with appropriate CLI keys and permissions already configured.
+ The pre-existing PEM key for SSH access to the demonstration instance. This key must exist within the region your demonstration stands up in. (Default: `us-east-2`)
    - You will be asked for the name of this key when the `demo.sh` script executes.
+ CrowdStrike Falcon API credentials with the following scopes:
    - MalQuery - `READ` (used to download malware samples)
    - Quick Scan - `READ`, `WRITE`
    - Sample Uploads - `READ`,`WRITE`
    - You will be asked to provide these credentials when the `demo.sh` script executes.
+ `md5sum` (used to generate a unique bucket name)
+ Terraform installed on the machine you are testing from.
+ The current external IP address of the machine you are testing from.

> This demonstration has been tested using MacOS and Linux, running either BASH or ZSH.

## Additional components
In order to demonstrate functionality, this demonstration adds the following additional AWS components along with the integration's required components.

### AWS VPC
+ VPC
    - Single public subnet
    - Internet gateway
    - Public route table
    - Security group allowing SSH access for defined Trusted IP

### AWS EC2
+ EC2 Instance, `t2.small`
    - IAM Role with two policies
        - Security Hub access
        - S3 access to the bucket (explicitly)
    - Custom helper scripts to demonstrate functionality
    - Sample files for bucket testing
    - Attached to the VPC subnet
    - Attached to the SSH inbound security group

### Demonstration architecture diagram
![Demonstration architecture](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/s3-bucket-protection-demo-architecture.png)

## Standing up the demonstration
From the root folder for this integration (`s3-bucket-protection`) execute the following command:

```shell
./demo.sh up
```

You will be asked to provide:
+ Your CrowdStrike API credentials.
    - These values will not display when entered.
+ The name of the PEM key to use for SSH access. (Do not include the `.pem` extension.)
+ Your external IP address.

```shell
√ s3-bucket-protection % ./demo.sh up

This script should be executed from the s3-bucket-protection root directory.

CrowdStrike API Client ID:
CrowdStrike API Client SECRET:
The following values are not required for the integration, only the demo.
EC2 Instance Key Name: instance-key-name
Trusted IP address: a.b.c.d
```

The latest version of [FalconPy](https://github.com/CrowdStrike/falconpy) is then downloaded as a Lambda layer from https://falconpy.io.

If this is the first time you're executing the demonstration, Terraform will initialize the working folder after you submit these values. After this process completes, Terraform will begin to stand-up the environment.

The demonstration instance is assigned an external IP address, and a security group that allows inbound SSH access from the trusted IP address you provide. The username and external IP address for this instance will be provided when environment creation is complete.

The name of the bucket used for the demonstration is randomly generated and will be output when environment creation is complete.

To stand up the entire demonstration takes approximately two minutes, after which you will be presented with the message:

```shell
  __                        _
 /\_\/                   o | |             |
|    | _  _  _    _  _     | |          ,  |
|    |/ |/ |/ |  / |/ |  | |/ \_|   |  / \_|
 \__/   |  |  |_/  |  |_/|_/\_/  \_/|_/ \/ o
```

---

## Using the demonstration
Once the environment has completed standing up, you should be able to connect via SSH immediately.

```shell
ssh -i KEY_LOCATION ec2-user@IP_ADDRESS
```

Upon successful login, the following help menu should be displayed:

```shell
 _______                        __ _______ __        __ __
|   _   .----.-----.--.--.--.--|  |   _   |  |_.----|__|  |--.-----.
|.  1___|   _|  _  |  |  |  |  _  |   1___|   _|   _|  |    <|  -__|
|.  |___|__| |_____|________|_____|____   |____|__| |__|__|__|_____|
|:  1   |                         |:  1   |
|::.. . |                         |::.. . |
`-------'                         `-------'

Welcome to the CrowdStrike Falcon S3 Bucket Protection demo environment!

The name of your test bucket is efdcecfa-s3-protected-bucket and is
available in the environment variable BUCKET.

There are test files in the testfiles folder.
Use these to test the lambda trigger on bucket uploads.
NOTICE: Files labeled `malicious` are DANGEROUS!

Use the command `upload` to upload all of the test files to your demo bucket.

You can view the contents of your bucket with the command `list-bucket`.

Use the command `get-findings` to view all findings for your demo bucket.
```

### Helper Commands
There are several helper scripts implemented within the environment to demonstrate command line usage.

#### get-findings
Displays any negative findings for the demonstration bucket.

##### Example
```shell
[ec2-user@ip-10-99-10-100 ~]$ get-findings
 _______ __          __ __
|   _   |__.-----.--|  |__.-----.-----.-----.
|.  1___|  |     |  _  |  |     |  _  |__ --|
|.  __) |__|__|__|_____|__|__|__|___  |_____|
|:  |                           |_____|
|::.|
`---'

Findings in efdcecfa-s3-protected-bucket for the past hour:

Falcon Alert. Malware detected in bucket: efdcecfa-s3-protected-bucket
Malware has recently been identified in S3 bucket efdcecfa-s3-protected-bucket.

The file (malicious2.bin) has been removed from the bucket.

Falcon Alert. Malware detected in bucket: efdcecfa-s3-protected-bucket
Malware has recently been identified in S3 bucket efdcecfa-s3-protected-bucket.

The file (malicious3.bin) has been removed from the bucket.

Falcon Alert. Malware detected in bucket: efdcecfa-s3-protected-bucket
Malware has recently been identified in S3 bucket efdcecfa-s3-protected-bucket.

The file (malicious1.bin) has been removed from the bucket.
```

#### list-bucket
Lists the contents of the demonstration bucket.

##### Example
```shell
[ec2-user@ip-10-99-10-100 ~]$ list-bucket
2021-12-22 05:40:10      28904 safe1.bin
2021-12-22 05:40:10      81896 safe2.bin
2021-12-22 05:40:11    1119957 unscannable1.png
2021-12-22 05:40:12      58579 unscannable2.jpg
```

#### upload
Uploads the entire contents of the testfiles folder to the demonstration bucket.

This folder is located in `~/testfiles` and contains multiple samples named according to the sample's type.
+ 2 safe sample files
+ 3 malware sample files
    - These samples are downloaded from CrowdStrike MalQuery as part of the demonstration instance bootstrap.
    - The [FalconPy](https://github.com/CrowdStrike/falconpy) code sample
    [MalQueryinator](https://github.com/CrowdStrike/falconpy/tree/main/samples/malquery#search-and-download-samples-from-malquery) is leveraged to accomplish this.
+ 2 unscannable sample files

##### Example
```shell
[ec2-user@ip-10-99-10-100 ~]$ upload
Uploading test files, please wait...
upload: testfiles/malicious1.bin to s3://efdcecfa-s3-protected-bucket/malicious1.bin
upload: testfiles/malicious2.bin to s3://efdcecfa-s3-protected-bucket/malicious2.bin
upload: testfiles/malicious3.bin to s3://efdcecfa-s3-protected-bucket/malicious3.bin
upload: testfiles/safe1.bin to s3://efdcecfa-s3-protected-bucket/safe1.bin
upload: testfiles/safe2.bin to s3://efdcecfa-s3-protected-bucket/safe2.bin
upload: testfiles/unscannable1.png to s3://efdcecfa-s3-protected-bucket/unscannable1.png
upload: testfiles/unscannable2.jpg to s3://efdcecfa-s3-protected-bucket/unscannable2.jpg
Upload complete. Check CloudWatch logs or use the get-findings command for scan results.
```

### Console example
The following screenshots demonstrate the same functionality using the AWS console.

#### Reviewing Security Hub findings
![Findings](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/s3-bucket-protection-finding-list.png)

#### Reviewing finding details
![Finding details](https://raw.github.com/CrowdStrike/Cloud-AWS/main/docs/img/s3-bucket-protection-finding-display.png)

---

## Tearing down the demonstration
From the same folder where you stood up the environment, execute the command:

```shell
./demo.sh down
```

You will receive no further prompts.

Once the environment has been destroyed, you will be provided the message:

```shell
 ___                              __,
(|  \  _  , _|_  ,_        o     /  |           __|_ |
 |   ||/ / \_|  /  | |  |  |    |   |  /|/|/|  |/ |  |
(\__/ |_/ \/ |_/   |/ \/|_/|/    \_/\_/ | | |_/|_/|_/o
```
