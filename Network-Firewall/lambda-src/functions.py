import logging
import os
import traceback

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()


def handleRecord(decoded_line):
    # Grab our region and instance
    region, instance = getInstance(decoded_line["instance_id"])
    for iface in instance.network_interfaces:
        decoded_line["vpc_id"] = instance.vpc_id
        decoded_line["subnet_id"] = instance.subnet_id
        decoded_line["image_id"] = instance.image_id
        decoded_line["eni_id"] = iface.id
        # Try and grab the instance name tag
        for tag in instance.tags:
            if "name" in tag["Key"].lower():
                decoded_line["instance_name"] = tag["Value"]
    logger.debug('Sending to security hub {}'.format(decoded_line))
    send_result = sendToSecurityHub(generateManifest(decoded_line, region), region)
    return send_result


def generateManifest(detection_event, region):
    manifest = {}
    try:
        manifest["SchemaVersion"] = "2018-10-08"
        manifest["ProductArn"] = "arn:aws:securityhub:%s:517716713836:product/crowdstrike/crowdstrike-falcon" % region
        manifest["AwsAccountId"] = detection_event["service_provider_account_id"]
        manifest["Id"] = detection_event["instance_id"] + detection_event["detection_id"]
        manifest["GeneratorId"] = detection_event["generator_id"]
        manifest["Types"] = detection_event["types"]
        manifest["CreatedAt"] = detection_event["created_at"]
        manifest["UpdatedAt"] = detection_event["updated_at"]
        manifest["RecordState"] = detection_event["record_state"]
        severityProduct = detection_event["severity"]
        severityNormalized = severityProduct * 20
        manifest["Severity"] = {"Product": severityProduct, "Normalized": severityNormalized}
        manifest["Title"] = "Falcon Alert. Instance: %s" % detection_event["instance_id"]
        manifest["Description"] = detection_event["description"]
        manifest["SourceUrl"] = detection_event["source_url"]
        manifest["Resources"] = [{"Type": "AwsEc2Instance", "Id": detection_event["instance_id"], "Region": region}]
    except:
        print("Could not translate info for event %s\n%s" % (detection_event["detection_id"], traceback.format_exc()))
        return
    try:
        manifest["Types"] = ["Namespace: TTPs", "Category: %s" % detection_event["tactic"],
                             "Classifier: %s" % detection_event["technique"]]
    except:
        pass
    if "Process" in detection_event:
        manifest["Process"] = detection_event["Process"]
    if "Network" in detection_event:
        manifest["Network"] = detection_event["Network"]

    return manifest


def getInstance(instance_id):
    # Instance IDs are unique to the region, not the account, so we have to check them all
    # I'm less than happy with this solution
    try:
        regions = os.environ["REGIONS"].split(",")
    except:
        ec2_client = boto3.client("ec2")
        regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]

    ec2instance = False
    for region in regions:
        ec2 = boto3.resource("ec2", region_name=region)
        try:
            ec2instance = ec2.Instance(instance_id)
            # Force a call
            checkId = ec2instance.vpc_id
            break
        except ClientError as err:
            logger.debug('Got error  {}'.format(err))
            # This is the wrong region for this instance
            continue
        except:
            # Something untoward has occurred, throw the error in the log
            tb = traceback.format_exc()
            logger.debug('Got error sending to security hub {}'.format(tb))
            continue

    return region, ec2instance


def sendToSecurityHub(manifest, region):
    client = boto3.client('securityhub', region_name=region)
    import_response = {}
    try:
        import_response = client.batch_import_findings(Findings=[manifest])
    except ClientError as err:
        # Boto3 issue communicating with SH, throw the error in the log
        logger.debug('Got error sending to security hub {}'.format(err))
    except:
        # Unknown error / issue, log the result
        tb = traceback.format_exc()
        logger.debug('Got error sending to security hub {}'.format(tb))

    return import_response
