# Terraform Templates

The terraform templates here are examples that customers may use or modify as required.  The templates assume that you are using a shared "log archive" account.  Two types of template are included.

1) A template for the log archive account.  
A S3 bucket with a bucket ACL and access policy is required together with an IAM role that grants s3Get:Object permissions to a role that Crowdstrike will assume when accessing log files. 

2) A template for all additional accounts that can be applied during the account creation process or post creation. 
A IAM role with    
    "ec2:DescribeInstances",
    "ec2:DescribeImages",
    "ec2:DescribeNetworkInterfaces",
    "ec2:DescribeVolumes",
    "ec2:DescribeVpcs",
    "ec2:DescribeRegions",
    "ec2:DescribeSubnets",
    "ec2:DescribeNetworkAcls",
    "ec2:DescribeSecurityGroups",
    "iam:ListAccountAliases" permissions that Crowdstrike can assume to gather information about resources of interest. 
    
In some circumstances a customer may already have created the shared S3 bucket in the central "log archive" account and setup the CloudTrail logs.  Templates are included for this scenario.

    
    