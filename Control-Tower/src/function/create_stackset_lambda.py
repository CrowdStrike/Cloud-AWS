import json
import logging
import os
# from botocore.vendored import requests
import random
import string
import time

import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    print(responseUrl)

    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': physicalResourceId or context.log_stream_name, 'StackId': event['StackId'],
                    'RequestId': event['RequestId'], 'LogicalResourceId': event['LogicalResourceId'], 'NoEcho': noEcho,
                    'Data': responseData}

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))


def get_secret_value(secret):
    # key = 'falcon_client_secret'
    key = secret
    SM = boto3.client('secretsmanager')
    secret_list = SM.list_secrets()['SecretList']
    output = {}
    for s in secret_list:
        if key in s.values():
            output = SM.get_secret_value(SecretId=key)['SecretString']
    return output


def get_account_id(name='Log archive'):
    """Get the Account Id from AWS Organization"""
    ORG = boto3.client('organizations')
    result = ''
    try:
        orgList = ORG.list_accounts()['Accounts']
    except Exception as e:
        raise e
    if len(orgList) > 1:
        for i in orgList:
            if i['Name'] == name:
                result = i['Id']
    return result


def get_master_id():
    """ Get the master Id from AWS Organization - Only on master"""
    masterID = ''
    ORG = boto3.client('organizations')
    try:
        masterID = ORG.list_roots()['Roots'][0]['Arn'].rsplit(':')[4]
        return masterID
    except Exception as e:
        logger.error('This stack runs only on the Master of the AWS Organization')
        return False


def launch_crwd_discover(templateUrl, paramList, AdminRoleARN, ExecRole, cList, stacketsetName):
    """ Launch CRWD Discover Stackset on the Master Account """
    CFT = boto3.client('cloudformation')
    result = {}
    if len(paramList):
        try:
            result = CFT.create_stack_set(StackSetName=stacketsetName,
                                          Description='Roles for CRWD-Discover',
                                          TemplateURL=templateUrl,
                                          Parameters=paramList,
                                          AdministrationRoleARN=AdminRoleARN,
                                          ExecutionRoleName=ExecRole,
                                          Capabilities=cList)
            return result
        except ClientError as e:
            if e.response['Error']['Code'] == 'NameAlreadyExistsException':
                logger.info("StackSet already exists")
                result['StackSetName'] = 'CRWD-ROLES-CREATION'
                return result
            else:
                logger.error("Unexpected error: %s" % e)
                result['Status'] = e
                return result


def get_random_alphanum_string(stringLength=15):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))


def delete_stackset(stacksetName):
    CFT = boto3.client('cloudformation')
    try:
        stackset_result = CFT.describe_stack_set(StackSetName=stacksetName)
        if stackset_result and 'StackSet' in stackset_result:
            stackset_instances = CFT.list_stack_instances(StackSetName=stacksetName)
            while 'NextToken' in stackset_instances:
                stackinstancesnexttoken = stackset_instances['NextToken']
                morestackinstances = CFT.list_stack_instances(NextToken=stackinstancesnexttoken)
                stackset_instances["Summaries"].extend(morestackinstances["Summaries"])
            if len(stackset_instances["Summaries"]) > 0:
                stack_instance_members = [x["Account"] for x in stackset_instances["Summaries"]]
                stack_instance_regions = list(set(x["Region"] for x in stackset_instances["Summaries"]))
                CFT.delete_stack_instances(
                    StackSetName=stacksetName,
                    Accounts=stack_instance_members,
                    Regions=stack_instance_regions,
                    OperationPreferences={'MaxConcurrentCount': 3},
                    RetainStacks=False
                )
            stackset_instances = CFT.list_stack_instances(StackSetName=stacksetName)
            counter = 2
            while len(stackset_instances["Summaries"]) > 0 and counter > 0:
                logger.info("Deleting stackset instance from {}, remaining {}, "
                            "sleeping for 10 sec".format(stacksetName, len(stackset_instances["Summaries"])))
                time.sleep(10)
                counter = counter - 1
                stackset_instances = CFT.list_stack_instances(StackSetName=stacksetName)
            if counter > 0:
                CFT.delete_stack_set(StackSetName=stacksetName)
                logger.info("StackSet {} deleted".format(stacksetName))
            else:
                logger.info("StackSet {} still has stackset instance, skipping".format(stacksetName))
            return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            logger.info("StackSet {} does not exist".format(stacksetName))
            return True
        else:
            logger.error("Unexpected error: %s" % e)
            return False


def lambda_handler(event, context):
    try:
        STACKSETNAME = 'CrowdstrikeDiscover-IAM-ROLES'

        AwsRegion = os.environ['AwsRegion']
        RoleName = os.environ['RoleName']
        CSAccountNumber = os.environ['CSAccountNumber']
        CSAssumingRoleName = os.environ['CSAssumingRoleName']
        LogArchiveBucketRegion = os.environ['LogArchiveBucketRegion']
        LogArchiveAccount = os.environ['LogArchiveAccount']
        CredentialsSecret = os.environ['CrowdstrikeCredentialsSecret']
        #
        # Moved to virtual hosted-style URLs.
        # See https://aws.amazon.com/fr/blogs/aws/amazon-s3-path-deprecation-plan-the-rest-of-the-story/
        # path-style URLs to be depricated
        #
        CrowdstrikeTemplateUrl = f'https://crowdstrike-sa-resources-ct-{AwsRegion}.s3.amazonaws.com/ct_crowdstrike_stackset.yaml',
        AccountId = get_master_id()
        cList = ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        ExecRole = 'AWSControlTowerExecution'
        AdminRoleARN = 'arn:aws:iam::' + AccountId + ':role/service-role/AWSControlTowerStackSetRole'
        logger.info('EVENT Received: {}'.format(event))

        response_data = {}

        if event['RequestType'] in ['Create']:
            logger.info('Event = ' + event['RequestType'])

            # Parameters for CRWD-Discover stackset
            CRWD_Discover_paramList = []
            secretList = json.loads(get_secret_value(CredentialsSecret))
            keyDict = {}

            # LocalAccount:
            for s in secretList.keys():
                keyDict = {'ParameterKey': s, 'ParameterValue': secretList[s]}
                CRWD_Discover_paramList.append(dict(keyDict))
            ExternalID = get_random_alphanum_string(8)
            keyDict['ParameterKey'] = 'ExternalID'
            keyDict['ParameterValue'] = ExternalID
            CRWD_Discover_paramList.append(dict(keyDict))

            keyDict['ParameterKey'] = 'RoleName'
            keyDict['ParameterValue'] = RoleName
            CRWD_Discover_paramList.append(dict(keyDict))

            keyDict['ParameterKey'] = 'CSAccountNumber'
            keyDict['ParameterValue'] = CSAccountNumber
            CRWD_Discover_paramList.append(dict(keyDict))

            keyDict['ParameterKey'] = 'CSAssumingRoleName'
            keyDict['ParameterValue'] = CSAssumingRoleName
            CRWD_Discover_paramList.append(dict(keyDict))

            keyDict['ParameterKey'] = 'LogArchiveBucketRegion'
            keyDict['ParameterValue'] = LogArchiveBucketRegion
            CRWD_Discover_paramList.append(dict(keyDict))

            keyDict['ParameterKey'] = 'LogArchiveAccount'
            keyDict['ParameterValue'] = LogArchiveAccount
            CRWD_Discover_paramList.append(dict(keyDict))

            logger.info('CRWD_Discover ParamList:{}'.format(CRWD_Discover_paramList))
            logger.info('AdminRoleARN: {}'.format(AdminRoleARN))
            logger.info('CrowdstrikeTemplateUrl: {}'.format(CrowdstrikeTemplateUrl))
            logger.info('ExecRole: {}'.format(ExecRole))
            logger.info('ExecRole: {}'.format(cList))

            CRWD_Discover_result = launch_crwd_discover(CrowdstrikeTemplateUrl, CRWD_Discover_paramList, AdminRoleARN,
                                                        ExecRole, cList, STACKSETNAME)
            logger.info('CRWD-Discover Stackset: {}'.format(CRWD_Discover_result))

            if CRWD_Discover_result:
                cfnresponse_send(event, context, SUCCESS, CRWD_Discover_result, "CustomResourcePhysicalID")
                return
            else:
                cfnresponse_send(event, context, FAILED, CRWD_Discover_result, "CustomResourcePhysicalID")
                return

        elif event['RequestType'] in ['Update']:
            logger.info('Event = ' + event['RequestType'])

            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")
            return

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            delete_stackset(STACKSETNAME)
            response_data["Status"] = "Success"
            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")
            return
        raise Exception
    except Exception as e:
        logger.error(e)
        response_data = {"Status": str(e)}
        cfnresponse_send(event, context, 'FAILED', response_data, "CustomResourcePhysicalID")
        return
