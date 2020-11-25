import json
import logging
import os
import sys

import api_complete as FalconSDK
import boto3
import credvault

vpcfw_client = boto3.client(service_name='network-firewall')

logger = logging.getLogger()

if os.environ.get('DEBUG_LEVEL') == 'DEBUG':
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)

if 'fw_domain_rg_name' in os.environ:
    RG_NAME = os.environ.get('fw_domain_rg_name')
else:
    RG_NAME = 'CrowdStrike_IR_Domain_List'

RG_TYPE = 'STATEFUL'


def update_domain_rule_group(domain_rule_group_name: str, domain_list: list, update_token: str):
    """
    Updates network firewall rule group
    """
    try:
        response = vpcfw_client.update_rule_group(
            RuleGroupName=domain_rule_group_name,
            RuleGroup={
                'RulesSource': {
                    'RulesSourceList': {
                        'Targets': domain_list,
                        'TargetType': [
                            'TLS_SNI', 'HTTP_HOST',
                        ],
                        'GeneratedRulesType': 'DENYLIST'
                    },
                }
            },
            Type='STATEFUL',
            Description='string',
            UpdateToken=update_token,
            DryRun=False
        )
        print(response)
        return response
    except Exception as e:
        logger.info('Got Exception updating rule group {}'.format(e))
        return


def describe_rule_group_by_name(rg_name: str, rg_type: str) -> dict:
    """

    :param rg_name: Name of the rule group
    :param rg_type: Type can be "STATELESS" or "STATEFUL"
    :return:
    """

    try:
        result = vpcfw_client.describe_rule_group(
            RuleGroupName=rg_name,
            Type=rg_type)
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            return result
        else:
            raise ValueError('Received non success response {}. Error {}')
    except Exception as e:
        logger.info('Got exception tyring to create rule group {}'.format(e))


def get_cs_finding(lambda_event: dict) -> dict:
    """

    :rtype: object
    :param lambda_event: Event containing CRWD finding
    """
    try:
        finding = lambda_event['detail']['findings'][0]
        finding_id = finding['Id']
        str_elements = finding_id.split(':')
        logger.debug('str_elements {}'.format(str_elements))
        aid = str_elements[1].strip()
        fid = str_elements[2].strip()
        cs_finding = {
            "ids": [
                f"ldt:{aid}:{fid}"
            ]
        }
        logger.debug('Finding we are looking for is {}'.format(cs_finding))
        return cs_finding
    except KeyError:
        logger.info('Cant get finding info')
        raise


def get_domain_info(detect_details: dict) -> str:
    """

    :param detect_details:
    """
    try:
        domain = detect_details['resources'][0]['behaviors'][0]['ioc_value']
        logger.debug('Got domain {} from detect_details {}'.format(domain, detect_details))
        return domain
    except KeyError:
        logger.info('No Domain information exists in detect_details {}'.format(detect_details))
        raise
    except Exception as e:
        logger.info('General exception {}'.format(e))
        raise


def lambda_handler(event, context):
    logger.debug('Got vpc_client {}'.format(vpcfw_client))
    logger.debug('Event = {}'.format(event))

    try:
        # Try to get our creds from ssm
        config = json.loads(credvault.CredVault().get())
    except Exception as e:
        logger.info('Failed to retrieve credentials error {}'.format(e))
        sys.exit(1)

    try:
        # Connect to the API
        falcon = FalconSDK.APIHarness(
            creds={'client_id': config["falcon_client_id"], 'client_secret': config["falcon_client_secret"]})
    except:
        logger.info("Failed to connect to the API")
        sys.exit(1)

    # Extract the CRWD finding id from the event
    cs_finding_query = get_cs_finding(event)
    # Fetch details of the detection from the CRWD API
    query_res = falcon.command(action="GetDetectSummaries", body=cs_finding_query)
    detect_details = query_res["body"]
    # De authenticate as we are finished with the API for now
    falcon.deauthenticate()
    domain = get_domain_info(detect_details)
    # Get details of the current domain resource group
    rg_info = describe_rule_group_by_name(RG_NAME, RG_TYPE)
    try:
        targets = rg_info['RuleGroup']['RulesSource']['RulesSourceList']['Targets']
    except KeyError:
        logger.info('Failed to get existing domains')
        raise
    # Get the update token required to modify the RG
    rg_update_token = rg_info.get('UpdateToken')
    if rg_update_token:
        if domain in targets:
            logger.debug('Domain {} already exists in list'.format(domain))
        else:
            targets.append(domain)
            result = update_domain_rule_group(RG_NAME, targets, rg_update_token)
            if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.debug('Successfully updated domain filter with {}'.format(targets))
            else:
                logger.debug('Failed to update domain filter')
    domain_rg = describe_rule_group_by_name('domain-deny-list', 'STATEFUL')
    logger.debug('New resource group is {}'.format(domain_rg))
