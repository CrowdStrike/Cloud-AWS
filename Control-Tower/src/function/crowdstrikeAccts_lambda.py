import json
import boto3
import logging
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stackset_list = ['CrowdstrikeDiscover-IAM-ROLES']
result = {"ResponseMetadata": {"HTTPStatusCode": "400"}}


def lambda_handler(event, context):
    masterAcct = event['account']
    eventDetails = event['detail']
    regionName = eventDetails['awsRegion']
    eventName = eventDetails['eventName']
    srvEventDetails = eventDetails['serviceEventDetails']
    if eventName == 'CreateManagedAccount':
        newAccInfo = srvEventDetails['createManagedAccountStatus']
        cmdStatus = newAccInfo['state']
        if cmdStatus == 'SUCCEEDED':
            '''Sucessful event recieved'''
            ouInfo = newAccInfo['organizationalUnit']
            ouName = ouInfo['organizationalUnitName']
            odId = ouInfo['organizationalUnitId']
            accId = newAccInfo['account']['accountId']
            accName = newAccInfo['account']['accountName']
            CFT = boto3.client('cloudformation')

            for item in stackset_list:
                try:
                    result = CFT.create_stack_instances(StackSetName=item, Accounts=[accId], Regions=[regionName])
                    logger.info('Processed {} Sucessfully'.format(item))

                except Exception as e:
                    logger.error('Unable to launch in:{}, REASON: {}'.format(item, e))
        else:
            '''Unsucessful event recieved'''
            logger.info('Unsucessful Event Recieved. SKIPPING :{}'.format(event))
            return (False)
    else:
        logger.info('Control Tower Event Captured :{}'.format(event))


