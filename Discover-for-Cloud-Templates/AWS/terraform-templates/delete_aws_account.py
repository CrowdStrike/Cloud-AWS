#
# Script to register

import argparse
import json
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


def delete_falcon_discover_accounts(account, sortby=None, filterby=None) -> bool:
    """
    Prints a list of accounts that require modification and tries to indicate possible reasons for errors.
    :param sortby:
    :param filterby:
    :return: Bool indicating if API call succeeded.
    """

    url = "https://api.crowdstrike.com/cloud-connect-aws/entities/accounts/v1"

    PARAMS = {'ids': account}

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
        response = requests.request('DELETE', url, headers=headers, params=PARAMS)
        response_content = json.loads(response.text)
        logger.info('Response to register = {}'.format(response_content))

        good_exit = 200
        if response.status_code == good_exit:
            return True
        else:
            error_code = response.status_code
            error_msg = response_content["errors"][0]["message"]
            logger.info('Got response error code {} \nmessage {}'.format(error_code, error_msg))
            return False
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

    parser.add_argument('-a', '--account', help='The AWS Account to delete', required=True)
    parser.add_argument('-f', '--falcon_client_id', help='Falcon CID', required=True)
    parser.add_argument('-s', '--falcon_client_secret', help='Falcon CID', required=True)

    args = parser.parse_args()

    account = args.account
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    # Format post message

    # Delete account
    delete_falcon_discover_accounts(account)
