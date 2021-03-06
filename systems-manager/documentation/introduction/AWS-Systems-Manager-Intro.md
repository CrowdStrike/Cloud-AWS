AWS Systems Manager
===================

AWS Systems Manager allows you to centralize operational data from
multiple AWS services and automate tasks across your AWS resources.

Systems Manager Capabilities can be separated into four categories.
-------------------------------------------------------------------

### Monitor -- Monitor resources and applications

You can create logical groups of resources such as applications,
different layers of an application stack, or production versus
development environments. With Systems Manager, you can select a
resource group and view its recent API activity, resource configuration
changes, related notifications, operational alerts, software inventory,
and patch compliance status.

Systems Manager uses AWS CloudWatch for monitoring

### Audit -- Audit resource configurations, user access and policy enforcement

Systems Manager uses AWS CloudTrail AWS Config for Audit

### Manage -- Take operation action on resources

AWS Systems Manager allows you to safely automate common and repetitive
IT operations and management tasks. With Systems Manager Automation, you
can use predefined playbooks, or you can build, run, and share
wiki-style automated playbooks to enable AWS resource management across
multiple accounts and AWS Regions.

### Optimise -- Improve efficiency and security posture 

You can also take action on each resource group depending on your
operational needs. Systems Manager provides a central place to view and
manage your AWS resources, so you can have complete visibility and
control over your operations.

Systems Manager uses AWS Trusted Advisor, AWS Cost and Usage Report and
AWS Cost Explorer

CrowdStrike and AWS Systems Manager
-----------------------------------

AWS Systems Manager Distributor is a feature that you can use to
securely store and distribute software packages, such as software
agents, in your accounts. Distributor integrates with existing Systems
Manager features to simplify and scale the package distribution,
installation, and update process.

### Falcon Agent Installation

As part of Systems Manager Management capabilities, the Distributor
function provides a mechanism for installing the Falcon Agent on
instance types that support the systems manager agent.

Linux

SSM Agent is installed by default on Amazon Linux, Amazon Linux 2,
Ubuntu Server 16.04, and Ubuntu Server 18.04 LTS base EC2 AMIs.

Windows

SSM Agent is installed by default on instances created from Windows
Server 2016 and Windows Server 2019 Amazon Machine Images (AMIs), and on
instances created from Windows Server 2008-2012 R2 AMIs published in
November 2016 or later.

The SSM agent is supported on other operating systems but must be
installed manually

A complete list of supported systems can be found here.

<https://docs.aws.amazon.com/systems-manager/latest/userguide/prereqs-operating-systems.html>

Systems Manager uses "documents" to perform automation tasks. An AWS
Systems Manager document (SSM document) defines the actions that Systems
Manager performs on managed instances. Documents use JavaScript Object
Notation (JSON) or YAML, and they include steps and parameters that you
specify.

There are currently six types of document with Systems Manager but only
three directly relate to CrowdStrike Falcon agent.

| **Type** | **Use with** | **Details** |
| --- | --- | --- |
| Command document | [Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/execute-remote-commands.html)[State Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html)[Maintenance Windows](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-maintenance.html) | Run Command uses command documents to run commands. State Manager uses command documents to apply a configuration. These actions can be run on one or more targets at any point during the lifecycle of an instance. Maintenance Windows uses command documents to apply a configuration based on the specified schedule. |
| Automation document | [Automation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html)[State Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html)[Maintenance Windows](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-maintenance.html) | Use automation documents when performing common maintenance and deployment tasks such as creating or updating an Amazon Machine Image (AMI). State Manager uses automation documents to apply a configuration. These actions can be run on one or more targets at any point during the lifecycle of an instance. Maintenance Windows uses automation documents to perform common maintenance and deployment tasks based on the specified schedule. |
| Package document | [Distributor](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor.html) | In Distributor, a package is represented by an SSM document. A package document includes attached ZIP archive files that contain software or assets to install on managed instances. Creating a package in Distributor creates the package document. |

Package Documents
-----------------

After you create a package in Distributor, which creates an AWS Systems
Manager document, you can install the package in one of the following
ways.

-   One time by using [AWS Systems Manager Run
    Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/execute-remote-commands.html).

-   On a schedule by using [AWS Systems Manager State
    Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html).

You can use Run Command or State Manager to control which of your
managed instances get a package and which version of that package.
Managed instances can be grouped by instance IDs, AWS account numbers,
tags, or AWS Regions.

### Package document contents
A package is a collection of installable software or assets that
includes the following.

-   A zip file of software per target operating system platform. Each
    zip file must include the following.

    An install and an uninstall script. Windows Server-based instances require PowerShell scripts (scripts named install.ps1 and uninstall.ps1). Linux-based instances require shell scripts (scripts named install.sh and uninstall.sh).  SSM Agent reads and carries out the instructions in the install and uninstall scripts.

-   A JSON-formatted manifest file that describes the package contents.
    The manifest is not included in the .zip file, but it is stored in
    the same Amazon S3 bucket as the .zip files that form the package.
    The manifest identifies the package version and maps the .zip files
    in the package to target instance attributes, such as operating
    system version or architecture. For information about how to create
    the manifest, see [Step 2: Create the JSON package
    manifest](https://docs.aws.amazon.com/systems-manager/latest/userguide/distributor-working-with-packages-create.html#packages-manifest).

CrowdStrike will generate the required Package files and AWS will manage
the distribution of these packages so that they are available in
customer accounts.
