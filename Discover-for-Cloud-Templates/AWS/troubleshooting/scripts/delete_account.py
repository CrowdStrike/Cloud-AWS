#
# Script to register

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
# handler = logging.StreamHandler()
handler = RotatingFileHandler("account_register.log", maxBytes=20971520, backupCount=5)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

OAUTH2URL = "https://api.crowdstrike.com/oauth2/token"


def delete_falcon_discover_account(account) -> bool:
    url = f'https://api.crowdstrike.com/cloud-connect-aws/entities/accounts/v1?ids={account}'
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
        response = requests.request("DELETE", url, headers=headers)
        if response.status_code == 200:
            print('Deleted account')
            return True
        else:
            print('Delete failed with response \n {} \n{}'
                  .format(response.status_code, response["errors"][0]["message"]))
    except Exception as e:
        # logger.info('Got exception {} hiding host'.format(e))
        print(f'Got exception {e} hiding host')
        return


def get_auth_header(auth_token) -> str:
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token():
    payload = 'client_secret=' + falcon_client_secret + '&client_id=' + falcon_client_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.request("POST", OAUTH2URL, headers=headers, data=payload)
        if response.ok:
            response_object = (response.json())
            token = response_object.get('access_token', '')
            if token:
                return token
            else:
                return
    except Exception as e:
        print(f'Got exception {e} creating auth token')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Params to send notification to CRWD topic')

    parser.add_argument('-a', '--local_account', help='This AWS Account', required=True)
    parser.add_argument('-f', '--falcon_client_id', help='Falcon API key Client ID', required=True)
    parser.add_argument('-s', '--falcon_client_secret', help='Falcon API key Client Secret', required=True)

    args = parser.parse_args()

    local_account = args.local_account
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    # Register account
    delete_falcon_discover_account(local_account)
