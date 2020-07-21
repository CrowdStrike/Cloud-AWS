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

import argparse
import json
import logging
import sys
from logging.handlers import RotatingFileHandler

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
handler = RotatingFileHandler(
    "./get_registered_accounts.log", maxBytes=20971520, backupCount=5)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def get_falcon_discover_accounts(sortby=None, filterby=None) -> bool:
    """
    Prints a list of accounts that require modification and tries to indicate possible reasons for errors.
    :param sortby:
    :param filterby:
    :return: Bool indicating if API call succeeded.
    """
    good_accounts = []
    bad_accounts = []

    url = "https://api.crowdstrike.com/cloud-connect-aws/combined/accounts/v1"
    PARAMS = {'limit': '100'}
    if filterby:
        PARAMS.update({'filter': filterby})
    if sortby:
        PARAMS.update({'sort': sortby})

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
        response = requests.request('GET', url, headers=headers, params=PARAMS)
        response_content = json.loads(response.text)
        logger.info('Response to register = {}'.format(response_content))

        good_exit = 200
        if response.status_code == good_exit:
            accounts_list = response_content['resources']

            for account in accounts_list:
                # print(json.dumps(account, indent=4))
                if account['provisioning_state'] != "registered" or not account['access_health']['api']['valid']:
                    bad_accounts.append(account)
                else:
                    good_accounts.append(account)

            print('\nThese accounts have problems ')
            for accountval in bad_accounts:
                # print('\tAccount: {}'.format(accountid))
                print('AWS AccountId : {}'.format(accountval['id']))
                if account['provisioning_state'] != "registered":
                    reason = "Account provisioning state is not set to registered"
                else:
                    reason = account['access_health']['api']['reason']
                print('Reason: {}'.format(reason))
                account_values_to_check = {
                    'id': accountval['id'],
                    'iam_role_arn': accountval['iam_role_arn'],
                    'external_id': accountval['external_id'],
                    'cloudtrail_bucket_owner_id': accountval['cloudtrail_bucket_owner_id'],
                    'cloudtrail_bucket_region': accountval['cloudtrail_bucket_region'],
                }
                print(json.dumps(account_values_to_check, indent=4))

            print('\nThese accounts are ok ')
            for accountval in good_accounts:
                print('\tAccount: {}'.format(accountval['id']))
            return True
        else:
            error_code = response.status_code
            error_msg = response_content["errors"][0]["message"]
            logger.info('Got response error code {} \nmessage {}'.format(error_code, error_msg))
            return
    except Exception as e:
        logger.info('Got exception {}'.format(e))
        return


def get_auth_header(auth_token) -> str:
    """
    Generates the authentication headers required in the API request
    :param auth_token: OAuth2 token as string
    :return header as string
    """
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token() -> str:
    """
    Generates the OAuth2 token from credentials supplied in args
    :return: OAuth2 token as string or Null if auth fails
    """
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Params to send notification to CRWD topic')

    parser.add_argument('-f', '--falcon_client_id', help='Falcon Client ID', required=True)
    parser.add_argument('-s', '--falcon_client_secret', help='Falcon Client Secret', required=True)
    args = parser.parse_args()
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    get_falcon_discover_accounts()
