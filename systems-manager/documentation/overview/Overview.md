## Overview of the Setup Process. 

## Setting up and Using Systems Manager

![Setup Overview](images/systems-manager-private-package.png)

1) Customer downloads the files in this github repository and reviews the install and uninstall scripts provided.

2) Customer uploads package contents to an S3 bucket. 
The S3 bucket should contain a zip file for each supported OS and a manifest.json file.

3) Customer applies a CloudFormation template that sets up the required Parameters in the AWS parameter store. These parameters are required by the installation scripts. 
The cloudformation template will also create the distributor package in the customer account. 

4) System manager users can now use Run commands to install/uninstall the sensor on the EC2 instance. 



## Agent Install Process
 ![flows](images/sytems-manager-flows.png)

When a Systems manager administrator wishes to install the CrowdStrike sensor on an EC2 distance they will use a automation document to perform the task. 
During the agent install process the following tasks are performed.
1) Administrator invokes the automation script via the Systems Manager API, aws cli or Console.
2) The automation script retrieves the CrowdStrike API keys from the Systems Manager Parameter Store.
    - CS_API_GATEWAY_HOST: (CrowdStrike API 'api.crowdstrike.com')  
    - ACS_API_GATEWAY_CLIENT_ID: (CrowdStrike API Client ID Key) 
    - ACS_API_GATEWAY_CLIENT_SECRET: (CrowdStrike API Secret Key)
    
    ![Params](images/Parameter-store.png)

3) The automation script runs a python task that authenticates to the CrowdStrike API and generates an OAuth token
4) The automation script runs a python task that fetches the CID and installation token
5) The automation script then invokes the AWS `AWS-ConfigureAWSPackage` and passes the following parameters to it
    - SSM_CS_INSTALLTOKEN: (CrowdStrike Installation Token)  
    - SSM_CS_CCID: (CrowdStrike Customer CID) 
    - SSM_CS_INSTALLPARAMS: (Additional Install Params)
    - SSM_CS_AUTH_TOKEN: (CrowdStrike API OAuth2 token)

The `AWS-ConfigureAWSPackage` is a standard AWS package that invokes the process of delivering the software package to the instance and invoking the install/uninstall scripts. 




## Creating the Automation Document

```shell
python3 aws_ssm_automation_document_management.py --document_name=CS-FalconSensorDeploy-Test --source_file=../../aws-automation-doc/Crowdstrike-FalconSensorDeploy.yml --action=create --region=eu-west-1
```