import json
import logging
import os
import time
import requests
from falconpy import CloudConnectAWS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

CrowdStrikeCloud = os.environ['CrowdStrikeCloud']
cloudtrail_bucket_owner_id = os.environ['LogArchiveAccount']
cloudtrail_bucket_region = os.environ['cloudtrail_bucket_region']
iam_role_arn = os.environ['iam_role_arn']
CSAccountNumber = os.environ['CSAccountNumber']
CSAssumingRoleName = os.environ['CSAssumingRoleName']
LocalAccount = os.environ['LocalAccount']
aws_region = os.environ['aws_region']
delay_timer = os.environ['delay_timer']

def delete_falcon_discover_account(api_interface) -> bool:
    SuccessResult = True
    delete_response = api_interface.DeleteAWSAccounts(ids=LocalAccount)
    if delete_response["status_code"] == 200:
        print("Successfully deleted account.")
    else:
        ecode = delete_response['status_code']
        emsg = delete_response['body']['errors'][0]['message']
        print(f"Delete failed with response: {ecode} {emsg}")
        SuccessResult = False
    return SuccessResult


def register_falcon_discover_account(payload, api_interface) -> bool:
    SuccessResult = True
    result = api_interface.ProvisionAWSAccounts(body=payload)
    if result["status_code"] == 201:
        logger.info("Account Registered")
    elif result["status_code"] == 409:
        logger.info("Account already registered - nothing to do")
    else:
        ecode = result["status_code"]
        emsg = result["body"]["errors"][0]["message"]
        logging.info(f"Account Registration Failed - Response: {ecode}: {emsg}")
        SuccessResult = False
    return SuccessResult

def update_falcon_discover_account(payload, api_interface) -> bool:
    SuccessResult = True
    result = api_interface.UpdateAWSAccounts(body=payload)
    if result["status_code"] in [200, 201]:
        logger.info("Account Updated")
    else:
        ecode = result["status_code"]
        emsg = result["errors"][0]["message"]
        logging.info(f"Account Update Failed - Response: {ecode}: {emsg}")
        SuccessResult = False
    return SuccessResult

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
    logger.info(f'Post Data {data}')
    return data


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
    try:
        response_data = {}
        logger.info(f'Event = {event}')
        FalconClientId = event['ResourceProperties']['FalconClientId']
        FalconSecret = event['ResourceProperties']['FalconSecret']
        falcon = CloudConnectAWS(client_id=FalconClientId,
                                 client_secret=FalconSecret,
                                 base_url=CrowdStrikeCloud   # Only necessary for GovCloud
                                 )
        if event['RequestType'] in ['Create']:
            external_id = event['ResourceProperties']['ExternalID']
            api_message = format_notification_message(external_id)
            try:
                delay = float(delay_timer)
            except Exception as e:
                logger.info(f'cant convert delay_timer type {delay_timer} error {e}')
                delay = 60
            logger.info(f'Got ARN of Role Pausing for {delay} seconds for role setup')
            time.sleep(delay)
            register_result = register_falcon_discover_account(api_message, falcon)
            if register_result:
                cfnresponse_send(event, context, SUCCESS, register_result, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, register_result, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Update']:
            logger.info('Event = ' + event['RequestType'])
            external_id = event['ResourceProperties']['ExternalID']
            api_message = format_notification_message(external_id)
            register_result = update_falcon_discover_account(api_message, falcon)
            logger.info(f'Account update result: {register_result}')
            if register_result:
                cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")

            logger.info('Event = ' + event['RequestType'])

            cfnresponse_send(event, context, 'SUCCESS', "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            result = delete_falcon_discover_account(falcon)
            if result:
                logger.info('Successfully deleted account in Falcon Discover portal')
            else:
                logger.info('Failed to delete account in Falcon Discover portal')
            response_data["Status"] = "Success"
            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")

    except Exception as e:
        logger.error(e)
        response_data = {}
        response_data["Status"] = str(e)
        cfnresponse_send(event, context, 'FAILED', response_data, "CustomResourcePhysicalID")

