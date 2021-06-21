"""
s3-lambda-sns-sqs-py - Lambda function for multiple SNS publishing

Created: jhseceng 06.16.2021
Modified: jshcodes 06.21.2021

SETUP
---------------------
Environment Variables

Set the CrowdStrike SNS topic in the CRWD_TOPIC environment Variable
The value should be a comma seperated list
arn:aws:sns:<<your aws region>>:292230061137:cs-cloudconnect-aws-cloudtrail

Set SNS topics in the 'sns_topic_arns' environment Variable
The value should be a comma seperated list
arn:aws:sns:eu-west-1:517716712345:topic1,arn:aws:sns:eu-west-1:517716712345:topic2

Set SQS queue URLS in the 'sqs_queue_urls' environment Variable
The value should be a comma seperated list
https://sqs.eu-west-1.amazonaws.com/517716712345/queue1,https://sqs.eu-west-1.amazonaws.com/517716712345/queue2

IAM
The lambda function will require a lambda exection policy and the relevant IAM permissions to publish to the SNS and
SQS queues listed in the environment variable
"""
import json
import logging
import os
import boto3

#
# Change INFO to DEBUG for more information
#
logger = logging.getLogger()
logger.setLevel(logging.INFO)
runtime_region = os.environ['AWS_REGION']
sns_client = boto3.client('sns', region_name=runtime_region)
sqs_client = boto3.client('sqs', region_name=runtime_region)


def lambda_handler(event, context):

    logger.debug('Got event {}'.format(event))
    logger.debug('Got context {}'.format(context))

    #
    # First handle event and send PUT requests to CrowdStrike
    #
    # CrowdStrike only requires PUT events to be forwarded to SNS
    #
    # First check for PUT events
    CRWD_TOPIC = os.environ.get('CRWD_TOPIC')
    if event['Records'][0]['eventName'] == "ObjectCreated:Put" and CRWD_TOPIC:
        try:
            response = sns_client.publish(
                TopicArn=CRWD_TOPIC,
                Message=json.dumps(event),
            )
            logger.debug('Published to CRWD topic with response {}'.format(response))
        except Exception as e:
            logger.info("Got Error {} publishing to CrowdStrike SNS topic".format(e))
            pass

    if os.environ.get('sns_topic_arns'):
        sns_topic_arns = os.environ['sns_topic_arns'].split(',')
        logger.debug('Got Topic ARNS {}'.format(sns_topic_arns))
        for topic in sns_topic_arns:
            try:
                logger.debug("Publishing to topic {}".format(topic))
                response = sns_client.publish(
                    TopicArn=topic,
                    Message=json.dumps(event),
                )
                logger.debug('Publish response {}'.format(response))
            except Exception as e:
                logger.info("Got Error {} publishing to SNS topic {}".format(e, topic))
                pass

    if os.environ.get('sqs_queue_urls'):
        sqs_queue_urls = os.environ['sqs_queue_urls'].split(',')
        logger.debug('Got SQS queue {}'.format(sqs_queue_urls))
        for queue_url in sqs_queue_urls:
            try:
                logger.debug("Publishing to sqs queue {}".format(queue_url))
                response = sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(event),
                )
                logger.debug('Publish response {}'.format(response))
            except Exception as e:
                logger.info("Got Error {} publishing to SQS queue {}".format(e, queue_url))
                pass
