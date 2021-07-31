import traceback
import os
import boto3
from botocore.exceptions import ClientError  # , EndpointConnectionError


def handleRecord(decoded_line):
    send = False
    cur_region = os.environ["AWS_REGION"]
    try:
        confirm = os.environ["CONFIRM_INSTANCES"]
    except KeyError:
        # Default to confirm the instance exists in the account (Non-MSSP)
        confirm = "True"
    if confirm.lower() != "false":
        if "instance_id" in decoded_line:
            region, instance = getInstance(decoded_line["instance_id"], decoded_line["detected_mac_address"])
            try:
                for iface in instance.network_interfaces:
                    decoded_line["vpc_id"] = instance.vpc_id
                    decoded_line["subnet_id"] = instance.subnet_id
                    decoded_line["image_id"] = instance.image_id
                    decoded_line["eni_id"] = iface.id
                    # Try and grab the instance name tag
                    try:
                        for tag in instance.tags:
                            if "name" in tag["Key"].lower():
                                decoded_line["instance_name"] = tag["Value"]
                    except (AttributeError, IndexError, KeyError):
                        decoded_line["instance_name"] = "Unnamed instance"

                send = True

            except ClientError:
                # Not our instance
                i_id = decoded_line["instance_id"]
                mac = decoded_line["mac_address"]
                e_msg = f"Instance {i_id} with MAC address {mac} not found in regions searched. Alert not processed."
                send_result = {"Error": e_msg}
        else:
            e_msg = "Instance ID not provided. Alert not processed."
            send_result = {"Error": e_msg}

    else:
        # We are not confirming instances, so we cannot identify it's region. Use our reporting region instead.
        region = cur_region
        send = True

    if send:
        send_result = sendToSecurityHub(generateManifest(decoded_line, cur_region, region), cur_region)

    return send_result


def generateManifest(detection_event, region, det_region):
    manifest = {}
    if "gov" in region:
        ARN = "arn:aws-us-gov:securityhub:{}:358431324613:product/crowdstrike/crowdstrike-falcon".format(region)
    else:
        ARN = "arn:aws:securityhub:{}:517716713836:product/crowdstrike/crowdstrike-falcon".format(region)
    try:
        manifest["SchemaVersion"] = "2018-10-08"
        manifest["ProductArn"] = f"{ARN}"
        accountID = boto3.client("sts").get_caller_identity().get('Account')
        manifest["AwsAccountId"] = accountID
        manifest["GeneratorId"] = detection_event["generator_id"]
        manifest["Types"] = detection_event["types"]
        manifest["CreatedAt"] = detection_event["created_at"]
        manifest["UpdatedAt"] = detection_event["updated_at"]
        manifest["RecordState"] = detection_event["record_state"]
        severityProduct = detection_event["severity"]
        severityNormalized = severityProduct * 20
        manifest["Severity"] = {"Product": severityProduct, "Normalized": severityNormalized}
        if "instance_id" in detection_event:
            manifest["Id"] = detection_event["instance_id"] + detection_event["detection_id"]
            manifest["Title"] = "Falcon Alert. Instance: %s" % detection_event["instance_id"]
            manifest["Resources"] = [{"Type": "AwsEc2Instance", "Id": detection_event["instance_id"], "Region": det_region}]
        else:
            manifest["Id"] = f"UnknownInstanceID:{detection_event['detection_id']}"
            manifest["Title"] = "Falcon Alert."
            manifest["Resources"] = [{"Type": "Other",
                                      "Id": f"UnknownInstanceID:{detection_event['detection_id']}",
                                      "Region": region
                                      }]
        desc = f"{detection_event['description']}"
        if "service_provider_account_id" in detection_event:
            aws_id = f"| AWS Account for alerting instance: {detection_event['service_provider_account_id']}"
        else:
            aws_id = ""
        description = f"{desc}    {aws_id}"
        manifest["Description"] = description
        manifest["SourceUrl"] = detection_event["source_url"]

    except Exception:
        print("Could not translate info for event %s\n%s" % (detection_event["detection_id"], traceback.format_exc()))
        return
    try:
        manifest["Types"] = ["Namespace: TTPs",
                             "Category: %s" % detection_event["tactic"],
                             "Classifier: %s" % detection_event["technique"]
                             ]
    except Exception:
        pass
    if "Process" in detection_event:
        manifest["Process"] = detection_event["Process"]
    if "Network" in detection_event:
        manifest["Network"] = detection_event["Network"]

    return manifest


def getInstance(instance_id, mac_address):
    # Instance IDs are unique to the region, not the account, so we have to check them all
    try:
        regions = os.environ["REGIONS"].split(",")
    except Exception:  # Prolly a KeyError
        ec2_client = boto3.client("ec2")
        regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
    for region in regions:
        ec2 = boto3.resource("ec2", region_name=region)
        try:
            ec2instance = ec2.Instance(instance_id)
            found = False
            # Confirm the mac address matches
            for iface in ec2instance.network_interfaces:
                det_mac = mac_address.lower().replace(":", "").replace("-", "")
                ins_mac = iface.mac_address.lower().replace(":", "").replace("-", "")
                if det_mac == ins_mac:
                    found = True
            if found:
                break
            else:
                ec2instance = False
        except ClientError:
            # This is the wrong region for this instance
            continue
        except Exception:
            # Something untoward has occurred, throw the error in the log
            tb = traceback.format_exc()
            print(str(tb))
            continue

    return region, ec2instance


def sendToSecurityHub(manifest, region):
    client = boto3.client('securityhub', region_name=region)
    check_response = {}
    found = False
    try:
        check_response = client.get_findings(Filters={'Id': [{'Value': manifest["Id"], 'Comparison': 'EQUALS'}]})
        for finding in check_response["Findings"]:
            found = True
    except Exception:
        pass

    import_response = {"message": "Finding already submitted to Security Hub. Alert not processed."}
    if not found:
        try:
            import_response = client.batch_import_findings(Findings=[manifest])
        except ClientError as err:
            # Boto3 issue communicating with SH, throw the error in the log
            print(str(err))
        except Exception:
            # Unknown error / issue, log the result
            tb = traceback.format_exc()
            print(str(tb))

    return import_response
