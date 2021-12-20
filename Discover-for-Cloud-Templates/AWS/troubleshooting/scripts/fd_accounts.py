"""CrowdStrike Falcon Discover Account registration utility

Leverages the FalconPy uber class to perform check, update, register
and delete operations within a customer Falcon Discover environment.
"""
##############################################################################
# fd_accounts - Creation date - 2020.11.14                                   #
#                                                                            #
# PLEASE NOTE: This solution requires the falconpy SDK, version 0.7.0+       #
# This project can be accessed here: https://github.com/CrowdStrike/falconpy #
#                                                                            #
# Modified 2021.10.13, Version 2 - Add support for all CrowdStrike clouds    #
##############################################################################
import argparse
import json
# Falcon SDK - All in one uber-class
from falconpy.api_complete import APIHarness


# ############## FORMAT API PAYLOAD
def format_api_payload(rate_limit_reqs=0, rate_limit_time=0):
    """Generates a properly formatted JSON payload for POST and PATCH requests."""
    data = {
        "resources": [
            {
                "cloudtrail_bucket_owner_id": cloudtrail_bucket_owner_id,
                "cloudtrail_bucket_region": cloudtrail_bucket_region,
                "external_id": external_id,
                "iam_role_arn": iam_role_arn,
                "id": local_account,
                "rate_limit_reqs": rate_limit_reqs,
                "rate_limit_time": rate_limit_time
            }
        ]
    }
    return data


# ############## CHECK ACCOUNTS
def check_account():
    """Retrieves all registered accounts and checks their status."""
    # Retrieve the account list
    account_list = falcon.command(action="QueryAWSAccounts",
                                  parameters={"limit": f"{str(QUERY_LIMIT)}"}
                                  )["body"]["resources"]
    # Log the results of the account query to a file if logging is enabled
    if log_enabled:
        with open('falcon-discover-accounts.json', 'w+') as file_output:
            json.dump(account_list, file_output)
    # Create a list of our account IDs out of account_list
    id_items = []
    for acct in account_list:
        id_items.append(acct["id"])
    # Returns the specified value for a specific account id within account_list
    def account_value(i, v): return [a[v] for a in account_list if a["id"] == i][0]  # noqa: E731
    q_max = 10    # VerifyAWSAccountAccess has a ID max count of 10
    for index in range(0, len(id_items), q_max):
        sub_acct_list = id_items[index:index + q_max]
        temp_list = ",".join([a for a in sub_acct_list])
        # Check our AWS account access against the list of accounts returned in our query
        access_response = falcon.command(action="VerifyAWSAccountAccess", ids=temp_list)
        if access_response['status_code'] == 200 or access_response['status_code'] == 409:
            # Loop through each ID we verified
            resource_list = access_response["body"]["resources"]
            for result in [result for result in (resource_list or [])]:
                if result["successful"]:
                    # This account is correctly configured
                    print(f'Account {result["id"]} is ok!')
                else:
                    # This account is incorrectly configured.  We'll use our account_value function to
                    # retrieve configuration values from the account list we've already ingested.
                    account_values_to_check = {
                        'id': result["id"],
                        'iam_role_arn': account_value(result["id"], "iam_role_arn"),
                        'external_id': account_value(result["id"], "external_id"),
                        'cloudtrail_bucket_owner_id': account_value(result["id"], "cloudtrail_bucket_owner_id"),
                        'cloudtrail_bucket_region': account_value(result["id"], "cloudtrail_bucket_region"),
                    }
                    # Use the account_value function to retrieve the
                    # access_health branch, which contains our api failure reason
                    try:
                        problem = account_value(result["id"], "access_health")["api"]["reason"]
                        print(f'Account {result["id"]} has a problem: {problem}')
                    except:  # noqa: E722
                        # The above call will produce an error if we're running
                        # check immediately after registering an account as
                        # the access_health branch hasn't been populated yet.
                        # Requery the API for the account_list when this happens.
                        account_list = falcon.command(action="QueryAWSAccounts",
                                                      parameters={"limit": f"{str(QUERY_LIMIT)}"}
                                                      )["body"]["resources"]
                        issue = account_value(result["id"], "access_health")["api"]["reason"]
                        print(f'Account {result["id"]} has a problem: {issue}')
                    # Output the account details to the user to assist with troubleshooting the account
                    print(f'Current settings {json.dumps(account_values_to_check, indent=4)}\n')
            for status in [status for status in (access_response["body"]["errors"] or [])]:
                # This account has an issue
                print(f'Account {status["id"]} has an error: {status["message"]}!')
        else:
            try:
                # An error has occurred
                print("Got response error code {}".format(access_response["status_code"]))
            except:  # noqa: E722
                # Handle any egregious errors that break our return error payload
                print("Got response error code {} message {}".format(access_response["status_code"], access_response["body"]))


# ############## REGISTER ACCOUNT
def register_account():
    """Call the API to update the requested account."""
    register_response = falcon.command(action="ProvisionAWSAccounts", parameters={}, body=format_api_payload())
    if register_response["status_code"] == 201:
        print("Successfully registered account.")
    else:
        reg_status = register_response["status_code"]
        reg_message = register_response["body"]["errors"][0]["message"]
        print(f"Registration failed with response: {reg_status} {reg_message}")


# ############## UPDATE ACCOUNT
def update_account():
    """Call the API to update the requested account."""
    update_response = falcon.command(action="UpdateAWSAccounts", body=format_api_payload())
    if update_response["status_code"] == 200:
        print("Successfully updated account.")
    else:
        up_status = update_response["status_code"]
        up_message = update_response["body"]["errors"][0]["message"]
        print(f"Update failed with response: {up_status} {up_message}")


# ############## DELETE ACCOUNT
def delete_account():
    """Call the API to delete the requested account,
    multiple IDs can be deleted by passing in a comma-delimited list
    """
    delete_response = falcon.command(action="DeleteAWSAccounts", parameters={}, ids=local_account)
    if delete_response["status_code"] == 200:
        print("Successfully deleted account.")
    else:
        del_status = delete_response["status_code"]
        del_message = delete_response["body"]["errors"][0]["message"]
        print(f"Delete failed with response: {del_status} {del_message}")


# ############## MAIN
if __name__ == "__main__":
    # Configure argument parsing
    parser = argparse.ArgumentParser(description="Get Params to send notification to CRWD topic")
    # Fully optional
    parser.add_argument('-q', '--query_limit', help='The query limit used for check account commands', required=False)
    parser.add_argument('-l', '--log_enabled', help='Save results to a file?', required=False, action="store_true")
    # Optionally required
    parser.add_argument('-r', '--cloudtrail_bucket_region', help='AWS Region where the S3 bucket is hosted',
                        required=False)
    parser.add_argument('-o', '--cloudtrail_bucket_owner_id', help='Account where the S3 bucket is hosted',
                        required=False)
    parser.add_argument("-u", "--crowdstrike_cloud", help="US1, US2, EU, USGOV1", required=False)
    parser.add_argument('-a', '--local_account', help='This AWS Account', required=False)
    parser.add_argument('-e', '--external_id', help='External ID used to assume role in account', required=False)
    parser.add_argument('-i', '--iam_role_arn',
                        help='IAM AWS IAM Role ARN that grants access to resources for Crowdstrike', required=False)
    # Always required
    parser.add_argument('-c', '--command', help='Troubleshooting action to perform', required=True)
    parser.add_argument("-f", "--falcon_client_id", help="Falcon Client ID", required=True)
    parser.add_argument("-s", "--falcon_client_secret", help="Falcon Client Secret", required=True)
    args = parser.parse_args()

    # ############## SET GLOBALS
    command = args.command
    # Only execute our defined commands
    if command.lower() in "check,update,register,delete":
        if command.lower() in "update,register":
            # All fields required for update and register
            if (args.cloudtrail_bucket_owner_id is None
                    or args.cloudtrail_bucket_region is None
                    or args.local_account is None
                    or args.external_id is None
                    or args.iam_role_arn is None):
                parser.error(f"The {command} command requires the -r, -o, -a, -e, -i arguments to also be specified.")
            else:
                cloudtrail_bucket_region = args.cloudtrail_bucket_region
                cloudtrail_bucket_owner_id = args.cloudtrail_bucket_owner_id
                local_account = args.local_account
                external_id = args.external_id
                iam_role_arn = args.iam_role_arn
        elif command.lower() in "delete":
            # Delete only requires the local account ID
            if args.local_account is None:
                parser.error(f"The {command} command requires the -l argument to also be specified.")
            else:
                local_account = args.local_account
    else:
        parser.error(f"The {command} command is not recognized.")
    # These globals exist for all requests
    falcon_client_id = args.falcon_client_id
    falcon_client_secret = args.falcon_client_secret
    if not args.crowdstrike_cloud:
        CLOUD_URL = "US1"
    else:
        CLOUD_URL = args.crowdstrike_cloud
    log_enabled = args.log_enabled
    if not args.query_limit:
        QUERY_LIMIT = 100
    else:
        QUERY_LIMIT = args.query_limit

    # ############## MAIN ROUTINE
    # Connect to the API using our provided falcon client_id and client_secret

    try:
        falcon = APIHarness(client_id=falcon_client_id,
                            client_secret=falcon_client_secret,
                            base_url=CLOUD_URL
                            )
    except Exception as err:  # noqa: E722
        # We can't communicate with the endpoint
        print(f'Unable to communicate with API {str(err)}')
    # Authenticate
    if falcon.authenticate():
        try:
            # Execute the command by calling the named function
            if command.lower() == "check":
                check_account()
            if command.lower() == "update":
                update_account()
            if command.lower() == "register":
                register_account()
            if command.lower() == "delete":
                delete_account()
        except Exception as err:
            # Handle any previously unhandled errors
            print(f"Command failed with error: {str(err)}.")
        # Discard our token before we exit
        falcon.deauthenticate()
    else:
        # Report that authentication failed and stop processing
        print("Authentication Failure.")
