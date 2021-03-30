# Terraform Templates

The terraform templates here are examples that customers may use or modify as required.  The templates assume that you are using a shared "log archive" account.  Two templates are included.

1) Log archive account directory `log-archive-account`. 
   This template is an example of the required settings for the log archive account.
   The template has two resources
   
    - IAM role that grants s3Get:Object permissions to a role that Crowdstrike will assume when accessing log files that with a trusted entity of a CrowdStrike Role arn:aws:iam::292230061137:role/CS-Prod-HG-CsCloudconnectaws.
    
   ```
    resource "aws_iam_policy" "ReadS3CloudTrailFiles" {
    name = "iamPolicyFalconDiscoverAccess"
    description = "S3 access policy for role assumed by Falcon Discover"
    policy = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
        {
              "Action": [
                "s3:GetObject"

              ],
              "Effect": "Allow",
              "Resource": "arn:aws:s3:::${var.CloudTrailS3BucketName}/*",
              "Sid": ""
        }
        ]
    }
    EOF
    }

    data "aws_iam_policy_document" "CrowdStrikeDiscoverAssumeRolePolicyDocument" {
      statement {
        actions = ["sts:AssumeRole"]
        principals {
          type = "AWS"
          identifiers = [
            "arn:aws:iam::292230061137:role/CS-Prod-HG-CsCloudconnectaws"
          ]
        }
        condition {
          test = "StringEquals"
          variable = "sts:ExternalId"

          values = [
            var.ExternalID
          ]
        }
      }
    }
    ```

    - A bucket notification policy that sends an SNS notification to CrowdStrike
    ```
    resource "aws_s3_bucket_notification" "bucket_notification" {
    bucket = aws_s3_bucket.CloudTrail_bucket.id

    topic {
        //    Crowdstrike hosts topics in most region has a topic as SNS cannot send notifications across regions
        //    All topics are in account 292230061137 which is set in ${var.CSAccountNumber}
    topic_arn = "arn:aws:sns:${var.aws_region}:292230061137:cs-cloudconnect-aws-cloudtrail"
    events = [
      "s3:ObjectCreated:Put"]
    }
    }
    ```
2) The additional accounts in the directory `additional-acount-existing-trail`.
   This template should be used for all accounts that contain resources that should be monitored and which forward logs to the log archive account
   The template contains the following resources
   
    -   A IAM role that Crowdstrike can assume to gather information about resources of interest. 
```text
    data "aws_iam_policy_document" "DescribeAPICalls" {
    statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeInstances",
      "ec2:DescribeImages",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeVolumes",
      "ec2:DescribeVpcs",
      "ec2:DescribeRegions",
      "ec2:DescribeSubnets",
      "ec2:DescribeNetworkAcls",
      "ec2:DescribeSecurityGroups",
      "iam:ListAccountAliases"
    ]
    resources = ["*"]
      }
    }

    data "aws_iam_policy_document" "CrowdStrikeDiscoverAssumeRolePolicyDocument" {
      statement {
        actions = ["sts:AssumeRole"]
        principals {
          type = "AWS"
          identifiers = [
            "arn:aws:iam::${var.CSAccountNumber}:role/${var.CSAssumingRoleName}"
          ]
        }
        condition {
          test = "StringEquals"
          variable = "sts:ExternalId"
    
          values = [
            var.ExternalID
          ]
        }
      }
    }


```

Once the templates have run the accounts should be registered with or removed from the CrowdStrike discover service via the CrowdStrike API.   A script is provided here for registration, update and deletion
https://github.com/CrowdStrike/Cloud-AWS/tree/master/Discover-for-Cloud-Templates/AWS/troubleshooting/scripts

    
    
