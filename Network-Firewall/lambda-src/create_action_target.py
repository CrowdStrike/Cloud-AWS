import logging
import os

import boto3
import cfnresponse

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    try:
        properties = event['ResourceProperties']
        region = os.environ['AWS_REGION']
        client = boto3.client('securityhub', region_name=region)
        responseData = {}
        if event['RequestType'] == 'Create':
            response = client.create_action_target(
                Name=properties['Name'],
                Description=properties['Description'],
                Id=properties['Id']
            )
            responseData['Arn'] = response['ActionTargetArn']
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        elif event['RequestType'] == 'Delete':
            account_id = context.invoked_function_arn.split(":")[4]
            client.delete_action_target(
                ActionTargetArn=f"arn:aws:securityhub:{region}:{account_id}:action/custom/{properties['Id']}"
            )
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        logger.info('Got exception adding action {}'.format(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
