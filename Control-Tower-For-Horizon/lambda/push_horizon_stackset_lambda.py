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


if __name__ == '__main__':
    context = ()
    event = {
        "version": "0",
        "id": "999cccaa-eaaa-0000-1111-123456789012",
        "detail-type": "AWS Service Event via CloudTrail",
        "source": "aws.controltower",
        "account": "XXXXXXXXXXXX",
        "time": "2018-08-30T21:42:18Z",
        "region": "us-east-1",
        "resources": [],
        "detail": {
            "eventVersion": "1.05",
            "userIdentity": {
                "accountId": "XXXXXXXXXXXX",
                "invokedBy": "AWS Internal"
            },
            "eventTime": "2018-08-30T21:42:18Z",
            "eventSource": "controltower.amazonaws.com",
            "eventName": "CreateManagedAccount",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "AWS Internal",
            "userAgent": "AWS Internal",
            "eventID": "0000000-0000-0000-1111-123456789012",
            "readOnly": False,
            "eventType": "AwsServiceEvent",
            "serviceEventDetails": {
                "createManagedAccountStatus": {
                    "organizationalUnit": {
                        "organizationalUnitName": "Custom",
                        "organizationalUnitId": "ou-XXXX-l3zc8b3h"

                    },
                    "account": {
                        "accountName": "LifeCycle1",
                        "accountId": "XXXXXXXXXXXX"
                    },
                    "state": "SUCCEEDED",
                    "message": "AWS Control Tower successfully created a managed account.",
                    "requestedTimestamp": "2019-11-15T11:45:18+0000",
                    "completedTimestamp": "2019-11-16T12:09:32+0000"}
            }
        }
    }
