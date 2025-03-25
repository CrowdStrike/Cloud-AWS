# CrowdStrike Falcon Elastic Beanstalk Deployment

This repository contains a sample AWS Elasticbeanstalk application to help illustrate how to deploy the Falcon sensor on your Elastic Beanstalk compute resources.
The recommended way is to use use an ebextension to deploy the Falcon sensor, but there are two other methods described at the bottom of this readme you can also utilize.

## Table of Contents

- [ebextensions (Recommended)](#ebextensions-recommended)
  - [Configuration](#configuration)
- [Deploying the Example Application](#deploying-the-example-application)
  - [Prerequisites](#prerequisites)
  - [Deployment Steps](#deployment-steps)
    - [Step 1: Store Falcon Credentials](#step-1-store-falcon-credentials)
    - [Step 2: Create a Key-Pair](#step-2-create-a-key-pair)
    - [Step 3: Create an Instance Profile](#step-3-create-an-instance-profile)
    - [Step 4: Create Elastic Beanstalk Environment](#step-4-create-elastic-beanstalk-environment)
    - [Step 5: Package the Sample Application](#step-5-package-the-sample-application)
    - [Step 6: Deploy the Sample Application](#step-6-deploy-the-sample-application)
    - [Step 7: Verify the Application Deployment](#step-7-verify-the-application-deployment)
    - [Step 8: Verify the Falcon Sensor Installation](#step-8-verify-the-falcon-sensor-installation)
- [Other Deployment Options](#other-deployment-options)
  - [AWS SSM](#aws-ssm)
  - [Baked in AMI](#baked-in-ami)

## ebextensions (Recommended)

### Configuration

1. First, add the Falcon client id and secret to Secrets Manager.

1. Create a `scripts` folder. In the script folder, create the following file.

`scripts/install_falcon.sh`

```bash
#!/bin/bash

export FALCON_CLIENT_ID="$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text | jq -r .FALCON_CLIENT_ID)"
export FALCON_CLIENT_SECRET="$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text | jq -r .FALCON_CLIENT_SECRET)"

curl -L https://raw.githubusercontent.com/crowdstrike/falcon-scripts/v1.7.1/bash/install/falcon-linux-install.sh | bash

```

> [!NOTE]
> This script retrieves the Falcon credentials from secrets manager, and installs the sensor using the linux script from the [falcon-scripts repository](https://github.com/CrowdStrike/falcon-scripts).

3. Create a `.ebextensions` directory in the root of the application package. Within this folder, create the following files.

`.ebextensions/secrets_manager.config`

```
option_settings:
  aws:elasticbeanstalk:application:environment:
    SECRET_ID: <secret name>
```

>[!TIP]
> Remember to change \<secret name\> to your actual secret name

> [!NOTE]
> This config will ensure the secret name is exported as an environment variable.

`.ebextensions/falcon.config`

```
container_commands:
  01_falcon:
    command: "sh scripts/install_falcon.sh"
```

> [!NOTE]
> This config will execute the falcon install script we previously created at runtime.

## Deploying the example application

### Prerequisites

- Have a current CrowdStrike Subscription
- Have appropriate AWS permissions to run CloudFormation and create resources
- Generate Falcon API credentials (Client ID and Client Secret)
- Ensure you have the [aws-elasticbeanstalk-service-role](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/concepts-roles-service.html) deployed in your AWS account

### Deployment steps

#### Step 1: Store Falcon credentials

1. Open the AWS console ans navigate to Secrets Manager.

1. Click on **Store a new secret**.

1. Under **Secret type** Choose **Other type of secret**

1. Create an entry for **FALCON_CLIENT_ID** and **FALCON_CLIENT_SECRET** with their respective values

1. Under **Secret Name** enter **ebs/falcon/credentials**

1. Click **Next** -> **Next** -> **Store**

#### Step 2: Create a key-pair

>[!NOTE]
> If you already have a key pair you want to use, feel free to skip this step

1. In the AWS Console, navigate to **EC2**

1. Under **Network and security** click **Key Pairs**

1. Click **Create key pair**

1. Give your key pair a suitable name.

1. Click **Create key pair** as save your key to a secure location.

#### Step 3: Create an Instance profile

1. Navigate to **IAM** in the AWS console.

1. Click **Roles** and **Create role**

1. Under **Select trusted entity** choose **AWS Service**

1. Under **Use case** choose **EC2** then click **Next**

1. Select the **AWSElasticBeanstalkWebTier** and **SecretsManagerReadWrite** managed policies. Click **Next**

1. Give your role a name then click **Create role**

#### Step 4: Create Elastic Beanstalk Environment

1. Navigate to **Elastic Beanstalk** in the AWS Console
Click on **Create environment**

- **Configure Environment**
  - Choose the following values
    - **Environment tier**: Web server environment
    - **Application Name**: CSHelloWorld
    - **Platform**: Python
    - **Platform branch**: Python 3.12
    - **Platform version**: 4.3.1(Recommended)
  - Click **Next**
- **Configure service access**
  - For **Existing service roles** choose **aws-elasticbeanstalk-service-role**
    - If you do not have this role, refer to [this documentation](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/concepts-roles-service.html) to get it deployed.
  - For **EC2 key pair**, choose the key pair we created earlier
  - For **EC2 instance profile** choose the instance profile we created earlier
  - Click **Next** until you arrive at **Configure instance traffic and scaling**
- **Configure instance traffic and scaling**
  - For **Root volume type** choose **General Purpose 3(SSD)**
  - Leave everything else as default, scroll down, and click **Skip to review**
  - Click **Submit**

#### Step 5: Package the sample application

Open up this root directory in your terminal and execute the following commands

```bash
zip -r ./hello_world.zip .
```

#### Step 6: Deploy the sample application

1. Navigate back to the environment we created in Elastic Beanstalk.

1. Click **Upload and deploy**.

1. Select the **hello_world.zip** file we created.

1. Click **Deploy**

#### Step 7: Verify the application deployment

1. Click the url under **Domain**

1. You should see a simple webpage with a `Hello World!` message

#### Step 8: Verify the Falcon sensor installation

1. In the logs tab, click **Request logs** and then **Full**

1. Download and unzip the contents

1. In the `var/log/` directory, open the cfn-init-cmd.log file. At the bottom of the file, you should see some logs that resemble the following

```
...
2024-12-03 17:53:01,286 P3644 [INFO] Command 01_falcon
2024-12-03 17:53:14,245 P3644 [INFO] -----------------------Command Output-----------------------
2024-12-03 17:53:14,246 P3644 [INFO]    % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
2024-12-03 17:53:14,247 P3644 [INFO]                                   Dload  Upload   Total   Spent    Left  Speed
2024-12-03 17:53:14,247 P3644 [INFO]  
2024-12-03 17:53:14,247 P3644 [INFO]    0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
2024-12-03 17:53:14,247 P3644 [INFO]  100 35817  100 35817    0     0   164k      0 --:--:-- --:--:-- --:--:--  164k
2024-12-03 17:53:14,247 P3644 [INFO]  Check if Falcon Sensor is running ... [ Not present ]
2024-12-03 17:53:14,247 P3644 [INFO]  Falcon Sensor Install  ... 
2024-12-03 17:53:14,247 P3644 [INFO]  Installed:
2024-12-03 17:53:14,247 P3644 [INFO]    falcon-sensor-7.20.0-17306.amzn2023.x86_64                                    
2024-12-03 17:53:14,247 P3644 [INFO]  
2024-12-03 17:53:14,247 P3644 [INFO]  [ Ok ]
2024-12-03 17:53:14,247 P3644 [INFO]  Falcon Sensor Register ... [ Ok ]
2024-12-03 17:53:14,247 P3644 [INFO]  Falcon Sensor Restart  ... [ Ok ]
2024-12-03 17:53:14,247 P3644 [INFO]  Falcon Sensor installed successfully.
2024-12-03 17:53:14,247 P3644 [INFO] ------------------------------------------------------------
2024-12-03 17:53:14,248 P3644 [INFO] Completed successfully.

```

Congratulations! The sensor was successfully installed.

>[!TIP]
>You can further confirm this by querying for your instance in the Falcon console.

### Other Deployment Options

#### AWS SSM

This method involves using AWS SSM distributor to deploy the Falcon sensor directly on the machine. An in depth guide can be found [in this repository](https://github.com/CrowdStrike/aws-ssm-distributor?tab=readme-ov-file)

#### Baked in AMI

This method involves creating custom AMIs with the Falcon sensor already installed using [EC2 Image Builder](https://aws.amazon.com/image-builder/), and using that AMI for your Elasticbeanstalk compute resources. An in depth guide can be found [in this repository](https://github.com/CrowdStrike/aws-ec2-image-builder)
