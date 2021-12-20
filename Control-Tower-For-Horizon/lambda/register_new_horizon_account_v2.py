import json
import logging
import os
import sys
import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CONSTANTS
SUCCESS = "SUCCESS"
FAILED = "FAILED"


CSPM_ROLE_TEMPLATE_URL = 'https://cs-prod-cloudconnect-templates.s3-us-west-1.amazonaws.com' \
                         '/aws_cspm_cloudformation_v1.1.json'
STACK_SET_NAME = "CrowdStrike-CSPM-Integration"


organizationalUnitId = os.environ['organizationalUnitId']
CSAccountNumber = os.environ['CSAccountNumber']
CSAssumingRoleName = os.environ['CSAssumingRoleName']
aws_region = os.environ['aws_region']


def deregister_falcon_horizon_account(account_id, api_keys, api_method) -> bool:
    cs_action = api_method
    url = "https://api.crowdstrike.com/cloud-connect-cspm-aws/entities/account/v1?ids="+account_id
    auth_token = get_auth_token(api_keys)
    if auth_token:
        auth_header = get_auth_header(auth_token)
    else:
        print("Failed to auth token")
        sys.exit(1)
    headers = {
        'Content-Type': 'application/json',
    }
    headers.update(auth_header)

    try:
        response = requests.request(cs_action, url, headers=headers)
        response_content = json.loads(response.text)
        logger.info('Response to deregister = {}'.format(response_content))
        good_exit = 201 if cs_action == 'POST' else 200
        if response.status_code == good_exit:
            logger.info('Account Deregistered')
            return True
        else:
            error_code = response.status_code
            logger.info('Account Deregistration Failed - Response {}'.format(error_code))
            return False
    except Exception as e:
        logger.info('Got exception {}'.format(e))


def register_falcon_horizon_account(payload, api_keys, api_method) -> dict:
    cs_action = api_method
    url = "https://api.crowdstrike.com/cloud-connect-cspm-aws/entities/account/v1"
    auth_token = get_auth_token(api_keys)
    if auth_token:
        auth_header = get_auth_header(auth_token)
    else:
        print("Failed to auth token")
        sys.exit(1)
    headers = {
        'Content-Type': 'application/json',
    }
    headers.update(auth_header)

    try:
        response = requests.request(cs_action, url, headers=headers, data=payload)
        response_content = json.loads(response.text)
        logger.info('Response to register = {}'.format(response_content))
        good_exit = 201 if cs_action == 'POST' else 200
        if response.status_code == good_exit:
            logger.info('Account Registered')
            return response_content['resources'][0]
        elif response.status_code == 409:
            logger.info('Account already registered - nothing to do')
            return response_content['resources'][0]
        else:
            error_code = response.status_code
            error_msg = response_content["errors"][0]["message"]
            logger.info('Account Registration Failed - Response {} {}'.format(error_code, error_msg))
            return response_content['resources'][0]
    except Exception as e:
        logger.info('Got exception {}'.format(e))


def get_auth_header(auth_token) -> dict:
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token(api_keys):
    FalconClientId = api_keys['FalconClientId']
    FalconSecret = api_keys['FalconSecret']
    url = "https://api.crowdstrike.com/oauth2/token"
    payload = 'client_secret=' + FalconSecret + '&client_id=' + FalconClientId
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request('POST', url, headers=headers, data=payload)
    if response.ok:
        response_object = (response.json())
        token = response_object.get('access_token', '')
        if token:
            return \
                token
    return


def format_notification_message(account_id, organization_id):
    data = {
        "resources": [
            {
                "organization_id": organization_id,
                "account_id": account_id,
            }
        ]
    }
    logger.info('Post Data {}'.format(data))
    message = json.dumps(data)
    return message


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    print(responseUrl)

    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']

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


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    logger.info('Context {}'.format(context))
    try:
        response_data = {}
        logger.info('Event = {}'.format(event))
        CFT = boto3.client('cloudformation')
        api_keys = event['ResourceProperties']
        accountId = context.invoked_function_arn.split(":")[4]
        if event['RequestType'] in ['Create']:
            # Format post message
            API_METHOD = 'POST'
            api_message = format_notification_message(accountId, organizationalUnitId)
            register_result = register_falcon_horizon_account(api_message, api_keys, API_METHOD)
            logger.info('Account registration result: {}'.format(register_result))
            external_id = register_result['external_id']
            RoleName = register_result['iam_role_arn'].split('/')[-1]
            CRWD_Discover_paramList = []
            keyDict = {'ParameterKey': 'ExternalID', 'ParameterValue': external_id}
            CRWD_Discover_paramList.append(dict(keyDict))
            keyDict['ParameterKey'] = 'RoleName'
            keyDict['ParameterValue'] = RoleName
            CRWD_Discover_paramList.append(dict(keyDict))
            keyDict['ParameterKey'] = 'CSRoleName'
            keyDict['ParameterValue'] = CSAssumingRoleName
            CRWD_Discover_paramList.append(dict(keyDict))
            keyDict['ParameterKey'] = 'CSAccountNumber'
            keyDict['ParameterValue'] = CSAccountNumber
            CRWD_Discover_paramList.append(dict(keyDict))

            cft_result = CFT.create_stack(
                StackName=STACK_SET_NAME,
                TemplateURL=CSPM_ROLE_TEMPLATE_URL,
                Parameters=CRWD_Discover_paramList,
                TimeoutInMinutes=5,
                Capabilities=[
                    'CAPABILITY_NAMED_IAM',
                ],
                # RoleARN='string',
                Tags=[
                    {
                        'Key': 'Vendor',
                        'Value': 'CrowdStrike'
                    },
                ],
            )
            if cft_result:
                logger.info('Created Stack {}'.format(cft_result.get('StackId')))
                cfnresponse_send(event, context, SUCCESS, register_result, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, register_result, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Update']:
            logger.info('Event = ' + event['RequestType'])
            cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            API_METHOD = 'DELETE'
            deregister_falcon_horizon_account(accountId, api_keys, API_METHOD)
            cft_result = CFT.delete_stack(
                StackName="CrowdStrike-CSPM-Integration")
            logger.info('Stack delete OperationId {}'.format(cft_result.get('OperationId')))
            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")

    except Exception as e:
        logger.info('Got exception {}'.format(e))
        response_data = {"Status": str(e)}
        cfnresponse_send(event, context, 'FAILED', response_data, "CustomResourcePhysicalID")
