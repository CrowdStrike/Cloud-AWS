import json
import os
import logging
import string
import random
import sys
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


SUCCESS = "SUCCESS"
FAILED = "FAILED"

cloudtrail_bucket_owner_id = os.environ['central_s3_bucket_account']
cloudtrail_bucket_region = os.environ['cloudtrail_bucket_region']
iam_role_arn = os.environ['iam_role_arn']
CSAccountNumber = os.environ['CSAccountNumber']
CSAssumingRoleName = os.environ['CSAssumingRoleName']
LocalAccount = os.environ['LocalAccount']
aws_region = os.environ['aws_region']
Falcon_Discover_Url = 'https://ctstagingireland.s3-'+aws_region+'.amazonaws.com/crowdstrike_role_creation_ss.yaml'


def register_falcon_discover_account(payload, api_keys, api_method) -> bool:
    cs_action = api_method
    url = "https://api.crowdstrike.com/cloud-connect-aws/entities/accounts/v1?mode=manual"
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
            return True
        elif response.status_code == 409:
            logger.info('Account already registered - nothing to do')
            return True
        else:
            error_code = response.status_code
            error_msg = response_content["errors"][0]["message"]
            logger.info('Account {} Registration Failed - Response {} {}'.format(error_code, error_msg))
            return
    except Exception as e:

        logger.info('Got exception {}'.format(e))
        return


def get_auth_header(auth_token) -> str:
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


def format_notification_message(external_id, rate_limit_reqs=0, rate_limit_time=0):
    data = {
        "resources": [
            {
                "cloudtrail_bucket_owner_id": cloudtrail_bucket_owner_id,
                "cloudtrail_bucket_region": cloudtrail_bucket_region,
                "external_id": external_id,
                "iam_role_arn": iam_role_arn,
                "id": LocalAccount,
                "rate_limit_reqs": rate_limit_reqs,
                "rate_limit_time": rate_limit_time
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


def get_random_alphanum_string(stringLength=8):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))


def lambda_handler(event, context):
    try:
        response_data = {}
        logger.info('Event = {}'.format(event))
        if event['RequestType'] in ['Create']:
            api_keys = event['ResourceProperties']
            external_id = event['ResourceProperties']['ExternalID']
            # Format post message
            API_METHOD = 'POST'
            api_message = format_notification_message(external_id)
            # Register account
            register_result = register_falcon_discover_account(api_message, api_keys, API_METHOD)
            logger.info('Account registration result: {}'.format(register_result))
            if register_result:
                cfnresponse_send(event, context, SUCCESS, register_result, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, register_result, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Update']:
            logger.info('Event = ' + event['RequestType'])
            api_keys = event['ResourceProperties']
            external_id = event['ResourceProperties']['ExternalID']
            # Format post message
            API_METHOD = 'PATCH'
            api_message = format_notification_message(external_id)
            # Register account
            register_result = register_falcon_discover_account(api_message, api_keys, API_METHOD)
            logger.info('Account registration result: {}'.format(register_result))
            if register_result:
                cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")

            logger.info('Event = ' + event['RequestType'])

            cfnresponse_send(event, context, 'SUCCESS', "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            # TODO handle account deletion
            response_data["Status"] = "Success"
            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")

    except Exception as e:
        logger.error(e)
        response_data = {}
        response_data["Status"] = str(e)
        cfnresponse_send(event, context, 'FAILED', response_data, "CustomResourcePhysicalID")
