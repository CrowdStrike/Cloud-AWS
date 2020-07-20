import boto3
import argparse
import logging
from logging.handlers import RotatingFileHandler
import json
import requests
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
# handler = logging.StreamHandler()
handler = RotatingFileHandler("account_register.log", maxBytes=20971520, backupCount=5)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def register_falcon_discover_account(payload) -> bool:
    url = "https://api.crowdstrike.com/cloud-connect-aws/entities/accounts/v1?mode=manual"
    auth_token = get_auth_token()
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
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 201:
            return True
        else:
            print('Registration failed with response \n {} \n{}'
                  .format(response.status_code, response["errors"][0]["message"]))
    except Exception as e:
        # logger.info('Got exception {} hiding host'.format(e))
        print('Got exception {} hiding host'.format(e))
        return


def get_auth_header(auth_token) -> str:
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token():
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


def format_notification_message(rate_limit_reqs=0, rate_limit_time=0):
    data = {
        "resources": [
            {
                "cloudtrail_bucket_owner_id": cloudtrail_bucket_owner_id,
                "cloudtrail_bucket_region": cloudtrail_bucket_region,
                "external_id": external_id,
                "iam_role_arn": iam_role_arn,
                "id": local_account,
                # "rate_limit_reqs": "<integer>",
                # "rate_limit_time": "<long>"
            }
        ]
    }
    message = json.dumps({'default': json.dumps(data)})
    return message


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Params to send notification to CRWD topic')
    parser.add_argument('-r', '--cloudtrail_bucket_region', help='AWS Region where bucket is hosted', required=True)
    parser.add_argument('-o', '--cloudtrail_bucket_owner_id', help='Account where bucket is hosted', required=True)
    parser.add_argument('-a', '--local_account', help='This AWS Account', required=True)
    parser.add_argument('-e', '--external_id', help='External ID used to assume role in account', required=True)
    parser.add_argument('-i', '--iam_role_arn', help='IAM Role', required=True)
    parser.add_argument('-f', '--falcon_client_id', help='Falcon CID', required=True)
    parser.add_argument('-s', '--falcon_client_secret', help='Falcon CID', required=True)

    args = parser.parse_args()

    cloudtrail_bucket_region = args.cloudtrail_bucket_region
    cloudtrail_bucket_owner_id = args.cloudtrail_bucket_owner_id
    local_account = args.local_account
    external_id = args.external_id
    iam_role_arn = args.iam_role_arn
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    # Format post message
    api_message = format_notification_message()
    # Register account
    register_falcon_discover_account(api_message)
