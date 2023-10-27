# Security Hub Manual Guide

This guide will walk you through the steps required to manually deploy the Security Hub integration application. The guide is based
off the CloudFormation guide.

> :memo: **NOTE:** This guide assumes that you already have a pre-existing VPC and network infrastructure where you would like to deploy the application in.

## Table of Contents

- [Prerequisites](#prerequisites)
- [IAM Roles for EC2 and Lambda](#iam-roles-for-ec2-and-lambda)
  - [Create the IAM Role for EC2](#create-the-iam-role-for-ec2)
  - [Create the IAM Role for Lambda](#create-the-iam-role-for-lambda)
    - [Create Custom Policy for Lambda Role](#create-custom-policy-for-lambda-role)
    - [Create the Lambda Role](#create-the-lambda-role)
- [SQS Queues](#sqs-queues)
  - [Create the Dead Letter Queue](#create-the-dead-letter-queue)
  - [Create the Main SQS Queue](#create-the-main-sqs-queue)
- [SSM Parameters](#ssm-parameters)
- [Lambda](#lambda)
  - [Create Lambda Layer](#create-lambda-layer)
  - [Create Lambda Function](#create-lambda-function)
  - [Create Lambda Trigger](#create-lambda-trigger)
- [Security Group](#security-group)
  - [Create Security Group](#create-security-group)
- [EC2 Instance](#ec2-instance)
  - [Launch Instance](#launch-instance)

## Prerequisites

- Valid CrowdStrike Falcon API credentials allowing access _READ_ to Event Streams, Hosts, and Detections. (Sensor Download can also be used to lookup CIDs, but it is not required.)
- Two pre-existing zip files used to create the lambda handler:
  - [sechub-identify-detections_lambda.zip](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Security-Hub/install) (Download the latest)
  - `falconpy-layer.zip` - A Lambda layer containing the CrowdStrike FalconPy SDK.
    - You can generate one using the latest SDK with the utility provided [here](https://github.com/CrowdStrike/falconpy/blob/main/util/create-lambda-layer.sh).

---

> [!WARNING]
> **Please ensure you are in the correct AWS region for each step**

## IAM Roles for EC2 and Lambda

Open the AWS Management Console, then go to the [IAM dashboard](https://console.aws.amazon.com/iam/home).

### Create the IAM Role for EC2

1. **Create a New Role**:
   - Click on **Roles** from the navigation pane, then click the **Create role** button.
   - Select **AWS service** as the trusted entity type.
   - Choose **EC2** as the service that will use this role, then click the **Next** button.

1. **Attach Policies**:
    - Search and attach the following policies:
        - `AmazonSQSFullAccess`
        - `AmazonEC2RoleforSSM`
        - `AmazonSSMManagedInstanceCore`
    - Click the **Next** button.

1. **Name, review, and create**:
    - Name the role something descriptive, like `EC2-SecHubRole`.
    - Review the configurations.
    - Optionally, add tags.
    - Click the **Create role** button.

### Create the IAM Role for Lambda

> Prior to creating the Lambda role, you will need to create a custom policy for the Lambda role.

#### Create Custom Policy for Lambda Role

1. **Create a New Policy**:
    - From the IAM dashboard, click on **Policies** from the navigation pane, then click the **Create policy** button.
    - Go to the JSON tab and paste the following JSON code:

      ```json
      {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Action": [
                      "ssm:GetParametersByPath",
                      "ssm:GetParameter",
                      "ssm:GetParameters"
                  ],
                  "Resource": "*",
                  "Effect": "Allow"
              },
              {
                  "Action": [
                      "securityhub:*"
                  ],
                  "Resource": "*",
                  "Effect": "Allow"
              }
          ]
      }
      ```

    - Click the **Next** button.

1. **Name and Review**:
    - Name the policy something descriptive, like `LambdaSecHubCustomPolicy`.
    - Review the configurations and click the **Create policy** button.

#### Create the Lambda Role

1. **Create a New Role**:
   - Click on **Roles** from the navigation pane, then click the **Create role** button.
   - Select **AWS service** as the trusted entity type.
   - Choose **Lambda** as the service that will use this role, then click the **Next** button.

1. **Attach Policies**:
    - Search and attach the following policies:
        - `AWSLambdaExecute`
        - `AmazonEC2ReadOnlyAccess`
        - `AmazonSQSFullAccess`
        - `LambdaSecHubCustomPolicy`

1. **Name, review, and create**:
    - Name the role something descriptive, like `Lambda-SecHubRole`.
    - Review the configurations.
    - Optionally, add tags.
    - Click the **Create role** button.

## SQS Queues

Open the AWS Management Console, then go to the [SQS dashboard](https://console.aws.amazon.com/sqs/v2/home).

This integration creates two SQS queues - A "main" queue and a "dead letter" queue. The main queue is configured with a
redrive policy to move messages to the dead letter queue after a specified number of failed processing attempts. Below are the
steps to manually set up these queues in AWS:

### Create the Dead Letter Queue

1. **Create New Queue**:
    - Click on the **Create queue** button.
    - Select **Standard** as the queue type.
    - Name this queue `SecHubDeadLetterQueue` or as per your naming convention.

1. **Create Queue**:
    - Click on the **Create queue** button at the bottom of the page.

### Create the Main SQS Queue

1. **Create New Queue**:
    - Click on the **Create queue** button.
    - Select **Standard** as the queue type.
    - Name the queue per your naming convention, for instance, we will use `SecHubQueue`.

1. **Configure Queue Settings** (optional):
    - Under the **Configuration** section, set the **Visibility Timeout** to 120 seconds.
    - You can leave the rest of the settings at their default values or adjust them according to your requirements.

1. **Enable Dead-letter Queue**:
    - Under the **Dead-letter queue** section, select **Enabled**.
    - Select the dead letter queue you created earlier from the dropdown.
    - Set the **Maximum receives** to 5.

1. **Create Queue**:
    - Click on the **Create queue** button at the bottom of the page.

## SSM Parameters

> If you prefer to use the [config.json](README.md#configjson) file instead of SSM parameters, you can skip this step. This
> guide will use SSM parameters to store the configuration values.

Open the AWS Management Console, then go to the [SSM dashboard](https://console.aws.amazon.com/systems-manager/parameters).

1. **Creating Parameters**:
    - In the navigation pane, choose `Parameter Store`.
    - Choose `Create parameter`.
    - Now create the following parameters:

      | Parameter Name | Type | Value |
      | :--- | :--- | :--- |
      | FIG_FALCON_CLIENT_ID | String | The API client ID for the API key used to access your Falcon environment. |
      | FIG_FALCON_CLIENT_SECRET | SecureString | The API client secret for the API key used to access your Falcon environment. |
      | FIG_APP_ID | String | A unique string value that describes the name of the application you are connecting to Falcon. (e.g. `sechub-integration-1`) |
      | FIG_SEVERITY_THRESHOLD | String | `3` - An integer representing the threshold for detections you want published to AWS Security Hub. |
      | FIG_SQS_QUEUE_NAME | String | `SecHubQueue` - The name of the SQS queue you created earlier. |
      | FIG_SSL_VERIFY | String | `True` - Enable / Disable SSL verification boolean |
      | FIG_API_BASE_URL | String | `https://api.crowdstrike.com` - The base URL for the CrowdStrike Falcon API. |

## Lambda

Open the AWS Management Console, then go to the [Lambda dashboard](https://console.aws.amazon.com/lambda/home).

### Create Lambda Layer

1. **Create Layer**:
    - Click on **Layers** from the navigation pane, then click the **Create layer** button.
    - Name your layer (e.g., `falconpy-layer`).
    - Select **Upload a .zip file** and upload the `falconpy-layer.zip` file.
    - Under **Compatible runtimes**, select `Python 3.7`.
    - Click the **Create** button.

### Create Lambda Function

1. **Create Function**:
    - Click on **Functions** from the navigation pane, then click the **Create function** button.
    - Select **Author from scratch**.
    - Name the function something descriptive, like `SecHub-Lambda`.
    - Select **Python 3.7** as the runtime.
    - Click the **Change default execution role** dropdown and select **Use an existing role**.
    - Select the Lambda role you created earlier (ex: `Lambda-SecHubRole`).
    - Click the **Create function** button.
1. **Upload Function Code**:
    - Under the Function code section, click on the **Upload from** dropdown and select **.zip file**.
    - Select and upload the `sechub-identify-detections_lambda.zip` file.
    - Click the **Save** button.
1. **Update Handler**:
    - In the **Code** tab, scroll down to the **Runtime settings** section.
    - Click on the **Edit** button.
    - Change the **Handler** to `main.lambda_handler`.
1. **Configure General Settings**:
    - In the **Configuration** tab, click on **General configuration**.
    - Set the **Memory (MB)** to `128` and **Timeout** to `1 min`
    - Click the **Save** button.
1. **Configure Environment Variables**:
    - In the **Configuration** tab, click on **Environment variables**.
    - Click on **Edit** and add a new environment variable with the key as `DEBUG` and value as `True`.
    - Click the **Save** button.
1. **Add Lambda Layer**:
    - In the **Code** tab, scroll down to the **Layers** section.
    - Click on **Add a layer**.
    - Select **Custom layers** and select the layer you created earlier (ex: `falconpy-layer`) and version.
    - Click the **Add** button.

### Create Lambda Trigger

1. **Create Trigger**:
    - In the **Function overview** window or under **Configuration -> Triggers**, select the **Add trigger** button.
    - Select **SQS** as the trigger type.
    - Select the main SQS queue you created earlier (ex: `SecHubQueue`).
    - Set the batch size to `1`.
    - Click the **Add** button.

## Security Group

> If you already have a security group that you would like to use, you can skip this step. As long as the security group allows SSH from your trusted IP, it should work.

Open the AWS Management Console, then go to the [VPC dashboard](https://console.aws.amazon.com/vpc/home).

### Create Security Group

1. **Create Security Group**:
   - In the sidebar, click **Security Groups**
   - Click the **Create security group** button.
1. **Configure Security Group**:
   - Name the security group something descriptive, like `SecHub-SG`.
   - Select the VPC where you would like to deploy the application.
   - Add an inbound rule to allow SSH from your trusted IP.
   - Click the **Create security group** button.

## EC2 Instance

> If you already have an EC2 instance that you would like to use, you can skip this step.
> As long as the instance has the appropriate IAM role attached, you can copy/modify the UserData script
> below to bootstrap the application.

Open the AWS Management Console, then go to the [EC2 dashboard](https://console.aws.amazon.com/ec2/v2/home).

### Launch Instance

1. **Launch Instance**:
    - Click on **Instances** from the navigation pane, then click the **Launch Instance** button.
1. **Name and tags**:
    - Name the instance something descriptive, like `SecHub-Instance`.
    - Optionally, add tags.
1. **AMI**: Choose `Amazon Linux 2023`.
1. **Instance Type**: Select your preferred instance type.
1. **Key pair**: Select your preferred key pair.
1. **Network settings**:
    - Select the VPC where you would like to deploy the application.
    - Select any other network related settings as per your needs.
    - **Firewall**: Select the existing security group you created earlier (ex: `SecHub-SG`).
1. **Advanced details**:
    - Click on **Advanced details** to expand the section.
    - **IAM instance profile**: Select the EC2 IAM role you created earlier (ex: `EC2-SecHubRole`).
    - **UserData**: Use the following script for UserData:

      > :pencil2: **Replace** the following variables with your own values (optionally):
      > - `SECHUB_NAME` - Hostname you would like to give the Security Hub integration instance
      > - `SECHUB_INSTALLER` - Name/version of the Security Hub [installer archive](install/)

      ```bash
      #!/bin/bash
      SECHUB_NAME=sechub-crwd-integration
      SECHUB_INSTALLER=sechub-2.0.latest-install.run
      cd /var/tmp
      hostname -b ${SECHUB_NAME}-fig
      echo ${SECHUB_NAME}-fig > /etc/hostname
      sed -i "s/  localhost/ localhost ${SECHUB_NAME}-fig/g" /etc/hosts
      wget -O ${SECHUB_INSTALLER} https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Security-Hub/install/${SECHUB_INSTALLER}
      chmod 755 ${SECHUB_INSTALLER}
      ./${SECHUB_INSTALLER} --target /usr/share/fig
      ```

      > :memo: **NOTE**: For existing instances, you can use the following script to bootstrap the application:
      >
      > ```bash
      > # Run the below as the root user or via sudo
      > cd /var/tmp
      > SECHUB_INSTALLER=sechub-2.0.latest-install.run
      > wget -O ${SECHUB_INSTALLER} https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/master/Security-Hub/install/${SECHUB_INSTALLER}
      > chmod 755 ${SECHUB_INSTALLER}
      > ./${SECHUB_INSTALLER} --target /usr/share/fig
      > ```

1. **Launch Instance**:
    - Click on the **Launch instance** button to initiate a new EC2 instance.
      > Give the instance a few minutes to bootstrap the application and start the services.

---

That concludes this guide! You should now have a similar environment to what is defined in the
CloudFormation template. Feel free to adjust settings and configurations as per your needs.
