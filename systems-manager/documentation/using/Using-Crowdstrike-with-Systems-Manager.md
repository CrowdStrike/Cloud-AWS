Using Systems Manager
=====================

Check that your environment meets the prerequisites for Systems Manager

<https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-prereqs.html>


# Important Information: 

* The DEFAULT version of the package will be (latest-release)-2. For example
if the latest release of the linux sensor is 5.34.9918 the DEFAULT version installed would be 5.33.9808.  
It is expected that once installed, sensor versions will be managed via the falcon console.

![](./media/downloads.png) 

# Managing Sytems Agent Versions
AWS releases a new version of SSM Agent when we they update Systems Manager capabilities. This solution requires version 2.3.1550.0 or later. We recommend that you automate the process of updating SSM Agent on your instances using any of the following methods.

[https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent-automatic-updates.html](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent-automatic-updates.html)
* You can configure all instances in your AWS account to automatically check for and download new versions of SSM Agent. To do this, choose Agent auto update on the Managed instances page in the AWS Systems Manager console (Recommended)

* You can use State Manager to create an association that automatically downloads and installs SSM Agent on your instances. If you want to limit the disruption to your workloads, you can create a Systems Manager maintenance window to perform the installation during designated time periods.



## Installing the CrowdStrike Falcon agent 
### Installing With the GUI
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

Addtional information for installing the Windows sensor [https://falcon.crowdstrike.com/support/documentation/23/falcon-sensor-for-windows](https://falcon.crowdstrike.com/support/documentation/23/falcon-sensor-for-windows)

Addtional information for installing the Linux sensor [https://falcon.crowdstrike.com/support/documentation/20/falcon-sensor-for-linux](https://falcon.crowdstrike.com/support/documentation/20/falcon-sensor-for-linux)


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

### Installing With the CLI

The CrowdStrike agent is installed with a automation document as described in the earlier section.  The document is
 
[Crowdstrike-FalconSensorDeploy.yml](./documents/Crowdstrike-FalconSensorDeploy.yml)


To start the installation process via the cli use the **aws ssm start-automation-execution** command.
 [https://docs.aws.amazon.com/cli/latest/reference/ssm/start-automation-execution.html](https://docs.aws.amazon.com/cli/latest/reference/ssm/start-automation-execution.html)
 
 ```console
aws ssm start-automation-execution --document-name "Crowdstrike-FalconSensorDeploy" -document-version "\$DEFAULT" --parameters '{"InstallerParams":["--tags=\"CrowdStrike SSMAutomationTest\""],"Action":["Install"],"InstallationType":["Uninstall and reinstall"],"PackageName":["FalconSensor-Windows"],"PackageVersion":["5.36.xxxx"],"APIGatewayHostKey":["CS_API_GATEWAY_HOST"],"APIGatewayClientIDKey":["CS_API_GATEWAY_CLIENT_ID"],"APIGatewayClientSecretKey":["CS_API_GATEWAY_CLIENT_SECRET"],"InstanceIds":["i-0axxxyyyzzzc12345"],"AutomationAssumeRole":["xxxxxxxxxxxxxxxxxxx"]}' --region us-east-1
```

### Installing With Python

AWS provides a boto3 client for interaction with Systems Manager [https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#client)
The command [start_automation_execution(**kwargs)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.start_automation_execution) will begin the execution of the automation document.

An example python script is included [here](python-example/example_aws_ssm_package_installation.py)



## Troubleshooting


SSM Agent writes information about executions, commands, scheduled
actions, errors, and health statuses to log files on each instance. You
can view log files by manually connecting to an instance. Logs are
written to the following locations.

#### Linux logs
 ```console
/var/log/amazon/ssm/amazon-ssm-agent.log

/var/log/amazon/ssm/errors.log
```

#### Windows logs
```powershell

%PROGRAMDATA%\\Amazon\\SSM\\Logs\\amazon-ssm-agent.log

%PROGRAMDATA%\\Amazon\\SSM\\Logs\\errors.log
```

Installation of the CrowdStrike agent requires version x.xxx or later of
the systems manager agent.

1.  Check the version of the agent running on the host

On Windows run

```powershell
Get-WmiObject Win32_Product \| Where-Object {\$\_.Name -eq \'Amazon SSM Agent\'} \| Select-Object Name,Version
```

On Amazon Linux and Amazon Linux 2

```shell script
yum info amazon-ssm-agent
```

![](.//media/image4.png)

2.  Check the Parameters Store

Verify the api keys are correct

![](.//media/image5.png)

3.  Check the agent logs

Look for the output in the log files

![](.//media/image6.png)
