# Installing the FIG detections SQS queue
FIG leverages the AWS Simple Queue Service to handle message queuing for detections identified by the CrowdStrike Falcon API. This allows for significant scaling capacity without impacting the size of the FIG service application instance and provides a secure mechanism for delivering these detections from our AWS EC2 instance over to our AWS Lambda function.

Two queues will be created as part of this deployment, a primary detections queue, and a dead-letter queue for malformed message traffic.

## Creating the dead-letter queue (DLQ)
The dead-letter queue is the repository for messages received by our primary queue that are either malformed, have timed out or are incapable of being handled. Messages arrive in this queue after first failing processing within our primary detection queue. Messages retained in the dead-message queue are available for up to 7 days after failing. (This setting can be changed within the dead-letter queue message retention configuration.)

The dead-letter queue can have any name, and should have the following characteristics:
+ Type: __Standard__
+ Dead-letter queue: __Disabled__

The following characteristics can be customized per deployment requirements:
+ Maximum message size: __256 KB__
+ Default visibility timeout: __30 Seconds__
+ Message retention period: __7 days__
+ Delivery delay: __0 Seconds__
+ Receive message wait time: __0 Seconds__

## Creating the primary detections queue
The primary detections queue is the repository for detections identified by FIG as potentially active within your AWS environment. These messages are consumed by a lambda function that further confirms the instance's region and MAC address and then publishes the finding to AWS Security Hub.

The primary detection queue can have any name, and should have the following characteristics:
+ Type: __Standard__
+ Dead-letter queue: __*ARN of the queue defined above*__

The following characteristics can be customized per deployment requirements:
+ Maximum message size: __256 KB__
+ Default visibility timeout: __30 Seconds__
+ Message retention period: __4 hours__
+ Delivery delay: __0 Seconds__
+ Receive message wait time: __0 Seconds__

## Access policy
SQS permissions can be customized to meet your environment requirements, but the following minimum levels of access will be required.

> Make sure to update this policy to reflect the values for your account, the [Lambda execution role](lambda-install.md) and the [EC2 Instance IAM role](manual-install.md) before applying.

```json
{
  "Version": "2008-10-17",
  "Id": "__default_policy_ID",
  "Statement": [
    {
      "Sid": "__owner_statement",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{AWS_ACCOUNT_ID}:root"
      },
      "Action": "SQS:*",
      "Resource": "arn:aws:sqs:{AWS_REGION}:{AWS_ACCOUNT_ID}:{SQS_QUEUE_NAME}"
    },
    {
      "Sid": "__sender_statement",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{EC2_INSTANCE_IAM_ROLE}",
          "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{LAMBDA_EXECUTION_ROLE_NAME}",
          "arn:aws:iam::{AWS_ACCOUNT_ID}:root"
        ]
      },
      "Action": "SQS:SendMessage",
      "Resource": "arn:aws:sqs:{AWS_REGION}:{AWS_ACCOUNT_ID}:{SQS_QUEUE_NAME}"
    },
    {
      "Sid": "__receiver_statement",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::{AWS_ACCOUNT_ID}:role/{LAMBDA_EXECUTION_ROLE_NAME}",
          "arn:aws:iam::{AWS_ACCOUNT_ID}:root"
        ]
      },
      "Action": [
        "SQS:ChangeMessageVisibility",
        "SQS:DeleteMessage",
        "SQS:ReceiveMessage"
      ],
      "Resource": "arn:aws:sqs:{AWS_REGION}:{AWS_ACCOUNT_ID}:{SQS_QUEUE_NAME}"
    }
  ]
}
```
