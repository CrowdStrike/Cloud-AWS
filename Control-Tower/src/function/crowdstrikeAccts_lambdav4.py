import boto3
import logging
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)

stackset_name = os.environ['stackset_name']
result = {"ResponseMetadata": {"HTTPStatusCode": "400"}}


def lambda_handler(event, context):
    # masterAcct = event['account']
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
            # ouName = ouInfo['organizationalUnitName']
            # odId = ouInfo['organizationalUnitId']
            accId = newAccInfo['account']['accountId']
            # accName = newAccInfo['account']['accountName']
            CFT = boto3.client('cloudformation')
            try:
                _ = CFT.create_stack_instances(StackSetName=stackset_name, Accounts=[accId], Regions=[regionName])
                logger.info('Processed {} Sucessfully'.format(stackset_name))

            except Exception as e:
                logger.error('Unable to launch in:{}, REASON: {}'.format(stackset_name, e))
        else:
            '''Unsucessful event recieved'''
            logger.info('Unsucessful Event Recieved. SKIPPING :{}'.format(event))
            return (False)
    else:
        logger.info('Control Tower Event Captured :{}'.format(event))


