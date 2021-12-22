"""Security Hub integration functions."""
import traceback
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from julian import to_jd


def generate_manifest(detection, region):
    """Generate a manifest for submission to Security Hub."""
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    now = datetime.now()
    create_date = f"{now.date()}T{now.time()}Z"
    jdate = to_jd(now)
    manifest = {}
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
        manifest["Description"] = f"{manifest['Description']}\n\n" + \
            f"The file ({detection['file']}) has been removed from the bucket.\n"
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
            print(str(err))
        except:  # pylint: disable=W0702
            # Unknown error / issue, log the result
            trace = traceback.format_exc()
            print(f"An error has occurred.\n{trace}")

    return import_response
