# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <https://unlicense.org>

import datetime
import json
import logging
import os
import sys

import boto3
import requests
import urllib3

# import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
REGION = os.environ['aws_region']
SUCCESS = "SUCCESS"
FAILED = "FAILED"

http = urllib3.PoolManager()
ssm_client = boto3.client('ssm', region_name=REGION)


def get_auth_header(auth_token) -> dict:
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token(falcon_client_secret, falcon_client_id):
    url = "https://api.crowdstrike.com/oauth2/token"
    payload = 'client_secret=' + falcon_client_secret + '&client_id=' + falcon_client_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.ok:
        response_object = (response.json())
        token = response_object.get('access_token', '')
        if token:
            return \
                token
    return


def check_for_install_token(credentials) -> bool:
    url = "https://api.crowdstrike.com/installation-tokens/queries/tokens/v1?filter=status:'valid'"
    auth_token = get_auth_token(credentials['CS_API_GATEWAY_CLIENT_ID'], credentials['CS_API_GATEWAY_CLIENT_SECRET'])
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
        response = requests.request('GET', url, headers=headers)
        response_content = json.loads(response.text)
        good_exit = 200
        if response.status_code == good_exit:
            # Tokens are listed in response[]
            if len(response_content['resources']) > 0:
                return True
            else:
                logger.info('No installation valid installation tokens found')
                return False
    except Exception as e:
        logger.info('Got exception {}'.format(e))
        return False


def create_installation_token(credentials, label='aws-ssm-token1', valid_days=365) -> bool:
    now = datetime.datetime.now()
    valid_until = (now + datetime.timedelta(valid_days))
    expiry_date = str(valid_until.isoformat() + 'Z')
    PARAMS = {
        "expires_timestamp": expiry_date,
        "label": label
    }

    url = "https://api.crowdstrike.com/installation-tokens/entities/tokens/v1"
    auth_token = get_auth_token(credentials['CS_API_GATEWAY_CLIENT_ID'], credentials['CS_API_GATEWAY_CLIENT_SECRET'])
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
        response = requests.post(url, headers=headers, json=PARAMS)
        response_content = json.loads(response.text)
        good_exit = 201
        if response.status_code == good_exit:
            print(response_content)
            return True
        else:
            logger.info('Failed to generate install token')
            return False
    except Exception as e:
        logger.info('Got exception {} creating installation token'.format(e))
        return False


def create_ssm_param(parameter_name, parameter_description, parameter_value, parameter_type, overwrite):
    response = ssm_client.put_parameter(
        Name=parameter_name,
        Description=parameter_description,
        Value=parameter_value,
        Type=parameter_type,
        Overwrite=overwrite,
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False


def delete_ssm_param(parameter_name):
    response = ssm_client.delete_parameter(
        Name=parameter_name
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False


def cfnresponse_send(event, context, response_status, physical_resource_id=None):
    responseUrl = event['ResponseURL']
    responseBody = {'Status': response_status,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': physical_resource_id or context.log_stream_name, 'StackId': event['StackId'],
                    'RequestId': event['RequestId'], 'LogicalResourceId': event['LogicalResourceId']}

    json_responseBody = json.dumps(responseBody)

    # print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = http.request('PUT', responseUrl, body=json_responseBody.encode('utf-8'), headers=headers)
        # print("Status code: " + response.reason)
        # response = requests.put(responseUrl,
        #                         data=json_responseBody,
        #                         headers=headers)
        # logger.info('Sending CFN response status: {}'.format(responseStatus))
        logger.info('Got CFN response status: {}'.format(response.reason))
    except Exception as e:
        logger.info('Error sending CFN response {}'.format(e))


def create_params(params, overwrite_action):
    for k, v in params.items():
        try:
            logger.info('Creating parameter {}'.format(k))
            create_ssm_param(k, 'CrowdStrike API', v, 'SecureString', overwrite_action)
        except Exception as e:
            logger.info('Got Exception creating parameters.  \nException is {}'.format(e))
            return False
    return True


def delete_params(params):
    for k, v in params.items():
        try:
            logger.info('Deleting parameter {}'.format(k))
            delete_ssm_param(k)
        except Exception as e:
            logger.info('Got Exception deleting parameters.  \nException is {}'.format(e))
    return True


def lambda_handler(event, context):
    try:
        response_data = {}
        logger.info('Event = {}'.format(event))
        original_params = event['ResourceProperties']
        params = {key: val for key, val in original_params.items() if key != 'ServiceToken'}
        # params = {
        #         CS_API_GATEWAY_HOST: <URL>,
        #         CS_API_GATEWAY_CLIENT_ID: <clientID>
        #         CS_API_GATEWAY_CLIENT_SECRET: <clientSecret>
        # }

        logger.info('Parameter are {}'.format(params))
        if check_for_install_token(params):
            logger.info('Valid installation token exists in CrowdStrike Console')
        else:
            logger.info('No valid installation token exists in CrowdStrike Console - Creating one')
            if create_installation_token(params):
                logger.info('Created installation token in CrowdStrike Console')
            else:
                logger.info('Failed to create installation token in CrowdStrike Console')
        if event['RequestType'] in ['Create']:
            overwrite_action = False
            create_params(params, overwrite_action)
            if create_params:
                cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Update']:
            overwrite_action = True
            create_params(params, overwrite_action)
            if create_params:
                cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")

            logger.info('Event = ' + event['RequestType'])

            cfnresponse_send(event, context, 'SUCCESS', "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            delete_params(params)
            response_data["Status"] = "Success"
            cfnresponse_send(event, context, 'SUCCESS', "CustomResourcePhysicalID")

    except Exception as e:
        logger.error(e)
        cfnresponse_send(event, context, 'FAILED', "CustomResourcePhysicalID")


if __name__ == '__main__':
    # CS_API_GATEWAY_HOST: !Ref
    # APIGatewayHostKey
    # CS_API_GATEWAY_CLIENT_ID: !Ref
    # APIGatewayClientIDKey
    # CS_API_GATEWAY_CLIENT_SECRET: !Ref
    # APIGatewayClientSecretKey

    result = create_ssm_param("test", "A test parameter", "value", "SecureString", True)
