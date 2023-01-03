
# CrowdStrike Horizon
Horizon delivers continuous agentless discovery and visibility of cloud-native assets from the host to the cloud, providing valuable context and insights into the overall security posture and the actions required to prevent potential security incidents.
Horizon also provides intelligent agentless monitoring of cloud resources to detect *Indicators of Misconfiguration* (IOM) by assuming an IAM role in your accounts and making API queries to discover assets and assess their state.

CrowdStrike also observes EventBridge streams in near real time across all your accounts.  CrowdStrike applies algorithms that reveal adversarial or anomalous activities from the log file streams. It correlates new and historical events in real time while enriching the events with CrowdStrike threat intelligence data.  CrowdStrike will generate an *Indicator of Attack* if suspicious activity is detected. Each IOA is prioritized with the likelihood of activity being malicious via scoring and mapped to the MITRE ATT&CK framework.

CrowdStrikes adversary-focused approach provides real-time threat intelligence on 150+ adversary groups, 50+ IOA detections and guided remediation that improves investigation speed by up to 88%, enabling teams to respond faster and stop breaches.

![Horizon Data Flows)](imagesorizon-Data-Flows.png)

CrowdStrikes Org Registration Process is designed to support all AWS Organization setups including Control Tower. 

The following resources will be created

## IOM Scanning Resources
In order to monitor for *Indicators of Misconfiguration* an IAM role is required in each account.  The role is used by CrowdStrike to make API calls to discover assets in your account.

## IOA Scanning Resources
In order to perform IOA scanning CrowdStrike creates EventBridge Rules in each active region in each account that will forward cloudtrail events to an EventBus in a CrowdStrike account.  CrowdStrike uses these events to scan for *Indicators of Attack*.  For more information on sending events across accounts https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html For more information on CrowdStrike IOAs https://aws.amazon.com/blogs/architecture/detect-adversary-behavior-in-seconds-with-crowdstrike-and-amazon-eventbridge/


(Optional but recommended) Creates an additional *Organization Wide* CloudTrail in the master or delegated account to forward Read events from CloudTrail.  The additional trail is not created today as this is an additional cost item. 

> NOTE: IOA scanning involves the correlation of events that together indicate that an attack is in progress.  CrowdStrike attempts to detect these events where critical changes (mutable events) have been made to resources and correlates related *read* events to provide additional context.  EventBridge does not forward read events today and therefore we use CloudTrail to gather the additional *read* (immutab events).   Later this year both mutable and immutable events will be forwarded by EventBridge and we will no longer require CloudTrail.

## IOA Architecture diagram

![Architecture Diagram)](imagesrowdStrike-CT-arch.png)



## Resources Created

The following resources are created during the setup process

**Cloudformation Stacks**

*CrowdStrike-CSPM-Integration* -- Stackset that defines the IAM role and is applied to a single region in the **Master** account.

**Cloudformation StackSets**


* *CrowdStrike-CSPM-Integration* -- 
CrowdStrike-CSPM-Integration is a ``SERVICE-MANAGED`` Stackset that defines the IAM role that is assumed by CrowdStrike to discover resources in your account.  The StackSet is applied to all accounts in the organization.


* *CrowdStrike-CSPM-Integration-EB* -- CrowdStrike-CSPM-Integration-EB is a ``SERVICE-MANAGED`` Stackset that defines EventBridge rules that are applied to all regions in all member accounts that require monitoring.


* *CrowdStrike-CSPM-Integration-Root-EB* -- CrowdStrike-CSPM-Integration-Root-EB is a ``SELF-MANAGED`` Stackset that defines EventBridge rules that is applied to all regions in the **Master** account.


# CrowdStrike Discover

With CrowdStrike Discover for Cloud and Containers you can gain immediate and comprehensive visibility into all managed endpoints equipped with CrowdStrike Falcon workload security, and unmanaged assets across all accounts. In addition, Discover for Cloud and Containers is able to cross boundaries to see Amazon Virtual Private Cloud (Amazon VPC) and subnets, and collect data from all endpoints -- even those that are unmanaged -- as well as all hybrid infrastructure. The rich AWS content Discover for Cloud and Containers allows organizations to quickly understand and prioritize instances and immediately ensure that the Falcon sensor is fully deployed, dramatically improving organizations' security positions.

## Notable Changes from the Existing Discover Service
During account registration the required input parameters are now the account ID and optionally the AWS org (When registering an org)

The registration response will now contain both the RoleName and ExternalID that should be used in creating the IAM roles in each account.   

> Note: For more information on how the legacy Discocer service worked please see this guide. https://github.com/CrowdStrike/Cloud-AWS/tree/main/Discover-for-Cloud-Templates/AWS#how-crowdstrike-discover-works


![Discover Registration)](imagesiscover-Setup.png)


The diagram below shows the account setup process.

> Note: The master account requires the additional IAM permision **organizations:ListAccounts** permission in additional to the following permisions that must be applied to each role 
**ec2:DescribeInstances, ec2:DescribeImages, ec2:DescribeNetworkInterfaces, ec2:DescribeVolumes, ec2:DescribeVpcs, ec2:DescribeRegions, ec2:DescribeSubnets, ec2:DescribeNetworkAcls,ec2:DescribeSecurityGroups,iam:ListAccountAliases** 




![Discover Flow)](imagesiscover-v2-data-flows.png)

