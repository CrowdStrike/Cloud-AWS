# Cloud-AWS
A collection of projects supporting AWS Integration

## AWS Network Firewall Integration
[About the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/overview.md)

[Setting up the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/deployment.md)

[Running the Demo](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Network-Firewall/documentation/testing.md)

## Agent Install Examples
[AWS Terraform BootStrap S3](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Agent-Install-Examples/Terraform-bootstrap-s3)

[AWS Autoscale](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Agent-Install-Examples/Cloudformation/autoscale)

## Control Tower
Cloud Formation Templates and lambda functions to integrate Falcon Discover with AWS Control Tower

[Implementation Guide](https://github.com/CrowdStrike/Cloud-AWS/blob/master/Control-Tower/documentation/implementation-guide.md)

[Files](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower)

[Multiple Providers Require SNS notifications](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Control-Tower/multiple-sns)

## AWS Security Hub Integration/ Falcon Integration Gateway
[CrowdStrike FIG](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Falcon-Integration-Gateway)

## Discover for Cloud

This folder contains a number of templates for setting up AWS accounts with Discover.  The scripts all assume that you are using CloudTrail to write to an S3 bucket in a shared log Archive account. 

### Terraform

[Terraform templates for the log archive account creating new bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-new-S3-bucket-with-new-trail)

[Terraform templates for the log archive account using an existing bucket](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/log-archive-account-existing-S3-bucket-and-trail)

[Terraform templates for additional accounts creating new CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-new-trail)

[Terraform templates for additional accounts using and existing CloudTrail log](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/terraform/additional-account-existing-trail)

The python script "register_account.py" is included as an example of a script that should be run at the end of the terraform apply to register the AWS account with Crowdstrike.  The script may be run as part of a pipeline or as a local-exec process.

### CloudFormation

[See the README.md file here](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/cloudformation-templates)

## License

Copyright CrowdStrike 2020

By accessing or using this script, sample code, application programming interface, tools, and/or associated documentation (if any) (collectively, “Tools”), You (i) represent and warrant that You are entering into this Agreement on behalf of a company, organization or another legal entity (“Entity”) that is currently a customer or partner of CrowdStrike, Inc. (“CrowdStrike”), and (ii) have the authority to bind such Entity and such Entity agrees to be bound by this Agreement.

CrowdStrike grants Entity a non-exclusive, non-transferable, non-sublicensable, royalty free and limited license to access and use the Tools solely for Entity’s internal business purposes and in accordance with its obligations under any agreement(s) it may have with CrowdStrike. Entity acknowledges and agrees that CrowdStrike and its licensors retain all right, title and interest in and to the Tools, and all intellectual property rights embodied therein, and that Entity has no right, title or interest therein except for the express licenses granted hereunder and that Entity will treat such Tools as CrowdStrike’s confidential information.

THE TOOLS ARE PROVIDED “AS-IS” WITHOUT WARRANTY OF ANY KIND, WHETHER EXPRESS, IMPLIED OR STATUTORY OR OTHERWISE. CROWDSTRIKE SPECIFICALLY DISCLAIMS ALL SUPPORT OBLIGATIONS AND ALL WARRANTIES, INCLUDING WITHOUT LIMITATION, ALL IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT. IN NO EVENT SHALL CROWDSTRIKE BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE TOOLS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
