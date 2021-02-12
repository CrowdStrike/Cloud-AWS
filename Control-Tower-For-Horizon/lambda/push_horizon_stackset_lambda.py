import logging
import os
import json
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
stackset_list = ['CrowdStrikeCSPMReader-IAM-ROLES']


CredentialsSecret = os.environ['CrowdStrikeCredentialsSecret']


def get_secret_value(secret):
    key = secret
    SM = boto3.client('secretsmanager')
    secret_list = SM.list_secrets()['SecretList']
    output = {}
    for s in secret_list:
        if key in s.values():
            output = SM.get_secret_value(SecretId=key)['SecretString']
    return output


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    logger.info('Context {}'.format(context))
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
            # Parameters for CRWD-Discover stackset
            CRWD_Discover_paramList = []
            keyDict = {}
            secretList = json.loads(get_secret_value(CredentialsSecret))
            for s in secretList.keys():
                keyDict = {'ParameterKey': s, 'ParameterValue': secretList[s]}
                CRWD_Discover_paramList.append(dict(keyDict))
            CRWD_Discover_paramList.append({'ParameterKey': 'accountId', 'ParameterValue': accId})
            CRWD_Discover_paramList.append({'ParameterKey': 'organizationalUnitId', 'ParameterValue': odId})

            for item in stackset_list:
                try:
                    # TODO Possible Fetch api keys from secrets store instead of Input parameters in stackset
                    CFT.create_stack_instances(StackSetName=item, Accounts=[accId], Regions=[regionName],
                                               ParameterOverrides=CRWD_Discover_paramList)
                    logger.info('Processed {} Sucessfully'.format(item))

                except Exception as e:
                    logger.error('Unable to launch in:{}, REASON: {}'.format(item, e))
        else:
            '''Unsucessful event recieved'''
            logger.info('Unsucessful Event Recieved. SKIPPING :{}'.format(event))
            return (False)
    else:
        logger.info('Control Tower Event Captured :{}'.format(event))


