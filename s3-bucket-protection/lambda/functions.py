"""S3 bucket protection functions."""
import traceback
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from julian import to_jd


def generate_manifest(detection, region, mitigating):
    """Generate a manifest for submission to Security Hub."""
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    now = datetime.now()
    create_date = f"{now.date()}T{now.time()}Z"
    jdate = to_jd(now)
    manifest = {}
    if mitigating:
        desc_msg = f"The file ({detection['file']}) has been removed from the bucket.\n"
    else:
        desc_msg = f"The file ({detection['file']}) was NOT removed from the bucket and should be removed manually.\n"
    try:
        manifest["SchemaVersion"] = "2018-10-08"
        manifest["ProductArn"] = f"arn:aws:securityhub:{region}:517716713836:product/crowdstrike/crowdstrike-falcon"
        manifest["AwsAccountId"] = account_id
        manifest["Id"] = f"{detection['bucket']}_{detection['sha']}_{detection['file']}_{jdate}"
        manifest["GeneratorId"] = "falconx-bucket-protection"
        manifest["Types"] = ["Software and Configuration Checks/Vulnerabilities/Malware"]
        manifest["CreatedAt"] = create_date
        manifest["UpdatedAt"] = create_date
        manifest["RecordState"] = "ACTIVE"
        manifest["Severity"] = {"Original": "CRITICAL", "Label": "CRITICAL"}
        manifest["Title"] = f"Falcon Alert. Malware detected in bucket: {detection['bucket']}"
        manifest["Description"] = f"Malware has recently been identified in S3 bucket {detection['bucket']}."
        manifest["Description"] = f"{manifest['Description']}\n\n{desc_msg}"
        manifest["Resources"] = [{"Type": "AwsS3Bucket", "Id": detection["bucket"], "Region": region}]
    except KeyError:
        print(f"Could not translate info for malware event in bucket {detection['bucket']}")
        print(traceback.format_exc())

    return manifest


def send_to_security_hub(manifest, region):
    """Send the alert finding to Security Hub."""
    client = boto3.client('securityhub', region_name=region)
    check_response = {}
    found = False
    try:
        check_response = client.get_findings(Filters={'Id': [{'Value': manifest["Id"], 'Comparison': 'EQUALS'}]})
    except (ClientError, EndpointConnectionError):
        print("Unable to access SecurityHub findings")

    for _ in check_response["Findings"]:
        found = True

    import_response = {"message": "Finding already submitted to Security Hub. Alert not processed."}
    if not found:
        try:
            import_response = client.batch_import_findings(Findings=[manifest])
        except (ClientError, EndpointConnectionError) as err:
            # Boto3 issue communicating with SH, throw the error in the log
            print("Unable to submit to SecurityHub. Check that integration is accepting findings.")
            print(err)

    return import_response

def check_quota(interface):
    """Retrieve the current quota details from the API and display the result."""
    quota_lookup = interface.get_scans()
    if not quota_lookup["status_code"] == 200:
        raise SystemExit("Unable to retrieve quota details from the API.")
    total = quota_lookup["body"]["meta"]["quota"]["total"]
    used = quota_lookup["body"]["meta"]["quota"]["used"]
    in_progress = quota_lookup["body"]["meta"]["quota"]["in_progress"]
    print(f"You have used {used:,} out of {total:,} scans available. "
          f"Currently {in_progress:,} scan{'s are' if in_progress != 1 else ' is'} running."
          )
    return bool(used<total)