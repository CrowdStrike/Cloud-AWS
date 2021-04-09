# Automating CrowdStrike Falcon Sensor for Windows Installation
This example demonstrates leveraging Microsoft PowerShell to bootstrap the CrowdStrike 
Falcon sensor onto a Windows host during first boot. This solution leverages AWS Systems 
Manager Parameter Store to store API credentials for use in calling the CrowdStrike 
Falcon API to download the appropriate sensor version.

> This demonstration provides two methods for testing, [CloudFormation](#cloudformation)
and [Terraform](#terraform).

+ [Requirements](#requirements)
+ [Creating the required SSM parameters](#creating-the-required-ssm-parameters)
+ [CloudFormation](#cloudformation)
+ [Terraform](#terraform)
+ [Bootstrap timing](#bootstrap-timing)

## Requirements
+ API Credentials for your CrowdStrike Falcon CID
+ SSM parameters created that contain the value for your API client ID and secret.

## Creating the required SSM parameters
This demonstration leverages AWS SSM Parameter Store to store the API client ID and secret
used to communicate with the CrowdStrike Falcon API.

Two parameters must be created for this demonstration to function. They may be named whatever
you wish and will be referenced when you import the template into CloudFormation, execute 
`create-stack` using the AWS CLI, or when you update your Terraform template file and execute 
`terraform apply`. You will create one parameter to store the API client ID and one parameter 
to store the API client secret. 

This image provides an example of creating a SSM parameter within the AWS console.

![Creating a SSM parameter](images/create-ssm-param.png)

> Please note: At this point in time, CloudFormation does not support accessing parameters
of type `SecureString` from SSM parameter store.

## CloudFormation
An example CloudFormation template has been developed to demonstrate how this solution can
be leveraged to deploy instances that automatically download the correct version of the
sensor and install it upon first boot.

+ [WindowsInstanceExample.yml](cloudformation/WindowsInstanceExample.yml) - Example CloudFormation 
template that creates a single security group and a single Windows Server instance.
    - Uses the most recent AMI available for Windows Server 2019 Full. 
    - The instance and security group will be deployed to your default VPC for the region the 
    Availability Zone resides within.
    - The instance and security group will be deployed to the default subnet for the Availability Zone.
    - This template can be uploaded directly to your AWS console or executed via the AWS CLI.

### Standing up the demonstration using the AWS Console
This template can be uploaded directly into CloudFormation within the AWS console and executed.

Login to the AWS Console and navigate to CloudFormation. If it is not already displayed, select
__Stacks__ from the left hand navigation. On the upper right of the page you should see a __Create Stack__
drop down menu. Click this drop down menu and select _With new resources (standard)_.

![Getting started](images/create-stack-dropdown.png)

On the next page select _Template is ready_, _Upload a template file_, and click the __Choose file__
button. Using the file dialog provided, navigate to the `WindowsInstanceExample.yml` file and click __Upload__.
When the file dialog closes, click the __Next__ button.

![Uploading the template](images/create-stack-template-upload.png)

Enter the necessary parameters as demonstrated in the image below. 

Once you have completed all values on the form, click the __Next__ button.

> Note: You are __not__ entering your Falcon client ID / secret in this dialog. You are entering
the names of the SSM parameters that are storing these values.

![Specifying the stack details](images/specify-stack-details.png)

On this next page you can select stack-specific options you may want to implement. The most common
example would be to specify additional custom tags that would be propagated to the instance
upon creation. Once you have specified all of your options, scroll to the bottom of the page
and click the __Next__ button.

![Configuring stack options](images/configure-stack-options.png)

The next page will confirm all of your choices. Carefully review the options you've selected
and when you are satisfied, click the __Create stack__ button.

> If you have not created your SSM parameters containing your API credentials
you will need to do so before proceeding to the next step.

![Create stack button](images/create-stack-button.png)

You will be brought back to the Stacks status dashboard and will see the stack initiating creation.

![Creation in progress](images/create-in-progress.png)

Within a few minutes, the stack will complete its work and the instance will be available.

![Creation complete](images/create-complete.png)


### Standing up the demonstration using the AWS CLI
The sample command below demonstrates how to utilize the AWS CLI to create a stack using the
provided template. The command below is a sample, and needs the following values updated to match
your environment.
+ `STACK_NAME` - The name to use for your CloudFormation stack.
+ `CLIENT_ID_PARAMETER_NAME` - The name of the SSM parameter to use for your Falcon Client ID. This
parameter must exist within the same region you specify as REGION.
+ `CLIENT_SECRET_PARAMETER_NAME` - The name of the SSM parameter to use for your Falcon Client Secret.
This parameter must exist within the same region you specify as REGION.
+ `TRUSTED_IP` - The IP address to provide RDP (TCP 3389) access to upon creation.
+ `AVAILABILITY_ZONE` - The availability zone to deploy the example instance to. This availability 
zone must reside within the same region you specify as REGION.
+ `KEY_PAIR_NAME` - The name of the key pair to use for the instance. This key pair must exist
within the same region as the region you specify as REGION.
+ `INSTANCE_TYPE` - The AWS Instance Type to use for the instance.
+ `INSTANCE_NAME` - The value to use for the name tag on the instance.
+ `REGION` - The AWS region where the instance and security group are deployed.

> If you have not created your SSM parameters containing your API credentials
you will need to do so before executing this command.

```bash
aws cloudformation create-stack --template-body file://WindowsInstanceExample.yml \
--stack-name STACK_NAME \
--parameters ParameterKey=FalconClientID,ParameterValue=CLIENT_ID_PARAMETER_NAME \
ParameterKey=FalconClientSecret,ParameterValue=CLIENT_SECRET_PARAMETER_NAME \
ParameterKey=TrustedIPAddress,ParameterValue=TRUSTED_IP/32 \
ParameterKey=InstanceExampleAvailabilityZone,ParameterValue=AVAILABILITY_ZONE \
ParameterKey=InstanceExampleKeyPairName,ParameterValue=KEY_PAIR_NAME \
ParameterKey=InstanceExampleInstanceType,ParameterValue=INSTANCE_TYPE \
ParameterKey=InstanceExampleName,ParameterValue=INSTANCE_NAME \
--region REGION
```

If successful, you will receive a response containing the request ID for this stack creation
request. The stack will take approximately 3 to 5 minutes to stand up the demonstration.

```bash
arn:aws:cloudformation:us-east-2:{ACCOUNT_ID}:stack/WindowsSensorExample2/72ee79f2-96ef-12ab-8554-02b5a70b77dc
```

## Terraform
An example Terraform template has been developed to demonstrate how this solution can
be leveraged to deploy instances that automatically download the correct version of the
sensor and install it upon first boot.

+ [WindowsInstanceExample.tf](terraform/WindowsInstanceExample.tf) - Example Terraform 
template that creates a single security group and a single Windows Server instance.
    - Uses the most recent AMI available for Windows Server 2019 Full. 
    - The instance and security group will be deployed to the VPC you specify.
    - The instance and security group will be deployed to the subnet you specify.
    - You must have Terraform installed in order to make use of this template.
    - Your installation of Terraform must be configured with appropriate AWS API credentials.

### Standing up the demonstration
Open the Terraform template in any editor and update the following values to reflect your environment:
+ `region` - The AWS region where the demonstration will be deployed.
+ `instance_name` - The name of the deployed instance.
+ `security_group_name` - The name of the deployed security group.
+ `instance_type` - The type of instance. (_Example: t2.micro_)
+ `key_name` - The name of the key pair to use for the instance. This key pair must reside
within the specified `region`.
+ `subnet_id` - The ID of the subnet to deploy the demonstration to. This subnet must
reside within the VPC specified by `vpc_id`.
+ `vpc_id` - The ID of the VPC to deploy the demonstration to. This VPC must reside
within the region specified by `region`.
+ `trusted_ip` - The IP address in CIDR format of the IP(s) to allow RDP access to the demonstration.
+ `client_id_ssm_name` - The name of the SSM parameter storing your Falcon API client ID.
+ `client_secret_ssm_name` - The name of the SSM parameter storing your Falcon API client secret.

> Do __not__ enter your CrowdStrike Falcon API credentials into this file.

Open a terminal shell and navigate to the folder where the Terraform template `WindowsInstanceExample.tf`
resides and execute the following command:
```shell
terraform init
```
If your Terraform installation is working and you are in the right directory, you should see 
something similar to the following:
```shell
Initializing the backend...

Initializing provider plugins...
- Finding latest version of hashicorp/aws...
- Installing hashicorp/aws v3.36.0...
- Installed hashicorp/aws v3.36.0 (signed by HashiCorp)

The following providers do not have any version constraints in configuration,
so the latest version was installed.

To prevent automatic upgrades to new major versions that may contain breaking
changes, we recommend adding version constraints in a required_providers block
in your configuration, with the constraint strings suggested below.

* hashicorp/aws: version = "~> 3.36.0"

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

Confirm the template and your settings by executing the command:

```shell
terraform plan
```

If there are no errors in the template, you will see a display similar to the following:

```shell
Refreshing Terraform state in-memory prior to plan...
The refreshed state will be used to calculate this plan, but will not be
persisted to local or remote state storage.

data.aws_ssm_parameter.falcon_client_id: Refreshing state...
data.aws_ssm_parameter.falcon_client_secret: Refreshing state...
data.aws_ami.windows: Refreshing state...

------------------------------------------------------------------------

An execution plan has been generated and is shown below.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.windows_example_instance will be created
  + resource "aws_instance" "windows_example_instance" {
      + ami                          = "ami-0db6a09e9ade44bb3"
      + arn                          = (known after apply)
      + associate_public_ip_address  = (known after apply)
      + availability_zone            = (known after apply)
      + cpu_core_count               = (known after apply)
      + cpu_threads_per_core         = (known after apply)
      + get_password_data            = false
      + host_id                      = (known after apply)
      + id                           = (known after apply)
      + instance_state               = (known after apply)
      + instance_type                = "t2.micro"
      + ipv6_address_count           = (known after apply)
      + ipv6_addresses               = (known after apply)
      + key_name                     = "REDACTED"
      + outpost_arn                  = (known after apply)
      + password_data                = (known after apply)
      + placement_group              = (known after apply)
      + primary_network_interface_id = (known after apply)
      + private_dns                  = (known after apply)
      + private_ip                   = (known after apply)
      + public_dns                   = (known after apply)
      + public_ip                    = (known after apply)
      + secondary_private_ips        = (known after apply)
      + security_groups              = (known after apply)
      + source_dest_check            = true
      + subnet_id                    = "subnet-REDACTED"
      + tags                         = {
          + "Name"             = "WindowsInstanceExample"
        }
      + tenancy                      = (known after apply)
      + user_data                    = "3ac9124967385fb10fdf03f32f4fe6a387eda509"
      + vpc_security_group_ids       = (known after apply)

      + ebs_block_device {
          + delete_on_termination = (known after apply)
          + device_name           = (known after apply)
          + encrypted             = (known after apply)
          + iops                  = (known after apply)
          + kms_key_id            = (known after apply)
          + snapshot_id           = (known after apply)
          + tags                  = (known after apply)
          + throughput            = (known after apply)
          + volume_id             = (known after apply)
          + volume_size           = (known after apply)
          + volume_type           = (known after apply)
        }

      + enclave_options {
          + enabled = (known after apply)
        }

      + ephemeral_block_device {
          + device_name  = (known after apply)
          + no_device    = (known after apply)
          + virtual_name = (known after apply)
        }

      + metadata_options {
          + http_endpoint               = (known after apply)
          + http_put_response_hop_limit = (known after apply)
          + http_tokens                 = (known after apply)
        }

      + network_interface {
          + delete_on_termination = (known after apply)
          + device_index          = (known after apply)
          + network_interface_id  = (known after apply)
        }

      + root_block_device {
          + delete_on_termination = (known after apply)
          + device_name           = (known after apply)
          + encrypted             = (known after apply)
          + iops                  = (known after apply)
          + kms_key_id            = (known after apply)
          + tags                  = (known after apply)
          + throughput            = (known after apply)
          + volume_id             = (known after apply)
          + volume_size           = (known after apply)
          + volume_type           = (known after apply)
        }
    }

  # aws_security_group.windows_example_security_group will be created
  + resource "aws_security_group" "windows_example_security_group" {
      + arn                    = (known after apply)
      + description            = "Allowed RDP traffic from trusted IP"
      + egress                 = [
          + {
              + cidr_blocks      = [
                  + "0.0.0.0/0",
                ]
              + description      = ""
              + from_port        = 0
              + ipv6_cidr_blocks = []
              + prefix_list_ids  = []
              + protocol         = "-1"
              + security_groups  = []
              + self             = false
              + to_port          = 0
            },
        ]
      + id                     = (known after apply)
      + ingress                = [
          + {
              + cidr_blocks      = [
                  + "REDACTED/32",
                ]
              + description      = ""
              + from_port        = 3389
              + ipv6_cidr_blocks = []
              + prefix_list_ids  = []
              + protocol         = "tcp"
              + security_groups  = []
              + self             = false
              + to_port          = 3389
            },
        ]
      + name                   = "WindowsExampleSecurityGroup"
      + name_prefix            = (known after apply)
      + owner_id               = (known after apply)
      + revoke_rules_on_delete = false
      + vpc_id                 = "vpc-REDACTED"
    }

Plan: 2 to add, 0 to change, 0 to destroy.

------------------------------------------------------------------------

Note: You didn't specify an "-out" parameter to save this plan, so Terraform
can't guarantee that exactly these actions will be performed if
"terraform apply" is subsequently run.
```

At this point, you are ready to stand up the demonstration environment. 

> If you have not created your SSM parameters containing your API credentials
you will need to do so before proceeding to the next step.

Execute the command:

```shell
terraform apply
```

If you wish to skip the review of your plan, execute the command as follows.

```shell
terraform apply -auto-approve
```

Terraform will then stand up the environment as specified.

```shell
data.aws_ssm_parameter.falcon_client_secret: Refreshing state...
data.aws_ssm_parameter.falcon_client_id: Refreshing state...
data.aws_ami.windows: Refreshing state...
aws_security_group.windows_example_security_group: Creating...
aws_security_group.windows_example_security_group: Still creating... [10s elapsed]
aws_security_group.windows_example_security_group: Still creating... [20s elapsed]
aws_security_group.windows_example_security_group: Still creating... [30s elapsed]
aws_security_group.windows_example_security_group: Creation complete after 35s [id=sg-0171cREDACTED]
aws_instance.windows_example_instance: Creating...
aws_instance.windows_example_instance: Still creating... [10s elapsed]
aws_instance.windows_example_instance: Still creating... [20s elapsed]
aws_instance.windows_example_instance: Still creating... [30s elapsed]
aws_instance.windows_example_instance: Still creating... [40s elapsed]
aws_instance.windows_example_instance: Still creating... [50s elapsed]
aws_instance.windows_example_instance: Still creating... [1m0s elapsed]
aws_instance.windows_example_instance: Creation complete after 1m0s [id=i-0a218bREDACTED]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

windows_example_instance_external_ip = Demonstration RDP address: AA.BB.CC.XX
Retrieve the Administrator password from the AWS console.
```

## Bootstrap timing
Typically, you should be able to retrieve the Windows Administrator password for the demonstration
instance from the AWS console within 3 - 5 minutes of the instance being created. 

The CrowdStrike Falcon sensor agent will be installed to the instance as it completes its first 
boot tasks. On average, this process takes approximately 5 minutes.
