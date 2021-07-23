# Sensor Deployment via S3
These scripts provide examples for deploying the CrowdStrike sensor from an S3 bucket that
resides within your AWS account.

## Bucket Access
Access to the bucket is provided to the instance via an EC2 instance profile. This profile contains
a singular policy providing ListBucket and GetObject access to the specific bucket used for deployment.

### Example Policy
The file `ec2-policy.json` contains an example of what this IAM policy might look like.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::DEPLOYMENT_BUCKET_NAME_HERE/*"
        }
    ]
}
```

## Script usage
This example script accepts 3 arguments, all of which can be defaulted by editing the script directly.
+ `bucket` - The name of the bucket where your sensor file is stored. This should match the name specified in your IAM profile policy.
+ `ccid` - The CCID for your Falcon environment. (Used during sensor installation)
+ `sensor` - The full file name (including extension) for the Sensor file you wish to install.

### Examples
Using the script directly from the command line.
```bash
./amzn-linux2.sh --ccid=CCID_VALUE_HERE --bucket=BUCKET_NAME_HERE --sensor=SENSOR_FILENAME_HERE
```

Calling the script as part of userdata during instance creation.
```bash
#!/bin/bash
cd /tmp
wget -O sensor-install.sh https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Agent-Install-Examples/bash/bucket-deploy/amzn-linux2.sh
chmod +x sensor-install.sh
./sensor-install.sh --ccid=CCID_VALUE_HERE --bucket=BUCKET_NAME_HERE --sensor=SENSOR_FILENAME_HERE
```