Using Systems Manager
=====================

Check that your environment meets the prerequisites for Systems Manager

<https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-prereqs.html>

## Installing the CrowdStrike Falcon agent 
From the AWS console can be select the automation document under AWS Systems Manager \> Distributor \> Third
Party Apps > FalconSensor-(linux\|windows) 

Select "Install one time"


![](.//media/image1.png)

Complete the Input parameters form

![](.//media/image2.png)

The instances that will be targeted for install/uninstall can be
selected using the InstanceIds tab OR the Targets tab.

## InstanceIds

Select the instances that you wish to perform the action on

![](.//media/image3.png)

## Action

Select either "Install" or "Uninstall" for the action to perform on the
instance

## InstallerParams

**Windows installer parameters**

Windows installer parameters are shown below (Note: CID and ProvTroken
are already included)

Parameter     | Description                                        
-------------- |-------------------
 /install       | Installs the sensor (default)
 /passive       | Shows a minimal UI with no prompts.                
/quiet         | Shows no UI and no prompts
/norestart     | Prevents the host from restarting at the end of he sensor installation.                           |


**Linux installation Parameters**

  Parameter   |         Description
-------------- |-------------------
  \--aph       |        Proxy host
  \--app        |       Proxy port
  \--billing=metered  | Shows no UI and no prompts.

**Package Name**

Enter either FalconSensor-Windows or FalconSensor-linux

**PackageVersion**

Leave blank unless you wish to specify a specific version

**APIGatewayHostKey**

Check the value of the key CS_API_GATEWAY_HOST in the parameter store

**APIGatewayClientIDKey**

Check the value of the key CS_API_GATEWAY_CLIENT_ID in the parameter
store

**APIGatewayClientSecretKey**

Check the value of the key CS_API_GATEWAY_CLIENT_SECRET in the parameter
store

**Targets**

The Targets tab will select the instances using a filter that is
entered. For instance to target by tag enter
"Key=tag:Name,Values=January2018Backups". For more information regarding
Targets

<https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-working-targets.html>.

Targets is required if you don\'t provide one or more instance IDs in
the call.

**AutomationAssumeRole**

[Select a role that has the pre configured *AWS-SSM-ExecutionRole* policy
bound to it. If you have used the supplied cloudformation template to
setup the account select the role named
*Crowdstrike-SSMExecutionRole*



## Troubleshooting


SSM Agent writes information about executions, commands, scheduled
actions, errors, and health statuses to log files on each instance. You
can view log files by manually connecting to an instance. Logs are
written to the following locations.

#### Linux logs

/var/log/amazon/ssm/amazon-ssm-agent.log

/var/log/amazon/ssm/errors.log

#### Windows logs

%PROGRAMDATA%\\Amazon\\SSM\\Logs\\amazon-ssm-agent.log

%PROGRAMDATA%\\Amazon\\SSM\\Logs\\errors.log

Installation of the CrowdStrike agent requires version x.xxx or later of
the systems manager agent.

1.  Check the version of the agent running on the host

On Windows run

***Get-WmiObject Win32_Product \| Where-Object {\$\_.Name -eq \'Amazon
SSM Agent\'} \| Select-Object Name,Version***

On Amazon Linux and Amazon Linux 2

***yum info amazon-ssm-agent***

![](.//media/image4.png)

2.  Check the Parameters Store

Verify the api keys are correct

![](.//media/image5.png)

3.  Check the agent logs

Look for the output in the log files

![](.//media/image6.png)
