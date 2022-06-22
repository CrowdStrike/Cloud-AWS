"""CrowdStrike Agent Deployment automation script.

 ______                         __ _______ __         __ __
|      |.----.-----.--.--.--.--|  |     __|  |_.----.|__|  |--.-----.
|   ---||   _|  _  |  |  |  |  _  |__     |   _|   _||  |    <|  -__|
|______||__| |_____|________|_____|_______|____|__|  |__|__|__|_____|

        Falcon Sensor deployment automation helper utility v1.0

Creation date: 01.22.22 - jshcodes@CrowdStrike, musayev-io@CrowdStrike

Requirements: boto3, crowdstrike-falconpy
"""
# pylint: disable=W0613,R0914,C0103
import boto3
try:
    from falconpy import OAuth2, SensorDownload, Hosts
except ImportError as no_falconpy:
    raise SystemExit("Unable to import CrowdStrike SDK. Check automation layer contents.") from no_falconpy


def get_ssm_params(events):
    """Retrieve the stored configuration parameters from SSM Parameter Store."""
    ssm = boto3.client('ssm', region_name=events["AWSRegion"])

    print('Fetching APIGatewayHostKey')
    apiGatewayHostResponse = ssm.get_parameter(Name=events["APIGatewayHostKey"], WithDecryption=True)
    if apiGatewayHostResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError(f"Required property {events['APIGatewayHostKey']} not found")

    base_url = apiGatewayHostResponse['Parameter']['Value']

    print('Fetching APIGatewayClientIDKey')
    apiGatewayClientIDResponse = ssm.get_parameter(Name=events["APIGatewayClientIDKey"], WithDecryption=True)
    if apiGatewayClientIDResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError(f"Required property {events['APIGatewayClientIDKey']} not found")

    cust_id = apiGatewayClientIDResponse['Parameter']['Value']

    print('Fetching APIGatewayClientSecretKey')
    apiGatewayClientSecretResponse = ssm.get_parameter(Name=events["APIGatewayClientSecretKey"], WithDecryption=True)
    if apiGatewayClientSecretResponse['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError(f"Required property {events['APIGatewayClientSecretKey']} not found")

    cust_secret = apiGatewayClientSecretResponse['Parameter']['Value']

    return base_url, cust_id, cust_secret


def get_install_params(events, context):
    """Retrieve necessary installation detail from CrowdStrike cloud."""
    api_base_url, api_client_id, api_client_secret = get_ssm_params(events)

    try:
        auth = OAuth2(client_id=api_client_id,
                      client_secret=api_client_secret,
                      base_url=api_base_url
                      )
    except Exception as err:
        raise ValueError(f"Failure while interacting with CrowdStrike backend. Error: {err}") from err

    try:
        print('Requesting Customer ID from CrowdStrike backend.')
        sensor = SensorDownload(auth_object=auth)
        get_ccid = sensor.get_sensor_installer_ccid()
        if get_ccid["status_code"] != 200:
            error_detail = get_ccid['body']['errors'][0]
            code = error_detail["code"]
            msg = error_detail["message"]
            raise ValueError(f"Received non success response {code}. Error: {msg}")
        customer_ccid = get_ccid['body']['resources'][0]
        print('Successfully received Customer ID.')
    except Exception as err:
        raise ValueError(f"Failure while interacting with CrowdStrike backend. Error {err}") from err

    try:
        hosts = Hosts(auth_object=auth)

        id_to_retrieve = events["InstanceIds"][0]
        host_aid = hosts.query_devices_by_filter(filter=f"instance_id:'{id_to_retrieve}'")

        skip_install = "NO"
        if host_aid["status_code"] == 200:
            if host_aid["body"]["resources"]:
                skip_install = "YES"
        print('Checked for a skipped install')

        return {
            'CCID': customer_ccid,
            'SkipInstall': skip_install
            }
    except Exception as err:
        raise ValueError(f"Failure while interacting with CrowdStrike backend. Error {err}") from err


def hide_falcon_instance(events, context):
    """Hide the host from the Falcon Console."""
    try:
        api_base_url, api_client_id, api_client_secret = get_ssm_params(events)

        print("Hiding terminated instance in Falcon")
        hosts = Hosts(client_id=api_client_id,
                      client_secret=api_client_secret,
                      base_url=api_base_url
                      )

        for id_to_retrieve in events["InstanceIds"]:
            host_aid = hosts.query_devices_by_filter(filter=f"instance_id:'{id_to_retrieve}'")

            if host_aid["status_code"] != 200:
                returned = f"AWS instance: {id_to_retrieve} was not found in your Falcon tenant"

            if host_aid["body"]["resources"]:
                falcon_host_id = host_aid["body"]["resources"][0]
                hide_result = hosts.perform_action(action_name="hide_host", ids=falcon_host_id)
                if hide_result["status_code"] == 202:
                    returned = (
                        f"AWS Instance: {id_to_retrieve} | Falcon Resource ID: {falcon_host_id} was "
                        "successfully hidden"
                    )
                elif hide_result["status_code"] == 404:
                    returned = (
                        f"AWS Instance: {id_to_retrieve} does not have a sensor installed."
                    )
                else:
                    err_detail = hide_result["body"]["errors"][0]
                    code = err_detail["code"]
                    msg = err_detail["message"]
                    raise ValueError(f"Received non success response {code} while attempting to hide host. Error: {msg}")

            else:
                returned = f"AWS instance: {id_to_retrieve} was not found in your Falcon tenant"

            return returned
    except Exception as err:
        raise ValueError(f"Failure while interacting with CrowdStrike backend. Error {err}") from err


def check_tags(events, context):
    """Check for the existence of the filter tag."""
    execute = "NO"
    ec2_client = boto3.client("ec2", region_name=events["AWSRegion"])
    found = ec2_client.describe_instances(
        InstanceIds=events["InstanceIds"],
        Filters=[{
            "Name": f"tag:{events['TagName']}",
            "Values": [events["TagValue"]]
        }]
    )

    if found["Reservations"]:
        execute = "YES"

    return {"ContinueRun": execute}
