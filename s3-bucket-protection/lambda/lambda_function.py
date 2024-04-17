r"""CrowdStrike S3 Bucket Protection with QuickScan.

 _______                        __ _______ __        __ __
|   _   .----.-----.--.--.--.--|  |   _   |  |_.----|__|  |--.-----.
|.  1___|   _|  _  |  |  |  |  _  |   1___|   _|   _|  |    <|  -__|
|.  |___|__| |_____|________|_____|____   |____|__| |__|__|__|_____|
|:  1   |                         |:  1   |
|::.. . |                         |::.. . |
`-------'                         `-------'

Creation     : 09.01.21 - jshcodes@CrowdStrike, v1.0
Modification : 12.21.21 - jshcodes@CrowdStrike, v1.1
Modification : 03.21.23 - jshcodes@CrowdStrike, v1.2

This lambda handler requires the CrowdStrike FalconPy lambda layer.
Download the latest version: https://falconpy.io/downloads/falconpy-layer.zip
"""
import io
import os
import time
import logging
import urllib.parse
import json
import boto3
from botocore.exceptions import ClientError
# FalconPy SDK - Auth, Sample Uploads and Quick Scan
try:
    from falconpy import OAuth2, SampleUploads, QuickScan
except ImportError as no_falconpy:
    raise SystemExit("The crowdstrike-falconpy layer is not available") from no_falconpy
from functions import generate_manifest, send_to_security_hub, check_quota

# Current version
APP_VERSION = 1.2

# Maximum file size for scan (35mb)
MAX_FILE_SIZE = 36700160

# Log config
log = logging.getLogger()
log.setLevel(logging.INFO)

# Boto handlers
s3 = boto3.resource('s3')
ssm = boto3.client('ssm')

# Current region
region = os.environ.get('AWS_REGION')

# Mitigate threats?
MITIGATE = bool(json.loads(os.environ.get("MITIGATE_THREATS", "TRUE").lower()))

# Base URL
try:
    BASE_URL = os.environ["BASE_URL"]
except KeyError:
    # Cloud region autodiscovery will not work in GovCloud, specify usgov1 for BASE_URL instead
    BASE_URL = "auto"

# Grab our SSM parameter store variable names from the environment if they exist
try:
    CLIENT_ID_PARAM_NAME = os.environ["CLIENT_ID_PARAM"]
except KeyError:
    CLIENT_ID_PARAM_NAME = "BUCKET_SCAN_CLIENT_ID"

try:
    CLIENT_SEC_PARAM_NAME = os.environ["CLIENT_SECRET_PARAM"]
except KeyError:
    CLIENT_SEC_PARAM_NAME = "BUCKET_SCAN_CLIENT_SECRET"

# Grab our Falcon API credentials from SSM Parameter Store
try:
    ssm_response = ssm.get_parameters(Names=[CLIENT_ID_PARAM_NAME, CLIENT_SEC_PARAM_NAME],
                                      WithDecryption=True
                                      )
    client_id = ssm_response['Parameters'][0]['Value']
    client_secret = ssm_response['Parameters'][1]['Value']

except IndexError as no_creds:
    raise SystemExit("Unable to retrieve CrowdStrike Falcon API credentials.") from no_creds

except KeyError as bad_creds:
    raise SystemExit("Unable to retrieve CrowdStrike Falcon API credentials.") from bad_creds

# Authenticate to the CrowdStrike Falcon API
auth = OAuth2(client_id=client_id,
              client_secret=client_secret,
              base_url=BASE_URL,
              user_agent=f"crowdstrike-s3protection/{APP_VERSION}"
              )

# Connect to the Samples Sandbox API
Samples = SampleUploads(auth_object=auth)
# Connect to the Quick Scan API
Scanner = QuickScan(auth_object=auth)


# Main routine
def lambda_handler(event, _):  # pylint: disable=R0912,R0914,R0915
    """Lambda execution entry point."""
    returned = ""
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket = s3.Bucket(bucket_name)
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    upload_file_size = int(
        bucket.Object(key=key).get()["ResponseMetadata"]["HTTPHeaders"]["content-length"]
        )
    if upload_file_size > MAX_FILE_SIZE:
        returned = f"File ({key}) exceeds maximum file scan size ({MAX_FILE_SIZE} bytes), skipped."
        log.warning(returned)
        raise SystemExit(returned)

    if not check_quota(Scanner):
        returned = "QuickScan quota exceeded. Unable to continue."
        log.error(returned)
        raise SystemExit(returned)

    try:
        filename = os.path.basename(key)
        response = Samples.upload_sample(file_name=filename,
                                         file_data=io.BytesIO(
                                            bucket.Object(key=key).get()["Body"].read()
                                            )
                                         )
    except Exception as err:
        returned = f"Error uploading {key} from bucket {bucket_name} to Falcon Intelligence Sandbox. "
        returned = f"{returned}Make sure your API key has the Sample Uploads WRITE scope."
        log.error(returned)
        raise SystemExit(returned)

    try:
        # Uploaded file unique identifier
        upload_sha = response["body"]["resources"][0]["sha256"]
        # Scan request ID, generated when the request for the scan is made
        scan_id = Scanner.scan_samples(samples=upload_sha)["body"]["resources"][0]
        scanning = True
        # Loop until we get a result or the lambda times out
        while scanning:
            # Retrieve our scan using our scan ID
            scan_results = Scanner.get_scans(ids=scan_id)
            try:
                if scan_results["body"]["resources"]:
                    if scan_results["body"]["resources"][0]["status"] == "done":
                        # Scan is complete, retrieve our results (there will be only one)
                        result = scan_results["body"]["resources"][0]["samples"][0]
                        # and break out of the loop
                        scanning = False
                # Not done yet, sleep for a bit
                time.sleep(3)
            except IndexError:
                # Results aren't populated yet, wait a sec and try again
                time.sleep(1)
        if result["sha256"] == upload_sha:
            if "no specific threat" in result["verdict"]:
                # File is clean
                returned = f"Bucket: {bucket_name} No threat found in {key}"
                log.info(returned)
            elif "unknown" in result["verdict"]:
                if "error" in result:
                    # Error occurred
                    returned = f"Bucket: {bucket_name} Scan error for {key}: {result['error']}"
                else:
                    # Undertermined scan failure
                    returned = f"Bucket: {bucket_name} Unable to scan {key}"
                log.warning(returned)
            elif "malware" in result["verdict"]:
                # Mitigation triggers from here
                returned = f"Bucket: {bucket_name} Verdict for {key}: {result['verdict']}"
                detection = {}
                detection["sha"] = upload_sha
                detection["bucket"] = bucket_name
                detection["file"] = key
                log.critical(returned)
                threat_removed = False
                if MITIGATE:
                    # Remove the threat
                    try:
                        s3.Object(bucket_name, key).delete()
                        threat_removed = True
                    except ClientError as err:
                        log.error("Unable to remove threat %s from bucket %s", key, bucket_name)
                        print(err)
                else:
                    # Mitigation is disabled. Complain about this in the log.
                    log.warning("Threat discovered (%s). Mitigation disabled, threat persists in %s bucket.",
                                key,
                                bucket_name
                                )
                # Inform Security Hub of the threat and our mitigation status
                manifest = generate_manifest(detection, region, threat_removed)
                _ = send_to_security_hub(manifest, region)
            else:
                # Unrecognized response
                returned = f"Unrecognized response ({result['verdict']}) received from API for {key}."
                log.warning(returned)

        # Clean up the artifact in the sandbox
        response = Samples.delete_sample(ids=upload_sha)
        if response["status_code"] > 201:
            log.warning("Could not remove sample (%s) from sandbox.", key)

    except Exception as err:
        returned = f"General error processing object {key} from bucket {bucket_name}. "
        returned = f"{returned}Make sure they exist and your bucket is in the same region as this function."
        returned = f"{returned}\n{err}"
        log.error(returned)
        raise SystemExit(returned)

    return returned

    #           ██████
    #         ██      ██
    #         ██    ████
    #         ██  ██▓▓████░░
    #         ████▓▓░░██  ██░░░░
    #         ██▓▓░░░░██░░░░██░░░░░░
    #       ██▓▓░░░░██░░██▒▒▓▓██░░░░░░     Let's pour out
    #     ██▓▓░░░░  ░░██▒▒▓▓▓▓████░░░░        the spoiled bits.
    #   ██▓▓░░░░  ░░░░▒▒▓▓▓▓████  ░░░░░░
    #   ██░░░░  ░░░░▒▒▓▓▓▓████    ░░░░░░
    #   ██░░  ░░░░▒▒▒▒▓▓████        ░░░░
    #     ██░░░░▒▒▓▓▓▓████        ░░░░░░
    #       ██▒▒▓▓▓▓████          ░░░░
    #         ██▓▓████            ░░░░
    #           ████              ░░
