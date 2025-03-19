![](https://raw.githubusercontent.com/CrowdStrike/falconpy/main/docs/asset/cs-logo.png)

## AWS Account Registration

| Integration Name | Description |
|:-|:-|
| [Amazon Built In](https://github.com/aws-ia/cfn-abi-crowdstrike-fcs) | Use Amazon Built-In to register the AWS Organization or Control Tower with CrowdStrike Cloud Security. |
| [AWS CloudFormation or Terraform](aws-registration) | Use CloudFormation or Terraform templates to register the AWS Organization with CrowdStrike Cloud Security. |

## AWS Service Integrations

| Integration Name | Description |
|:-|:-|
| [AWS CloudTrail Lake with CrowdStrike](cloudtrail-lake) | Leverage the CrowdStrike Falcon Streaming API to log and store user activity data from the Falcon console in a seamless and efficient way with AWS CloudTrail Lake. |
| [AWS Network Firewall with CrowdStrike Threat Intelligence](https://github.com/CrowdStrike/aws-network-firewall) | Build capabilities such as automated blocking of malicious domains (via AWS Network Firewall) based on CrowdStrike detection alerts, or perform threat hunting derived from CrowdStrike domain-based Indicators of Activity (IOAs). |
| [AWS PrivateLink with CrowdStrike Sensor Proxy](aws-privatelink) | Leverage AWS PrivateLink to provide private connectivity between your CrowdStrike-protected workloads and the CrowdStrike cloud. |
| [AWS Security Hub with CrowdStrike Event Streams API](https://github.com/CrowdStrike/falcon-integration-gateway) | The Falcon Integration Gateway publishes detections identified by CrowdStrike Falcon for instances residing within Amazon Web Services (AWS) to AWS Security Hub. |
| [Amazon S3 Protected Bucket with CrowdStrike QuickScan Pro API](https://github.com/crowdstrike/cloud-storage-protection) | S3 Bucket Protection secures your Amazon S3 buckets by scanning files as they are uploaded using the CrowdStrike QuickScan Pro API. |
| [Amazon S3 Protected Bucket with CrowdStrike QuickScan ML API](s3-bucket-protection) (*Deprecated and slated for removal in 6 months*) | S3 Bucket Protection secures your Amazon S3 buckets by scanning files as they are uploaded using the CrowdStrike QuickScan ML API. |
| [AWS Verified Access with CrowdStrike Zero Trust Assessment (ZTA)](https://github.com/CrowdStrike/aws-verified-access) | Using CrowdStrike ZTA, we provide customers the ability to assess their endpoint security posture, allowing AWS Verified Access to provide conditional access to private applications that comply to your organization's device posture policies. |
| [Amazon Security Lake with CrowdStrike Falcon Data Replicator (FDR)](https://github.com/CrowdStrike/aws-security-lake) | Transforms your CrowdStrike FDR data into OCSF (Open Cybersecurity Schema Framework) and ingests it into your Amazon Security Lake for centralized management of your security-related logs. |
| [AWS Workspaces](workspaces) | Deploy the CrowdStrike Falcon sensor to AWS Workspaces. |

## CrowdStrike Sensor Automation

| Integration Name | Description |
|:-|:-|
| [AWS EC2 Image Builder](https://github.com/CrowdStrike/aws-ec2-image-builder) | AWS EC2 Image Builder components for Linux and Windows that install and configure the CrowdStrike Falcon sensor, preparing it as a golden image for your AWS environment. |
| [AWS Systems Manager](https://github.com/CrowdStrike/aws-ssm-distributor) | Utilize AWS Systems Manager to automatically deploy the CrowdStrike Falcon Sensor to your EC2 instances. |
| [AWS Autoscale Groups for Auto Register/Deregister](Agent-Install-Examples/Cloudformation/autoscale) | Utilize AWS Autoscale Groups to install the CrowdStrike Falcon Sensor during virtual machine initialization, and AWS Autoscale Lifecycle hooks to deregister the instance with CrowdStrike upon virtual machine termination. |
| [AWS EventBridge and AWS State Manager](state-manager) | Leverage AWS EventBridge and AWS Systems Manager State Manager to manage the deployment of the Falcon Agent and the removal of stale sensors. |
| [AWS Systems Manager Parameter Store with PowerShell Sensor Installation Script](Agent-Install-Examples/powershell) | Sample automation which leverages AWS Systems Manager Parameter Store to store CrowdStrike API credentials. These credentials are passed into a Microsoft PowerShell script to bootstrap the CrowdStrike Falcon Sensor for Windows during a Windows virtual machine's first boot process. |
| [AWS Systems Manager with Linux BASH Sensor Installation Script](Agent-Install-Examples/bash) | POSIX script that will install CrowdStrike sensor. The script is current tailored to the use within AWS Systems Manager, but can be used outside the Systems Manager. |
| [AWS Terraform Template for Sensor Installation](Agent-Install-Examples/Terraform-bootstrap-s3) | Sample AWS Terraform template that builds a test VPC, creates an Ubuntu-based web server, and automatically installs the CrowdStrike Falcon sensor into the virtual machine. |
