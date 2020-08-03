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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Params to send notification to CRWD topic')

    parser.add_argument('-f', '--falcon_client_id', help='Falcon Client ID', required=True)
    parser.add_argument('-s', '--falcon_client_secret', help='Falcon Client Secret', required=True)
    args = parser.parse_args()
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    get_falcon_discover_accounts()
