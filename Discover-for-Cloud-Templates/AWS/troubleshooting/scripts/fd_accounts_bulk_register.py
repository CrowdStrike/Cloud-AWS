"""

falcon_discover_bulk_register - 2020.11.06
Modified: jhseceng - 06.16.2021
Modified: jshcodes - 06.21.2021

Leverages the FalconPy API SDK to perform check, update, register and
delete operations within a customer Falcon Discover environment.

PLEASE NOTE: This solution requires the falconpy SDK. This project
can be accessed here: https://github.com/CrowdStrike/falconpy

Accepts a json file in the following format:

{
  "resources": [
    {
        "cloudtrail_bucket_owner_id": "BUCKET_OWNER_ACCOUNT_ID_HERE",
        "cloudtrail_bucket_region": "AWS_REGION_HERE",
        "external_id": "EXTERNAL_ID_HERE",
        "iam_role_arn": "arn:aws:iam::ACCOUNT_ID_HERE:role/FalconDiscover",
        "id": "ACCOUNT_ID_HERE"
    },
    {
        "cloudtrail_bucket_owner_id": "BUCKET_OWNER_ACCOUNT_ID_HERE",
        "cloudtrail_bucket_region": "AWS_REGION_HERE",
        "external_id": "EXTERNAL_ID_HERE",
        "iam_role_arn": "arn:aws:iam::ACCOUNT_ID_HERE:role/FalconDiscover",
        "id": "ACCOUNT_ID_HERE"
    }
  ]
}

"""
import argparse
import json
# Falcon SDK - Cloud_Connect_AWS API service classes
# Use: pip3 install crowdstrike-falconpy
from falconpy import cloud_connect_aws as FalconAWS

DEBUG = False


# REGISTER ACCOUNT
def register_account(accounts):
    # Call the API to update the requested account.
    register_response = falcon_discover.ProvisionAWSAccounts(parameters={}, body=accounts)
    if register_response["status_code"] == 201:
        print("Successfully registered account(s).")
    else:
        print("Registration failed with response: {} {}".format(register_response["status_code"],
                                                                register_response["body"]["errors"][0]["message"]))
    return


# UPDATE ACCOUNT
def update_accounts(accounts):
    # Call the API to update the requested account.
    update_response = falcon_discover.UpdateAWSAccounts(body=accounts)
    if update_response["status_code"] == 200:
        print("Successfully updated account(s).")
    else:
        print("Update failed with response: {} {}".format(update_response["status_code"],
                                                          update_response["body"]["errors"][0]["message"]))
    return


# IMPORT ACCOUNT FILE
def import_accounts_from_file(filename):
    with open(filename, newline='') as f:
        data = json.load(f)
        # Iterating through the list
        if DEBUG:
            for account in data['resources']:
                print(account['id'])
        return data


# MAIN
if __name__ == "__main__":
    # Configure argument parsing
    parser = argparse.ArgumentParser(description="Get Params to send notification to CRWD topic")
    # Fully optional
    parser.add_argument('-l', '--log_enabled', help='Save results to a file?', required=False, action="store_true")
    # Always required
    parser.add_argument('-d', '--data_file', help='File name of csv file containing accounts', required=True)
    parser.add_argument('-c', '--command', help='Troubleshooting action to perform', required=True)
    parser.add_argument("-f", "--falcon_client_id", help="Falcon Client ID", required=True)
    parser.add_argument("-s", "--falcon_client_secret", help="Falcon Client Secret", required=True)
    args = parser.parse_args()

    # SET GLOBALS
    command = args.command
    # Only execute our defined commands
    if command.lower() in "update,register":
        if (args.data_file is None):
            parser.error(
                "The {} command requires the -d arguments to also be specified.".format(command))
        else:
            filename = args.data_file
            falcon_client_id = args.falcon_client_id
            falcon_client_secret = args.falcon_client_secret
    else:
        parser.error("The {} command is not recognized.".format(command))
        # These globals exist for all requests

    accounts = import_accounts_from_file(filename)

    # Authenticate using our provided falcon client_id and client_secret
    falcon_discover = FalconAWS.Cloud_Connect_AWS(creds={'client_id': falcon_client_id, 'client_secret': falcon_client_secret})
    # Confirm we authenticated
    if not falcon_discover.authenticated():
        # Report that authentication failed and stop processing
        print("Failed to retrieve authentication token.")
    else:
        try:
            # Execute the command by calling the named function
            if command.lower() == "register":
                register_account(accounts)
            elif command.lower() == "update":
                update_accounts(accounts)
            else:
                print(f"{command} is not a valid command.")
        except Exception as e:
            # Handle any previously unhandled errors
            print("Command failed with error: {}.".format(str(e)))
        # Discard our token before we exit
        falcon_discover.auth_object.revoke(falcon_discover.token)
