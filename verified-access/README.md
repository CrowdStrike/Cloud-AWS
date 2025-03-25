# Securing private applications with CrowdStrike and AWS Verified Access

AWS Verified Access delivers secure access to private applications without a VPN by continuously evaluating each request in real time based on contextual security signals like identity, device security status and location. The service then grants access based on the configured security policy for each application and connects the users, thereby improving the security posture of the organization. CrowdStrike customers leverage Falcon sensor's deep inspection and CrowdStrike Threat Graph® analytics to provide highly accurate security posture scores for the service's access decisions.

## Table of Contents

- [Overview](#overview)
  - [AWS Verified Access Integration Architecture](#aws-verified-access-integration-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Guides](#guides)
- [Quick Start Guide](#quick-start-guide)
  - [1. Create the CrowdStrike trust provider](#1-create-the-crowdstrike-trust-provider)
  - [2. Attach CrowdStrike trust provider to existing Verified Access Instance](#2-attach-crowdstrike-trust-provider-to-existing-verified-access-instance)
  - [3. Configure group-level access policy](#3-configure-group-level-access-policy)
    - [Modify existing Verified Access group](#modify-existing-verified-access-group)
    - [Create a new Verified Access group](#create-a-new-verified-access-group)
  - [4. Install the Native Message Host](#4-install-the-native-message-host)
    - [Windows](#windows)
  - [5. Install the browser extension](#5-install-the-browser-extension)
  - [6. Test connectivity to your application](#6-test-connectivity-to-your-application)
- [Reference Guide](#reference-guide)
  - [Prerequisite](#prerequisite)
  - [1. Deploy the private application](#1-deploy-the-private-application)
  - [2. Setup an OIDC-compliant identity provider](#2-setup-an-oidc-compliant-identity-provider)
  - [3. Create an AWS Verified Access instance](#3-create-an-aws-verified-access-instance)
  - [4. Create AWS Verified Access trust providers](#4-create-aws-verified-access-trust-providers)
    - [4.1. Create the Okta trust provider](#41-create-the-okta-trust-provider)
    - [4.2. Create the CrowdStrike trust provider](#42-create-the-crowdstrike-trust-provider)
  - [5. Attach the trust providers](#5-attach-the-trust-providers)
    - [5.1. Attach the Okta trust provider](#51-attach-the-okta-trust-provider)
    - [5.2. Attach the CrowdStrike trust provider](#52-attach-the-crowdstrike-trust-provider)
  - [6. Create an AWS Verified Access group](#6-create-an-aws-verified-access-group)
  - [7. Create a certificate](#7-create-a-certificate)
  - [8. Create your AWS Verified Access Endpoint](#8-create-your-aws-verified-access-endpoint)
  - [9. Update the DNS records](#9-update-the-dns-records)
  - [10. Update the Identity Provider settings](#10-update-the-identity-provider-settings)
  - [11. Install the Native Message Host](#11-install-the-native-message-host)
    - [Windows](#windows-1)
  - [12. Install the browser extension](#12-install-the-browser-extension)
  - [13. Verification](#13-verification)
- [Support](#support)
- [Resources](#resources)

## Overview

AWS Verified Access provides secure access to private applications (non-internet routable) hosted in an Amazon Virtual Private Cloud (Amazon VPC) by acting as a reverse proxy. It does this by providing identity and device posture checks before routing the traffic to the application. Using CrowdStrike Zero Trust Assessment (CrowdStrike ZTA), we provide customers the ability to assess their endpoint security posture, allowing AWS Verified Access to provide conditional access to resources that comply with your organization's device posture policies.

AWS Verified Access relies on these primary components for it to work properly:

1. Setting up the AWS Verified Access components i.e., (AWS Verified Access instances, access groups, access policies, endpoints, and trust providers).
1. Browser extensions that are installed on client endpoints for device posture evaluation.
1. An installer that sets up a [Native Message](https://developer.chrome.com/docs/apps/nativeMessaging/) Host. The host is responsible for reading the CrowdStrike ZTA score and securely communicating the payload to the browser extension.

### AWS Verified Access Integration Architecture

![AWS CRWD Verified Access Diagram](./assets/CrowdStrike_AWS_Verified_Access_Diagram.png)

## Getting Started

### Prerequisites

The following requirements must be met before you will be able to deploy or use this solution:

1. Have a current CrowdStrike Insights XDR subscription
1. Raise a ticket with [CrowdStrike support](https://supportportal.crowdstrike.com/) to have the ZTA file deployed to your environment by enabling the following feature flag: `zta_distribute_payload`
1. You must have an OIDC-compliant Identity Provider (IdP) configured to setup AWS Verified Access
    > See [Step 2](#2-setting-up-your-oidc-compliant-identity-provider) of the quick-start guide for setting up an example OIDC provider
    > if you don't have one.
1. Access to the AWS Command Line Interface (AWS CLI) as well as the AWS Management Console
1. A Windows endpoint with the Falcon sensor installed
   > This endpoint will get the Native Messaging installer and browser extension installed

### Guides

The CrowdStrike AWS Verified Access integration is broken down into 2 different guides, depending
on your use cases.

- [Quick Start Guide](#quick-start-guide) - The necessary components needed to complete the integration. This assumes all other AWS Verified Access components have already been established.
- [Reference Guide](#reference-guide) - A step-by-step guide, to include examples for setting up an OIDC provider, an example
private application, and all the AWS Verified Access components.

## Quick Start Guide

> :warning: Examples below use us-west-2 as the AWS Region. Please use your Region accordingly.

### 1. Create the CrowdStrike trust provider

1. Replace the following values in the command below before running:

   `{{ TenantId }}` with your CrowdStrike Customer ID (CCID)
   > :exclamation: The CCID used here is a lowercase version, excluding the checksum value.</br>
   >
   > **Example**: ABCD123456789EFG-1X would translate to: abcd123456789efg

   ```shell
   aws ec2 create-verified-access-trust-provider \
   --trust-provider-type device \
   --policy-reference-name "crowdstrike" \
   --device-trust-provider-type crowdstrike \
   --device-options \
   "TenantId={{ TenantID }}" \
   --region us-west-2 \
   --description "CrowdStrike trust provider"
   ```

1. Save the value of `VerifiedAccessTrustProviderId`

### 2. Attach CrowdStrike trust provider to existing Verified Access Instance

1. Replace the following values in the command below before running:

   `{{ Verified Instance ID }}` with your existing Verified Access Instance

   `{{ CrowdStrike Trust Provider ID }}` with the `VerifiedAccessTrustProviderId` value from the previous step

   ```shell
   aws ec2 attach-verified-access-trust-provider \
   --verified-access-instance-id "{{ Verified Instance ID}}" \
   --verified-access-trust-provider-id "{{ CrowdStrike Trust Provider ID}}" \
   --region us-west-2
   ```

### 3. Configure group-level access policy

Please choose the appropriate steps below based on your current situation:

#### Modify existing Verified Access group

1. Replace the following values in the command below before running:

   `{{ Verified Group ID }}` with your existing Verified Access group

   `{{ CrowdStrike Assessment Score }}` with your ZTA score criteria
   > This is a numerical value from 0-100

   ```shell
   aws ec2 modify-verified-access-group-policy \
   --policy-enabled \
   --verified-access-group-id {{ Verified Group ID }} \
   --policy-document \
   "permit(principal,action,resource) when {\
      context.crowdstrike.assessment.overall > {{ CrowdStrike Assessment Score }}\
   };" \
   --region us-west-2
   ```

#### Create a new Verified Access group

1. Replace the following values in the command below before running:

   `{{ Verified Instance ID }}` with your existing Verified Access instance

   `{{ CrowdStrike Assessment Score }}` with your ZTA score criteria
   > This is a numerical value from 0-100

   ```shell
   aws ec2 create-verified-access-group \
   --verified-access-instance-id {{ Verified Instance ID }} \
   --policy-document \
   "permit(principal,action,resource) when {\
      context.crowdstrike.assessment.overall > {{ CrowdStrike Assessment Score }}\
   };" \
   --region us-west-2 \
   --description "CrowdStrike + AWS Verified Access Demo | Threshold Example"
   ```

1. Save the value of `VerifiedAccessGroupId` and use it when creating/modifying your Verified Access endpoint.

### 4. Install the Native Message Host

Install the Native Message Host on your client endpoint. This will allow the AWS Verified Access browser extension to get the client endpoint's CrowdStrike ZTA score.

> :warning: **Currently only works on Windows** <br>
>
> AWS Verified Access is currently available for Windows clients while the service is in public preview. Support for macOS will be introduced at service launch.

#### Windows

1. Download the MSI via the [following link](https://d3p8dc6667u8pq.cloudfront.net/WPF/latest/AWS_Verified_Access_Native_Messaging_Host.msi)
1. Install the MSI on your Windows client endpoint

### 5. Install the browser extension

In this step, you'll install the AWS Verified Access browser extension on your client endpoint. In this example, we'll be using the Chrome browser. However, AWS Verified Access supports Firefox, too and the instructions are nearly identical.

1. Navigate to the [Chrome Extension Store](https://chrome.google.com/webstore/category/extensions)
1. Search for `AWS Verified Access` and install the extension

### 6. Test connectivity to your application

Enter your application's domain name into your web browser. The request should be allowed and you should be redirected to the application.

## Reference Guide

The following guide provides step-by-step instructions that showcase a sample application that's protected by AWS Verified Access, Okta (for OIDC), and CrowdStrike Zero Trust Assessment (for Device Posture). The solution will be deployed in `us-west-2`. If you'd like to deploy this elsewhere, please update the region in all commands referenced below.

### Prerequisite

- A managed domain name to use for the application, such as `www.myapp.example.com`
   > This guide uses AWS Route 53 to manage DNS settings

### 1. Deploy the private application

We'll be deploying an internal Application Load Balancer (ALB) through CloudFormation. The only function of this ALB is to emulate a private application by mocking a response on a successful hit.

1. Deploy the CloudFormation template in your respective AWS Account and Region
   - Right Click [here](https://github.com/CrowdStrike/cloud-aws/blob/main/verified-access/infrastructure/cfn-alb.json?raw=1) and *Save Link As..* to download the file
      > :exclamation: Ensure you save the file with **.json** extension

1. Once deployment is complete, refer to the CloudFormation Stack Output and collect the following information that will be used when creating the AWS Verified Access Endpoint in a later section: `ALBArn`, `SecurityGroup`, `Subnet1`, `Subnet2`.

### 2. Setup an OIDC-compliant identity provider

In this guide, we'll be using a free trial version of Okta for our OIDC provider. If you prefer to follow along with another provider, the steps should be nearly identical.

1. Sign up for a [free trial](https://www.okta.com/free-trial/) of Okta's Workforce Identity Cloud
1. After logging in, navigate to your Okta Administrator page and select the ***Application*** option on the sidebar nav
1. Create a new application with an OIDC as the sign-in method
   <img src="assets/idp-setup-1.png" alt="Create a new application with an OIDC as the sign-in method" width="550" height="500">
1. Set the following parameters and click save:
   - **App integration name:** Any name
   - **Grant Type:** Authorization Code
   - **Controlled access**: Allow everyone in your organization to access
1. Save your `Client ID` and `Client Secret`
1. Save your Okta Tenant URL.
   1. Example: If your Okta Admin URL is <https://trial-11111-admin.okta.com>, then your Okta Tenant URL is <https://trial-11111.okta.com>

### 3. Create an AWS Verified Access instance

1. Create an AWS Verified Access Instance

   ```shell
   aws ec2 create-verified-access-instance \
   --region us-west-2 \
   --description "CrowdStrike + AWS Verified Access Demo"
   ```

1. Save the value of `VerifiedAccessInstanceId`

### 4. Create AWS Verified Access trust providers

Create two trust providers, one for your IdP and another for CrowdStrike.

#### 4.1. Create the Okta trust provider

1. Replace the following values in the command below before running:

   `{{ Okta Tenant URL }}`, `{{ Okta Client ID }}`, `{{ Okta Client Secret }}`

   ```shell
   aws ec2 create-verified-access-trust-provider \
   --trust-provider-type user \
   --policy-reference-name "okta" \
   --user-trust-provider-type oidc \
   --oidc-options \
   "Issuer={{ Okta Tenant URL }}, \
   AuthorizationEndpoint={{ Okta Tenant URL }}/oauth2/v1/authorize, \
   TokenEndpoint={{ Okta Tenant URL }}/oauth2/v1/token, \
   UserInfoEndpoint={{ Okta Tenant URL }}/oauth2/v1/userinfo, \
   ClientId={{ Okta Client ID }}, \
   ClientSecret={{ Okta Client Secret}}, \
   Scope='openid groups profile email'" \
   --region us-west-2 \
   --description "Okta OIDC trust provider"
   ```

1. Save the value of `VerifiedAccessTrustProviderId`

#### 4.2. Create the CrowdStrike trust provider

1. Replace the following values in the command below before running:

   `{{ TenantId }}` with your CrowdStrike Customer ID (CCID)
   > :exclamation: The CCID used here is a lowercase version, excluding the checksum value.</br>
   >
   > **Example**: ABCD123456789EFG-1X would translate to: abcd123456789efg

   ```shell
   aws ec2 create-verified-access-trust-provider \
   --trust-provider-type device \
   --policy-reference-name "crowdstrike" \
   --device-trust-provider-type crowdstrike \
   --device-options \
   "TenantId={{ TenantID }}" \
   --region us-west-2 \
   --description "CrowdStrike trust provider"
   ```

1. Save the value of `VerifiedAccessTrustProviderId`

### 5. Attach the trust providers

Attach the two Verified Access trust providers created in the previous step to the Verified Access instance created earlier.

#### 5.1. Attach the Okta trust provider

1. Replace the following values in the command below before running:

   `{{ Verified Instance ID }}` with your existing Verified Access Instance

   `{{ Okta Trust Provider ID }}` with the `VerifiedAccessTrustProviderId` value from [4.1](#41-create-your-okta-trust-provider)

   ```shell
   aws ec2 attach-verified-access-trust-provider \
   --verified-access-instance-id "{{ Verified Instance ID}}" \
   --verified-access-trust-provider-id "{{ Okta Trust Provider ID}}" \
   --region us-west-2
   ```

#### 5.2. Attach the CrowdStrike trust provider

1. Replace the following values in the command below before running:

   `{{ Verified Instance ID }}` with your existing Verified Access Instance

   `{{ CrowdStrike Trust Provider ID }}` with the `VerifiedAccessTrustProviderId` value from [4.2](#42-create-the-crowdstrike-trust-provider)

   ```shell
   aws ec2 attach-verified-access-trust-provider \
   --verified-access-instance-id "{{ Verified Instance ID}}" \
   --verified-access-trust-provider-id "{{ CrowdStrike Trust Provider ID}}" \
   --region us-west-2
   ```

### 6. Create an AWS Verified Access group

Define a policy that will determine access based on the OIDC IdP, device posture, and other parameters provided by the AWS Verified Access service. For this guide, we'll create a policy document that checks that the client has the CrowdStrike agent installed and has an overall ZTA score higher than 80.

> Clients will need to successfully log into your Identity Provider before the policy document is evaluated. As such, any identity provider conditions you set in your policy document are evaluated on top of the successful login.

1. Replace the following values in the command below before running:

   `{{ Verified Instance ID }}` with your existing Verified Access instance

   ```shell
   aws ec2 create-verified-access-group \
   --verified-access-instance-id {{ Verified Instance ID }} \
   --policy-document \
   "permit(principal,action,resource) when {\
      context.crowdstrike.assessment.overall > 80\
   };" \
   --region us-west-2 \
   --description "CrowdStrike + AWS Verified Access Demo | Threshold Example"
   ```

1. Save the value of `VerifiedAccessGroupId`

### 7. Create a certificate

Use AWS Certificate Manager to create a certificate for the domain of your private application.

1. Navigate to the [AWS Certificate Manager](https://console.aws.amazon.com/acm) console page
1. Click `Request a certificate`
1. Select `Request a public certificate` and press `Next`
1. Type in the domain name of your application and press `Request`
   1. *This should belong to a domain that you manage, as you'll need to create DNS records in future steps*
1. Verify the certificate by creating the necessary CNAME records as instructed
1. Save the `ARN` of the certificate

### 8. Create your AWS Verified Access Endpoint

Bring everything together and create the AWS Verified Access Endpoint that will act as the reverse proxy for your private application.

> Please note that it takes 10-30 minutes for the endpoint to provision. If you make any changes to the endpoint, it will typically take 5-15 minutes for it to take into effect.

1. Replace the following values in the command below before running:

   `{{ Verified Access Group }}`, `{{ Certificate ARN }}`, `{{ Private Application Domain Name }}`, `{{ ALB ARN }}`, `{{ Subnet1 }}`, `{{ Subnet2 }}` and `{{ SecurityGroup }}`

   ```shell
   aws ec2 create-verified-access-endpoint \
   --verified-access-group-id {{ Verified Access Group }} \
   --endpoint-type load-balancer \
   --attachment-type vpc \
   --domain-certificate-arn {{ Certificate ARN }} \
   --application-domain {{ Private Application Domain Name }} \
   --endpoint-domain-prefix demo \
   --load-balancer-options \
   "LoadBalancerArn={{ ALB ARN }}, \
   Port=80, \
   Protocol=http, \
   SubnetIds={{ Subnet1 }}, {{ Subnet2 }} " \
   --security-group-ids {{ SecurityGroup }} \
   --region us-west-2 \
   --description "CrowdStrike + AWS Verified Access Demo"
   ```

1. Save the value of `VerifiedAccessEndpointId`, `EndpointDomain`, `ApplicationDomain`, and `DeviceValidationDomain`

1. Before moving on, ensure that the endpoint has been successfully provisioned

   ```shell
   aws ec2 describe-verified-access-endpoints --verified-access-endpoint-ids {{ VerifiedAccessEndpointId }} --region us-west-2
   ```

   You should see:

   ```json
      ...
      "Status": {
            "Code": "active"
      },
      ...
   ```

### 9. Update the DNS records

Update the DNS records to point your private application's domain name to the endpoint domain created by the AWS Verified Access Endpoint you created in the previous step. For this example, we'll assume that you're using Amazon Route53 to manage your domain's DNS. If you're using another DNS provider, please adjust the steps accordingly.

1. Navigate to Amazon Route53 console page -> Hosted Zones
1. Select the domain name for your private application
1. Press `Create record`
1. Type the domain name you created earlier and select `CNAME` as the Record type. Set the value of the record to be the value of `EndpointDomain` you saved in the previous step and press `Create records`

### 10. Update the Identity Provider settings

Update your Okta's application settings. Specifically, we'll be adding the AWS Verified Access URLs to the Sign-in redirect URIs. This will tell Okta to send the authentication response to these URLs.

1. Navigate to your Okta Administrator page and select the application you created
1. Press `Edit` under General Settings
1. Add the following URLs under ***Sign-in redirect URIs***:
   > Replace the placeholders `{{ ApplicationDomain }}` and `{{ DeviceValidationDomain }}` with the relevant values
   1. https://{{ ApplicationDomain }}/oauth2/idpresponse
   1. https://{{ DeviceValidationDomain }}/oauth2/idpresponse

### 11. Install the Native Message Host

Install the Native Message Host on the client endpoint. This will allow the AWS Verified Access browser extension to get the client endpoint's CrowdStrike ZTA score.

> :warning: **Currently only supported on Windows** <br>
>
> AWS Verified Access is currently available for Windows clients while the service is in public preview. Support for macOS will be introduced at service launch.

#### Windows

1. Download the MSI via the [following link](https://d3p8dc6667u8pq.cloudfront.net/WPF/latest/AWS_Verified_Access_Native_Messaging_Host.msi)
1. Install the MSI on your Windows client endpoint

### 12. Install the browser extension

Install the AWS Verified Access browser extension on your client endpoint. In this example, we'll be using the Chrome browser. However, AWS Verified Access also supports Firefox and the instructions are nearly identical.

1. Navigate to the [Chrome Extension Store](https://chrome.google.com/webstore/category/extensions)
1. Search for `AWS Verified Access` and install the extension

### 13. Verification

Verify that your private application is properly protected by AWS Verified Access.

1. Confirm that the AWS Verified Access Endpoint is successfully provisioned by running `aws ec2  describe-verified-access-endpoints --region us-west-2` and confirm that `Status.Code` is equal to `Active`
1. Navigate to your private application domain, which is the value of `ApplicationDomain`
1. Log into your identity provider
1. If you're navigating on a client machine that meets the criteria to access the private application, you'll see `Mock response`
1. If you're navigating on a client machine that doesn't meet the criteria, you'll see `Redirecting...`, which is the automated response from AWS Verified Access

## Support

The CrowdStrike AWS Verified Access integration is an open-source project and not a CrowdStrike product. As such, it carries no formal support, expressed, or implied. If you encounter any issues while deploying the integration, you can create an issue on our GitHub repository for bugs, enhancements, or other requests.

AWS Verified Access is an AWS product. As such, any questions or problems you experience with this service should be handled through a support ticket with AWS Support.

## Resources

[AWS Verified Access](https://docs.aws.amazon.com/verified-access/latest/ug/what-is-verified-access.html)
