![CrowdStrike Falcon](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

![Twitter URL](https://img.shields.io/twitter/url?label=Follow%20%40CrowdStrike&style=social&url=https%3A%2F%2Ftwitter.com%2FCrowdStrike)

# Automating CrowdStrike Falcon agent deployment with AWS EventBridge and AWS Systems Manager State Manager

- [Overview](#overview)
- [Solution components](#solution-components)
- [Implementing the solution](#implementing-the-solution)
- [Reviewing executions](#reviewing-executions)

## Overview
This solution leverages [The CrowdStrike Python SDK](#crowdstrike-falconpy), AWS EventBridge, and AWS Systems Manager ([AWS Automations](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html), [AWS Distributor](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html), and [AWS State Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html)) to automate the CrowdStrike Falcon Agent deployment for EC2 instances. Upon instance termination, agents are automatically removed from the Falcon Console.

- [Architecture diagram](#architecture-diagram)
- [Process flow](#process-flow)
- [Solution benefits](#solution-benefits)
- [Additional notes](#additional-notes)


### Architecture diagram
This solution leverages native AWS services and the CrowdStrike cloud to determine instance targets and to perform automated actions.

![Diagram depicting automated deployment of Falcon Agent with AWS SSM State Manager](images/architecture-diagram.png)

### Process flow
There are two distinct process flows for this solution.
The first process handles both agent installation and stale association pruning, executed on a schedule.
The second process is triggered on demand and handles host removal from the Falcon console when instances are moved to the `terminated` state.

![Process flow diagram](images/process-flow.png)

### Solution benefits

- Automated agent deployment as part of instance lifecycle management
  - Support for all instances, regardless of infrastructure deployment patterns e.g., (Standalone, Load-balanced, ASG, etc.)
  - Supports ephemeral instances
  - Addresses configuration drift
  - Removes terminated instances from the Falcon Console

### Additional notes

- AWS State Manager associations apply on a scheduled basis, which can be overridden using the helper script (`apply_association.py`) provided.
- This solutions provides support in the specific region where you deploy. If you're running multi-region workloads, deploy this solution across all regions you wish to manage.


## Solution components
This solution is comprised of native AWS service offerings and scripted automation processes.

- [AWS EventBridge](#aws-eventbridge)
    - [Event Pattern](#event-pattern)
- [AWS IAM](#aws-iam)
    - [Execution Role](#execution-role)
    - [AmazonSSMAutomationRole](#amazonssmautomationrole)
    - [Allow Read EC2 access](#allow-read-ec2-access)
- [AWS S3](#aws-s3)
- [AWS Systems Manager](#aws-systems-manager)
    - [AWS Automation](#aws-automation)
    - [AWS Distributor](#aws-distributor)
    - [AWS Parameter Store](#aws-parameter-store)
    - [AWS State Manager](#aws-state-manager)
        - [Target Types](#target-types)
- [CrowdStrike FalconPy](#crowdstrike-falconpy)

### AWS EventBridge
AWS EventBridge is used to trigger the SSM Automation deployment document when instances are moved to the `terminated` status. This is handled using an EventBridge rule.

#### Event Pattern
This rule uses a simple Event Pattern that targets instances when their state is changed to `terminated`.

```json
{
  "detail-type": ["EC2 Instance State-change Notification"],
  "source": ["aws.ec2"],
  "detail": {
    "state": ["terminated"]
  }
}
```

### AWS IAM
IAM is utilized to store execution permissions for the automation.

#### Execution Role
This role is used to provide execution permissions to the SSM Automation document. There are two policies attached.

##### AmazonSSMAutomationRole
This is an AWS provided policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:*:*:function:Automation*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateImage",
                "ec2:CopyImage",
                "ec2:DeregisterImage",
                "ec2:DescribeImages",
                "ec2:DeleteSnapshot",
                "ec2:StartInstances",
                "ec2:RunInstances",
                "ec2:StopInstances",
                "ec2:TerminateInstances",
                "ec2:DescribeInstanceStatus",
                "ec2:CreateTags",
                "ec2:DeleteTags",
                "ec2:DescribeTags",
                "cloudformation:CreateStack",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStacks",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:*"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": [
                "arn:aws:sns:*:*:Automation*"
            ]
        }
    ]
}
```

##### Allow Read EC2 access
A limited read scope policy allows the automation to retrieve EC2 tags.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeTags"
            ],
            "Resource": "*",
            "Effect": "Allow"
        }
    ]
}
```

### AWS S3
A single AWS S3 bucket is used to store the AWS Distributor package and the `agent-handler.zip` attachment layer.

### AWS Systems Manager
AWS Systems Manager is used to handle automation and deploy packages.

#### AWS Automation
A single SSM Automation Document is used to handle all agent management logic. This document contains steps for installation and removal of the agent, and includes an attachment containing the necessary helpers for interacting with your tenant within the CrowdStrike cloud.

#### AWS Distributor
A single AWS Distributor package is created, containing manifests and installers for Amazon Linux 2 (x64) and Microsoft Windows (10+/2016+). This is a bundled variation, so the binary installers are included within this distribution as well.

#### AWS Parameter Store
Three AWS Parameter Store parameters are created. These are used to provide credentials to the automation helper in a secure fashion.

#### AWS State Manager
A single AWS State Manager Association is created, creating the relationship between the targets you specify and the SSM Automation Document.

##### Target Types
AWS State Manager allows you to create Associations with various types of target configurations. It's important to remember the following:

- Associations are applied to resources within the region where the Association is created. If you're running multi-region workloads, deploy this solution in the other regions.
- If you're using **Tag Key and Value**, **Tag Key**, or **Resource Groups** as your `Target Type`, note that you can only use one combination per Association due to limitations of AWS State Manager. If you need multiple combinations, you'll need to create multiple Associations.

> As of today, only the **Tag Key and Value** Target Type is supported.

1. **Tag Key and Value**: Applies the Association to EC2s that contain a specific tag key/value combination.
   1. CloudFormation Parameter example:
      1. `TargetTagKey`: tag:{replace-with-tag-key}
      2. `TargetTagValue`: {replace-with-tag-value}
2. **Tag Key**: Applies the Association to EC2s that contain a specific tag key.
   1. CloudFormation Parameter example:
      1. `TargetTagKey`: tag-key
      2. `TargetTagValue`: {replace-with-tag-key}
3. **Resource Groups**: Applies the Association to a Resource Group of EC2s.
4. **All Instance**: Applies the Association to all EC2s.
   1. CloudFormation Parameter example:
      1. `TargetTagKey`: InstanceIds
      2. `TargetTagValue`: *

### CrowdStrike FalconPy
The CrowdStrike Python SDK, FalconPy, is used to interact with the CrowdStrike API as part of automation steps.

The FalconPy SDK contains a collection of Python classes that abstract CrowdStrike Falcon OAuth2 API interaction, removing duplicative code and allowing developers to focus on just the logic of their solution requirements.

FalconPy can be installed quickly using the following command:

```shell
python3 -m pip install crowdstrike-falconpy
```

For more details regarding FalconPy, refer to the project [repository](https://github.com/CrowdStrike/falconpy).


## Implementing the solution
This solution is designed to be easy to implement and can be modified quickly to meet the needs of your specific environment.

- [Prerequisites](#prerequisites)
- [Automation scripts](#automation-scripts)
- [Deployment steps](#deployment-steps)
    - [Step 1. Clone this repository](#step-1-clone-this-repository)
    - [Step 2. Create the SSM Distributor Package](#step-2-create-the-ssm-distributor-package)
    - [Step 3. Automation script upload](#step-3-automation-script-upload)
    - [Step 4. Deploy the stack via CloudFormation](#step-4-deploy-the-stack-via-cloudformation)
        - [Parameters](#parameters)
        - [Deployment](#deployment)
            - [AWS CLI deployment](#aws-cli-deployment)
            - [AWS Console deployment](#aws-console-deployment)

### Prerequisites
The following requirements must be met before you will be able to deploy or use this solution.

1. AWS CLI with the appropriate console permissions.
    - EC2
    - EventBridge
    - IAM
    - S3
    - State Manager
2. The [AWS SSM Agent](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html) is installed and configured properly on instances you wish to target. ([Troubleshooting the SSM agent](https://aws.amazon.com/premiumsupport/knowledge-center/systems-manager-ec2-instance-not-appear/))
3. The CrowdStrike FalconPy SDK for Python
4. CrowdStrike API credentials with the following scopes:
    - Hosts: **READ**
    - Sensor Download : **READ**

### Automation scripts
The following scripts are provided as part of this solution. Some scripts are include only to assist with demonstrating and modifying this solution.

| Script name | Description |
| :--- | :--- |
| `apply_association.py` | This script will manually apply the SSM State Manager Association to the targets you've defined prior to the schedule you've assigned to your Association, allowing you to force the installation of the Falcon agent to newly created instances. |
| `build-helper.sh` | This script downloads CrowdStrike's latest AWS Lambda Layer for the [CrowdStrike Python SDK](https://github.com/CrowdStrike/falconpy). This layer archive is then updated to contain all of the necessary helper scripts for this integration and saved as `agent-handler.zip`. This file is then used as an attachment to the SSM Deployment document. Running this script is only required if you make changes to `cs_install_automation.py`. If you run this helper, you will need to update the SHA256 parameter provided to the CFT to match. |
| `create-package.sh` | This script downloads the CrowdStrike packager application and a Falcon sensor download sample from GitHub. These scripts are used to download the appropriate versions of the Falcon Sensor (Windows, Amazon Linux) and then packages these binary and installation/uninstallation scripts for each operating system, uploads them to a new or existing S3 bucket you specify, and then creates the AWS SSM Distributor package. This Distributor package is later used by AWS SSM Automation to manage the deployment of the Falcon Agent for the lifecycle of the targeted instance. |
| `cs_install_automation.py` | Collection of python scripts leveraging the [CrowdStrike Python SDK](https://github.com/CrowdStrike/falconpy) to lookup tenant details and delete agents for terminated hosts. This file is bundled within the `agent-handler.zip` file. |
| `helper-sha.sh` | Calculates the SHA256 value for the current version of the `agent-handler.zip` file. Provided if changes are required to `cs_install_automation.py`. |

### Deployment steps
This solution can be deployed to your AWS environment quickly.

> Reminder: This is a region specific deployment. To cover multi-region infrastructures, you will need to deploy this solution in each region you wish to manage.

#### Step 1. Clone this repository
Create a local copy of this solution.

```shell
git clone https://github.com/CrowdStrike/Cloud-AWS/ cs-cloud-aws
cd cs-cloud-aws/state-manager
```

#### Step 2. Create the SSM Distributor Package
AWS Distributor is leveraged to deploy the agent to new instances.

1. Navigate to the `ssm-distributor` folder and execute the `create-package.sh` helper script.

    ```shell
    cd ssm-distributor
    ./create-package..sh [FALCON API CLIENT ID] [FALCON API CLIENT SECRET] [AWS REGION] [SSM PACKAGE NAME] [S3 BUCKET NAME]
    ```

    **Example**

    ```shell
    cd ssm-distributor
    ./create-package.sh $MY_KEY $MY_SECRET us-east-2 CrowdStrike-Falcon-Agent cs-agent-deployment-my-company
    ```

    > This script will automatically create the S3 bucket if you've passed in a name to a bucket that does not exist.
    > For more details regarding the AWS Distributor integration for this solution, check the documentation located [here](ssm-distributor).

2. In your AWS Console, navigate to **Systems Manager** -> **Distributor** -> **_Owned by me_** and confirm that the package created successfully.

#### Step 3. Automation script upload
Upload the `agent-handler.zip` file to the `script` folder in the S3 bucket.

- Using the AWS CLI.

  ```shell
  aws s3 cp util/agent-handler.zip s3://{BUCKET_NAME}/script/
  ```

OR

- Navigate to the AWS console and upload the file directly to the `script` folder. Create this folder if it does not exist.

#### Step 4. Deploy the stack via CloudFormation
A CloudFormation template is used to stand up the infrastructure for this solution. You can deploy this template using the AWS Console or the command line.

##### Parameters
This CloudFormation template consumes the following parameters.

| Parameter | Description |
| :--- | :--- |
| `Action` | Should be left as `Install`. `Uninstall` is used for event-based decommissioning via EventBridge._<BR/><BR/>Default value: **Install**_ |
| `AutomationHandlerHash` | SHA256 hash of the `agent-handler.zip` file. This value only needs to be updated if you run the `build-helper.sh` utility.<BR/><BR/>This value must match the calculated SHA256 value of the `util/agent-handler.zip` file. A helper utility for calculating this value can be found in the same folder. (`helper-sha.sh`) |
| `EventBridgeExecutionRoleName` | Name of the IAM Role used by EventBridge to trigger the SSM Automation when an EC2 instance is terminated._<BR/><BR/>Default value_: **crowdstrike-eventbridge-execution-role** |
| `EventBridgeRuleName` | Name of the EventBridge Rule used to trigger the SSM Automation when an EC2 instance is terminated._<BR/><BR/>Default value_: **crowdstrike-falcon-agent-hide-host** |
| `FalconBaseUrl` | CrowdStrike Base URL identify. Select either `us1`, `us2`, `eu1` or `usgov1`. (Only required for `usgov1` customers.)_<BR/><BR/>Default value: **us1**_ |
| `FalconClientID` | CrowdStrike Falcon API Client ID with the **`Hosts: READ`** and **`Sensor Download: READ`** scopes.<BR/><BR/>**REQUIRED** |
| `FalconClientSecret` | CrowdStrike Falcon API Client Secret.<BR/><BR/>**REQUIRED** |
| `MaxConcurrency` | Percentage of total targets on which the SSM State Manager should run the SSM Automation on concurrently._<BR/><BR/>Default value: **100%**_ |
| `MaxErrors` | Threshold percentage of failed instances in your Association before SSM State Manager deems the Association as a failure._<BR/><BR/>Default value: **25%**_ |
| `S3BucketName` | Name of the S3 bucket used to store the CrowdStrike Falcon distributor package, and the agent installation helper script.<BR/><BR/>**REQUIRED** |
| `SSMAssociationName` | Name of the SSM State Manager Association used to manage the the lifecycle of the Falcon Agent._<BR/><BR/>Default value: **CrowdStrike-DeployFalconAgent**_ |
| `SSMAutomationAssumeRoleName` | Name of the IAM Role used by SSM Automation to manage the lifecycle of the Falcon Agent._<BR/><BR/>Default value: **crowdstrike-ssm-assume-role**_ |
| `SSMDocumentName` | Name of the SSM Document used to manage the manage the lifecycle of the Falcon Agent._<BR/><BR/>Default value: **CrowdStrike-DeployFalconAgent**_ |
| `SSMPackageName` | Name of the SSM Distributor package you created earlier in the guide. Leave this unchanged unless you passed a different value to the `-p` flag._<BR/><BR/>Default value_: **CrowdStrike-FalconAgent** |
| `SSMParamPrefix` | Prefix used for SSM parameter names created._<BR/><BR/>Default value: **CS-AGENT-AUTOMATION**_ |
| `ScheduleRateExpressions` | Rate at which SSM State Manager should re-apply the Association, expressed in [Rate Expressions](https://docs.aws.amazon.com/systems-manager/latest/userguid_e/reference-cron-and-rate-expressions.html). Associations support the following rate expressions: intervals of 30 minutes or greater and less than 31 days._<BR/><BR/>Default value: **30 minutes**_ |
| `TargetTagKey` | Name of the tag used to target the Association. _<BR/><BR/>Reference [Target Types](#target-types) for instructions on how to define this value.<BR/><BR/>Default value: **SENSOR_DEPLOY**_ |
| `TargetTagValue` | Value of the tag used to target the Association._<BR/><BR/>Reference [Target Types](#target-types) for instructions on how to define this value.<BR/><BR/>Default value: **TRUE**_ |

##### Deployment
AWS supports console or command line deployment for this solution.

- [AWS CLI deployment](#aws-cli-deployment)
- [AWS Console deployment](#aws-console-deployment)

###### AWS CLI deployment
You can deploy this stack using the AWS CLI from this folder using the following command.
Only required parameters are shown below, additional parameters may be added from the table above as necessary to meet the needs of your environment.

```shell
aws cloudformation create-stack --stack-name [STACK-NAME] \
  --template-body file://ssm_agent_deployment_by_tag.yaml \
  --parameters ParameterKey=FalconClientID,ParameterValue=[FalconClientID] \
    ParameterKey=FalconClientSecret,ParameterValue=[FalconClientSecret] \
    ParameterKey=S3BucketName,ParameterValue=[S3BucketName] \
  --region [AWS REGION] --capabilities CAPABILITY_NAMED_IAM
```

###### AWS Console deployment
To deploy this stack using the AWS console, follow the procedure below.

1. In your AWS Console, navigate to **CloudFormation** -> **Create stack** -> **With new resources (standard)**

2. Under **Specify template**, select **Upload a template file** and upload the `ssm_agent_deployment_by_tag.yaml` included in this solution, then click **Next**
   ![State Manager CFT Step 1](images/state-manager-cft-1.png)

3. Provide a **Stack name** and update the **Parameters** if the default values do not match your deployment:
   ![State Manager CFT Step 2](images/state-manager-cft-2.png)

4. Apply any additional tags or advanced configuration options necessary for your environment (none are required) and then click **Next**.
   ![State Manager CFT Step 3](images/state-manager-cft-3.png)

5. Review your selections, and then on the bottom of the page click the `I acknowledge that AWS CloudFormation might create IAM resources with custom names` check box. After doing so, click the **Create Stack** button.
   ![State Manager CFT Step 4](images/state-manager-cft-4.png)

6. Your stack will now start to deploy.
   ![State Manager CFT Deployment](images/state-manager-cft-deploy-1.png)

   You can click the refresh button to watch as the deployment progresses.
   ![State Manager CFT Deployment](images/state-manager-cft-deploy-2.png)

   You will be presented with a `CREATE_COMPLETE` message for the stack when the process has finished.
   ![State Manager CFT Deployment](images/state-manager-cft-deploy-complete.png)

> It takes approximately 2 to 3 minutes to stand up this solution using CloudFormation. Immediately after deployment completes, the Association is applied and all instances with the correct tag value combination will be processed for Falcon agent installation.

---

## Reviewing executions
All executions, either scheduled or triggered, will be shown in the AWS Systems Manager Automation dashboard. You can access this dashboard in the AWS Console under **AWS Systems Manager** -> **Automation**.

![AWS Systems Manager Automation dashboard](images/systems-manager-automation-executions.png)
