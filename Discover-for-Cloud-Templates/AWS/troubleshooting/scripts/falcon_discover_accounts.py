"""CrowdStrike Falcon Discover Account registration utility

Leverages the FalconPy Service class to perform check, update, register
and delete operations within a customer Falcon Discover environment.
"""
#########################################################################
# falcon_discover_accounts - 2020.11.06                                 #
#                                                                       #
# Leverages the FalconPy API SDK to perform check, update, register and #
# delete operations within a customer Falcon Discover environment.      #
#                                                                       #
# PLEASE NOTE: This solution requires the falconpy SDK. This project    #
# can be accessed here: https://github.com/CrowdStrike/falconpy         #
#                                                                       #
# Modified - 2021.10.13 - Version 2, Added CrowdStrike cloud region     #
# !!! NOTE: This version requires FalconPy v0.7.2+ !!!                  #
#########################################################################
import argparse
import json
try:
    from falconpy import CloudConnectAWS
except ImportError as no_falconpy:
    raise SystemExit(
        "The CrowdStrike FalconPy library must be installed to run this utility."
        ) from no_falconpy


# ############## FORMAT API PAYLOAD
def format_api_payload(rate_limit_reqs=0, rate_limit_time=0):
    """Generate a properly formatted JSON payload for POST and PATCH requests."""
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
def check_account():  # pylint: disable=R0914
    """Return a list of accounts and their status."""
    # Retrieve the account list
    account_list = falcon.QueryAWSAccounts(limit=QUERY_LIMIT)["body"]["resources"]
    # Log the results of the account query to a file if logging is enabled
    if log_enabled:
        with open('falcon-discover-accounts.json', 'w+', encoding="utf-8") as file_output:
            json.dump(account_list, file_output)
    # Create a list of our account IDs out of account_list
    id_items = []
    for acct in account_list:
        id_items.append(acct["id"])

    # Returns the specified value for a specific account id within account_list
    def account_value(i, val):
        return [a[val] for a in account_list if a["id"] == i][0]  # noqa: E731
    q_max = 10    # VerifyAWSAccountAccess has a ID max count of 10
    for index in range(0, len(id_items), q_max):
        sub_acct_list = id_items[index:index + q_max]
        temp_list = list(sub_acct_list)
        # Check our AWS account access against the list of accounts returned in our query
        access_response = falcon.verify_aws_account_access(ids=temp_list)
        if access_response['status_code'] == 200 or access_response['status_code'] == 409:
            # Loop through each ID we verified
            resource_list = access_response["body"]["resources"]
            for result in resource_list:
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
                    except Exception:  # noqa: E722  pylint: disable=W0703
                        # The above call will produce an error if we're running
                        # check immediately after registering an account as
                        # the access_health branch hasn't been populated yet.
                        # Requery the API for the account_list when this happens.
                        account_list = falcon.QueryAWSAccounts(
                            parameters={"limit": f"{str(QUERY_LIMIT)}"}
                        )["body"]["resources"]
                        issue = account_value(result["id"], "access_health")["api"]["reason"]
                        print(f'Account {result["id"]} has a problem: {issue}')
                    # Output the account details to the user to assist with troubleshooting the account
                    print(f'Current settings {json.dumps(account_values_to_check, indent=4)}\n')
            for status in [status for status in (access_response["body"]["errors"] or [])]:  # pylint: disable=R1721
                # This account has an issue
                print(f'Account {status["id"]} has an error: {status["message"]}!')
        else:
            try:
                # An error has occurred
                print(f"Got response error code {access_response['status_code']}")
            except Exception:  # noqa: E722  pylint: disable=W0703
                # Handle any egregious errors that break our return error payload
                ecode = access_response["status_code"]
                emsg = access_response["body"]
                print(f"Got response error code {ecode} message {emsg}")


# ############## REGISTER ACCOUNT
def register_account():
    """Call the API to register the requested account."""
    register_response = falcon.ProvisionAWSAccounts(body=format_api_payload())
    if register_response["status_code"] == 201:
        print("Successfully registered account.")
    else:
        ecode = register_response['status_code']
        emsg = register_response['body']['errors'][0]['message']
        print(f"Registration failed with response: {ecode} {emsg}")


# ############## UPDATE ACCOUNT
def update_account():
    """Call the API to update the requested account."""
    update_response = falcon.UpdateAWSAccounts(body=format_api_payload())
    if update_response["status_code"] == 200:
        print("Successfully updated account.")
    else:
        ecode = update_response['status_code']
        emsg = update_response['body']['errors'][0]['message']
        print(f"Update failed with response: {ecode} {emsg}")


# ############## GET ACCOUNT
def get_account():
    """Call the API to retrieve the requested account."""
    get_response = falcon.GetAWSAccounts(ids=local_account)
    if get_response["status_code"] == 200:
        print(json.dumps(get_response["body"]["resources"][0], indent=4, sort_keys=True))
    else:
        get_status = get_response["status_code"]
        get_message = get_response["body"]["errors"][0]["message"]
        print(f"Update failed with response: {get_status} {get_message}")


# ############## DELETE ACCOUNT
def delete_account():
    """Call the API to delete the requested account(s).

    Multiple IDs can be deleted by passing in a comma-delimited list.
    """
    delete_response = falcon.DeleteAWSAccounts(ids=local_account)
    if delete_response["status_code"] == 200:
        print("Successfully deleted account.")
    else:
        ecode = delete_response['status_code']
        emsg = delete_response['body']['errors'][0]['message']
        print(f"Delete failed with response: {ecode} {emsg}")


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
    parser.add_argument('-a', '--local_account', help='This AWS Account', required=False)
    parser.add_argument("-u", "--crowdstrike_cloud", help="US1, US2, EU, USGOV1", required=False)
    parser.add_argument('-e', '--external_id', help='External ID used to assume role in account', required=False)
    parser.add_argument('-i', '--iam_role_arn',
                        help='IAM AWS IAM Role ARN that grants access to resources for Crowdstrike', required=False)
    # Always required
    parser.add_argument('-c', '--command',
                        help='Troubleshooting action to perform options are check, update, register, delete, get ',
                        required=True
                        )
    parser.add_argument("-f", "--falcon_client_id", help="Falcon Client ID", required=True)
    parser.add_argument("-s", "--falcon_client_secret", help="Falcon Client Secret", required=True)
    args = parser.parse_args()

    # ############## SET GLOBALS
    command = args.command
    # Only execute our defined commands
    if command.lower() in "check,update,register,delete,get".split(","):
        if command.lower() in "update,register".split(","):
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
        elif command.lower() in "delete,get".split(","):
            # Delete only requires the local account ID
            if args.local_account is None:
                parser.error(f"The {command} command requires the -a argument to also be specified.")
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
        falcon = CloudConnectAWS(client_id=falcon_client_id,
                                 client_secret=falcon_client_secret,
                                 base_url=CLOUD_URL
                                 )
    except Exception as err:  # noqa: E722  pylint: disable=W0703
        # We can't communicate with the endpoint
        print(f"Unable to communicate with API: {str(err)}")
    # Authenticate
    if falcon.auth_object.token()["status_code"] == 201:
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
            if command.lower() == "get":
                get_account()
        except Exception as err:  # pylint: disable=W0703
            # Handle any previously unhandled errors
            print(f"Command failed with error: {str(err)}.")
        # Discard our token before we exit
        falcon.auth_object.revoke(falcon.auth_object.token)
    else:
        # Report that authentication failed and stop processing
        print("Authentication Failure.")
