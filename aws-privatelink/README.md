# Leverage AWS PrivateLink to provide private connectivity between your CrowdStrike-protected workloads and the CrowdStrike cloud

---

## Overview

By leveraging AWS PrivateLink, you can establish private connectivity between the CrowdStrike Falcon Sensor (running inside your workloads) and the CrowdStrike cloud. Additionally, all API calls to the CrowdStrike cloud are routed through AWS PrivateLink  e.g., (download sensor, get host details, etc.)

### DNS, VPC Endpoints, and Region Metadata

#### Falcon US-1

| DNS Name                  | Service Name    | VPC Endpoint Service Name                               | AWS Region | Availability Zones  |
|---------------------------|-----------------|---------------------------------------------------------|------------|---------------------|
| ts01-b.cloudsink.net      | Sensor Proxy    | com.amazonaws.vpce.us-west-1.vpce-svc-08744dea97b26db5d | us-west-1  | usw1-az1 & usw1-az3 |
| lfodown01-b.cloudsink.net | Download Server | com.amazonaws.vpce.us-west-1.vpce-svc-0f9d8ca86ddcb7106 | us-west-1  | usw1-az1 & usw1-az3 |

#### Falcon US-2

| DNS Name                             | Service Name    | VPC Endpoint Service Name                               | AWS Region | Availability Zones  |
|--------------------------------------|-----------------|---------------------------------------------------------|------------|---------------------|
| ts01-gyr-maverick.cloudsink.net      | Sensor Proxy    | com.amazonaws.vpce.us-west-2.vpce-svc-08a5bb05d337fd834 | us-west-2  | usw2-az1 & usw2-az2 |
| lfodown01-gyr-maverick.cloudsink.net | Download Server | com.amazonaws.vpce.us-west-2.vpce-svc-0e11def2d8620ae74 | us-west-2  | usw2-az1 & usw2-az2 |

#### Falcon EU-1

| DNS Name                             | Service Name    | VPC Endpoint Service Name                                 | AWS Region   | Availability Zones  |
|--------------------------------------|-----------------|-----------------------------------------------------------|--------------|---------------------|
| ts01-lanner-lion.cloudsink.net       | Sensor Proxy    | com.amazonaws.vpce.eu-central1.vpce-svc-0eb7b6ca4b7271385 | eu-central-1 | euc1-az1 & euc1-az2 |
| lfodown01-lanner-lion. cloudsink.net | Download Server | com.amazonaws.vpce.eu-central1.vpce-svc-0340142b9ab8fc564 | eu-central-1 | euc1-az1 & euc1-az2 |

## Quick Start Overview

The templates provided in this project demonstrate how to configure this functionality. The templates create the following resources:

| Resource | Description |
|:-|:-|
| Linux Virtual Machine | An EC2 machine where you'll install the CrowdStrike agent. |
| Test VPC | Simulates real-world deployment scenario of workloads being protected in a project-specific VPC. |
| CrowdStrike Shared Services VPC | Demonstrates the use of AWS PrivateLink to provide private connectivity to the CrowdStrike Cloud via a shared service VPC dedicated based on AWS best practice recommendations.|

The VPCs are connected over an AWS Transit Gateway and enabled for DNS resolution. A Route53 private hosted zone is created for domain `cloudsink.net` and associated with the **Test VPC**. The private hosted zone contains A records that alias to the VPC endpoints associated with the Falcon Platform.

For visualization purposes, here is a reference diagram showing the AWS architectural components and network traffic flow:

![PrivateLink Demo](./docs/images/privatelink-demo.png)

### Configuration

1. Create an S3 bucket in the region where you wish to deploy the demo.

2. Copy the files from [https://github.com/CrowdStrike/Cloud-AWS/tree/master/aws-privatelink/s3bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/aws-privatelink/s3bucket) to the newly created S3 bucket.

![](docs/images/s3bucket-sm.png)

1. Create a CloudFormation Stack using the following template: [https://github.com/CrowdStrike/Cloud-AWS/blob/master/aws-privatelink/cloudformation/create-vpc-endpoint-r53-tgw-attachment.yaml](https://github.com/CrowdStrike/Cloud-AWS/blob/master/aws-privatelink/cloudformation/create-vpc-endpoint-r53-tgw-attachment.yaml).
<br/><br/>

4. Verify that the CloudFormation template has been created successfully.

![](docs/images/cft-output-sm.png)

5. Connect to the Linux EC2 instance and verify that the private hosted domain has been shared with the Test VPC.

![](docs/images/dnstest-sm.png)

6. Download and install the CrowdStrike sensor.
