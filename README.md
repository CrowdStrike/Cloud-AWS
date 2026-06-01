![CrowdStrike Logo (Light)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-light-mode.png#gh-light-mode-only)
![CrowdStrike Logo (Dark)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-dark-mode.png#gh-dark-mode-only)

## AWS Account Registration

| Integration Name | Description |
|:-|:-|
| [Amazon Built In](https://github.com/aws-ia/cfn-abi-crowdstrike-fcs) | Use Amazon Built-In to register the AWS Organization or Control Tower with CrowdStrike Cloud Security. |
| [AWS SCP Analysis](https://github.com/CrowdStrike/aws-cspm-scp-analysis) | Analyze Service Control Policies (SCPs) in your AWS Organization to identify policies that may prevent CSPM onboarding. |
| [AWS CSPM Multi-CID](https://github.com/CrowdStrike/aws-cspm-registration-multi-cid/tree/main) | Use CloudFormation templates to register multiple Falcon CIDs to accounts within the AWS Organization. |

## AWS Service Integrations

| Integration Name | Description |
|:-|:-|
| [AWS ECR Registry Connections](https://github.com/CrowdStrike/cloud-registry-connections/tree/main/AWS) | Use CloudFormation to connect your ECR Registries for Image Assessment. |
| [AWS CloudTrail Lake with CrowdStrike](cloudtrail-lake) | Leverage the CrowdStrike Falcon Streaming API to log and store user activity data from the Falcon console in a seamless and efficient way with AWS CloudTrail Lake. |
| [AWS Network Firewall with CrowdStrike Threat Intelligence](https://github.com/CrowdStrike/aws-network-firewall) | Build capabilities such as automated blocking of malicious domains (via AWS Network Firewall) based on CrowdStrike detection alerts, or perform threat hunting derived from CrowdStrike domain-based Indicators of Activity (IOAs). |
| [AWS PrivateLink for CrowdStrike Falcon Sensor](https://github.com/crowdstrike/aws-privatelink) | Use AWS PrivateLink with cross-region connectivity to route CrowdStrike Falcon sensor traffic privately to the CrowdStrike cloud. |
| [AWS Security Hub with CrowdStrike Event Streams API](https://github.com/CrowdStrike/falcon-integration-gateway) | The Falcon Integration Gateway publishes detections identified by CrowdStrike Falcon for instances residing within Amazon Web Services (AWS) to AWS Security Hub. |
| [Amazon S3 Protected Bucket with CrowdStrike QuickScan Pro API](https://github.com/crowdstrike/cloud-storage-protection) | S3 Bucket Protection secures your Amazon S3 buckets by scanning files as they are uploaded using the CrowdStrike QuickScan Pro API. |
| [Amazon Security Lake with CrowdStrike Falcon Data Replicator (FDR)](https://github.com/CrowdStrike/aws-security-lake) | Transforms your CrowdStrike FDR data into OCSF (Open Cybersecurity Schema Framework) and ingests it into your Amazon Security Lake for centralized management of your security-related logs. |
| [AWS Verified Access with Falcon Insight XDR](verified-access) | Using CrowdStrike ZTA, we provide customers the ability to assess their endpoint security posture, allowing AWS Verified Access to provide conditional access to private applications that comply to your organization's device posture policies. |

## CrowdStrike Sensor Automation

| Integration Name | Description |
|:-|:-|
| [AWS Systems Manager](https://github.com/CrowdStrike/aws-ssm-distributor) | Utilize AWS Systems Manager to automatically deploy the CrowdStrike Falcon Sensor to your EC2 instances. |
| [AWS EC2 Image Builder](https://github.com/CrowdStrike/aws-ec2-image-builder) | AWS EC2 Image Builder components for Linux and Windows that install and configure the CrowdStrike Falcon sensor, preparing it as a golden image for your AWS environment. |
| [AWS EKS Protection](https://github.com/CrowdStrike/aws-eks-protection) | Automatically deploy the CrowdStrike Falcon Sensor to your EKS Clusters in AWS. |
| [AWS Elastic Beanstalk](beanstalk) | Examples of how to deploy the Falcon sensor in AWS Elastic Beanstalk Resources. |
| [AWS Workspaces](workspaces) | Deploy the CrowdStrike Falcon sensor to AWS Workspaces. |

## Deploy the CrowdStrike Falcon Platform with Zero Commitment

Stop trading security for speed. Onboard instantly via AWS Pay-as-You-Go (PAYG) and get the full power of Falcon deployed across your environments in minutes.

**What You Get:**

- **Frictionless Adoption:** Start securing production workloads and integrating logs instantly. You pay only for what you use, scaled automatically via AWS.

- **Real-Time Runtime Security:** Agent-based protection for your EC2 instances, EKS clusters, and Fargate containers. Detect and block threats before they impact your services.

- **Next-Gen SIEM:** Stop wasting time waiting for data. Ingest key AWS data sources in minutes for blazing-fast cross-domain insights and automated response actions.

Secure your cloud environment by deploying Falcon in minutes [directly from the AWS Marketplace.](https://aws.amazon.com/marketplace/pp/prodview-vubjuepxztndi)
