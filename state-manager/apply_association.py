"""Reapply a State Manager assocation.

 ______                         __ _______ __         __ __
|      |.----.-----.--.--.--.--|  |     __|  |_.----.|__|  |--.-----.
|   ---||   _|  _  |  |  |  |  _  |__     |   _|   _||  |    <|  -__|
|______||__| |_____|________|_____|_______|____|__|  |__|__|__|_____|

Creation date: 01.24.22 - jshcodes@CrowdStrike

Requirements: boto3
"""
from argparse import ArgumentParser, RawTextHelpFormatter
import boto3


def parse_command_line() -> object:
    """Parse the command line for inbound configuration parameters."""
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawTextHelpFormatter
        )
    parser.add_argument(
        '-r',
        '--region',
        help='AWS Region where association resides.',
        required=True
        )
    parser.add_argument(
        '-s',
        '--ssm_doc_name',
        help='SSM Document Name',
        required=True
        )

    return parser.parse_args()


# Consume inbound command line parameters
args = parse_command_line()

REGION = args.region
SSM_DOC_NAME = args.ssm_doc_name

ssm_client = boto3.client("ssm", region_name=REGION)

associations = ssm_client.list_associations(AssociationFilterList=[{
    "key": "Name",
    "value": SSM_DOC_NAME
}])

assoc_id = associations["Associations"][0]["AssociationId"]

start_result = ssm_client.start_associations_once(AssociationIds=[assoc_id])

req_id = start_result["ResponseMetadata"]["RequestId"]

if start_result["ResponseMetadata"]["HTTPStatusCode"] == 200:
    print(f"Re-applying association to install agent to new instances.\nRequest ID: {req_id}")
else:
    print("Unable to re-apply association.")
