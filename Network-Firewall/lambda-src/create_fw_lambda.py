#
# Temporary script to create network firewall.
# Delete when CFT template available
#
import json
import logging
import os
import sys
import time

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(level=logging.INFO)
filtered_domains = ['awesomeopensource.com']

fw_stateless_rg_name = os.environ['fw_stateless_rg_name']
fw_domain_rg_name = os.environ['fw_domain_rg_name']
fw_stateful_rg_name = os.environ['fw_stateful_rg_name']
fw_policy_name = os.environ['fw_policy_name']
fw_name = os.environ['fw_name']
fw_subnet_id = os.environ['fw_subnet_id']
route_table_id = os.environ['route_table_id']
s3_bucket = os.environ['s3_bucket']
vpc_id = os.environ['vpc_id']
private_subnet_cidr = os.environ['private_subnet_cidr']
gw_route_table_id = os.environ['gw_route_table_id']

fw_description = 'CrowdStrike Created Firewall for Demo purposes'
STATELESS_RG_DESC = 'Filter all TCP UDP ICMP'
STATEFUL_TCP_RG_FILENAME = 'stateful-tcp-rules.txt'
STATELESS_RG_FILENAME = 'stateless-rules.txt'
DESTINATION_CIDR_BLOCK = '0.0.0.0/0'
STATELESS_RG_DESC = 'Filter all TCP UDP ICMP'
FW_POLICY_DESC = 'CrowdStrike Demo Policy'

ec2_client = boto3.client('ec2')
vpcfw_client = boto3.client('network-firewall')


def create_stateful_rule_group(rg_name: str, description: str, rules_string: str, dry_run=False):
    """
    :param rg_name: Rule group name
    :param description: Rule group description
    :param rules_string: Rules as a string
    :param dry_run:
    :return: dict
    """

    try:
        response = vpcfw_client.create_rule_group(
            RuleGroupName=rg_name,
            RuleGroup={
                'RulesSource': {
                    'RulesString': rules_string,
                }
            },
            Type='STATEFUL',
            # Description=description,
            Capacity=500,
            Tags=[
                {
                    'Key': 'CS_MANAGED',
                    'Value': 'STATEFUL'
                }
            ],
            DryRun=dry_run
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug('Got response tp create_stateful_rule_group {}'.format(response))
            return response['RuleGroupResponse']
        else:
            return
    except Exception as e:
        logger.info('Exception calling create_rule_group {}'.format(e))
        sys.exit(1)


def read_file_from_s3(file_name, bucket_name):
    try:
        s3 = boto3.resource('s3')
        obj = s3.Object(bucket_name, file_name)
        body = obj.get()['Body'].read()
        return body
    except Exception as e:
        logger.info('Exception calling read_file {}'.format(e))


def create_stateless_ipfilter_rulegroup(rg_name: str, description: str, rg_dict: dict, dry_run: bool = False):
    try:
        result = vpcfw_client.create_rule_group(
            RuleGroupName=rg_name,
            RuleGroup=rg_dict,
            Type='STATELESS',
            Description=description,
            Capacity=100,
            Tags=[
                {
                    'Key': 'CSStatelessfilterRuleGroup',
                    'Value': rg_name
                },
            ],
            DryRun=dry_run)
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug('Got response tp create_stateless_filter {}'.format(result))
            return result['RuleGroupResponse']
        else:
            return
    except Exception as e:
        logger.info('Exception calling create_stateless_ipfilter_rulegroup {}'.format(e))
        sys.exit(1)


def describe_rule_group_by_name(rg_name: str, type: str):
    try:
        result = vpcfw_client.describe_rule_group(
            RuleGroupName=rg_name,
            # RuleGroupArn=rg_arn,
            Type=type)
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug('Got response tp create describe_rule_group {}'.format(result))
            return result
        else:
            return
    except vpcfw_client.exceptions.ResourceNotFoundException:
        logger.info('Resource group {} not found'.format(rg_name))
        return
    except Exception as e:
        logger.info('Exception calling describe_rule_group {}'.format(e))
        sys.exit(1)


def create_domain_filter_rule_group(rg_name: str, targets: list, action: str) -> dict:
    # action allowed values 'DENYLIST' | 'ALLOWLIST'

    rulegroup = {
        'RulesSource': {
            'RulesSourceList': {
                'Targets': targets,
                'TargetTypes': [
                    'TLS_SNI', 'HTTP_HOST'
                ],
                'GeneratedRulesType': action
            },
        }
    }
    try:
        result = vpcfw_client.create_rule_group(RuleGroupName=rg_name, RuleGroup=rulegroup, Capacity=1000,
                                                Type='STATEFUL')
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug('Got create rule group response {}'.format(result))
            return result['RuleGroupResponse']
        else:
            return
    except Exception as e:
        logger.info('Exception calling create_domain_filter {}'.format(e))
        sys.exit(1)


def check_rg_status(rule_group_list):
    for rg in rule_group_list:
        result = describe_rule_group_by_name(rg)
        while result['RuleGroupResponse']['RuleGroupStatus'] == 'CREATING':
            time.sleep(20)


def create_fw_policy(policy_name: str, stateless_rg_ref, stateful_rg_arns, stateless_action: str,
                     description: str, dry_run: bool = False):
    stateful_ruleGroup_references = []
    for arn in stateful_rg_arns:
        stateful_ruleGroup_references.append({
            "ResourceArn": arn
        })
    logger.info('RuleGroupArns {}'.format(stateful_ruleGroup_references))
    try:

        result = vpcfw_client.create_firewall_policy(
            FirewallPolicyName=policy_name,
            FirewallPolicy={
                "StatelessDefaultActions": [
                    stateless_action
                ],
                "StatelessRuleGroupReferences": [
                    {
                        "Priority": 5,
                        "ResourceArn": stateless_rg_ref
                    }
                ],
                "StatelessFragmentDefaultActions": ["aws:drop"],
                "StatefulRuleGroupReferences": stateful_ruleGroup_references
            },
            Description=description,
            DryRun=dry_run
        )
        logger.debug('Got create_fw_policy response {}'.format(result))
        return result

    except Exception as e:
        logger.info('Got Exception {} creating firewall policy'.format(e))


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    logger.info('Got response {} {} {} {}'.format(event, context, responseStatus, responseData))
    print(responseUrl)

    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': physicalResourceId or context.log_stream_name, 'StackId': event['StackId'],
                    'RequestId': event['RequestId'], 'LogicalResourceId': event['LogicalResourceId'], 'NoEcho': noEcho,
                    'Data': responseData}

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }
    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        logger.debug('cfn response {}'.format(response))
    except Exception as e:
        logger.info('Exception calling cfnresponse {}'.format(e))


def create_fw(name: str, fw_policy_arn: str, subnet_mapping: list, vpc_id: str, description: str,
              delete_protect: bool = False, ):
    try:
        response = vpcfw_client.create_firewall(
            FirewallName=name,
            FirewallPolicyArn=fw_policy_arn,
            VpcId=vpc_id,
            SubnetMappings=subnet_mapping,
            DeleteProtection=delete_protect,
            Description=description,
            Tags=[
                {
                    'Key': 'Creator',
                    'Value': 'CrowdStrike CFT'
                },
            ]
        )
        logger.debug('Got response to create_fw {}'.format(response))
        return response

    except Exception as e:
        logger.info('Got Exception creating firewall {}'.format(e))


def describe_firewall(fw_name):
    try:
        response = vpcfw_client.describe_firewall(
            FirewallName=fw_name,
            # FirewallArn = fw_policy_arn
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.debug('Got response to describe_firewall {}'.format(response))
            return response
        else:
            return
    except Exception as e:
        logger.info('Got Exception creating firewall {}'.format(e))


def get_fw_nic(subnet_id):
    fw_int = ec2_client.describe_network_interfaces(
        Filters=[{'Name': 'subnet-id', 'Values': [subnet_id]}])
    return fw_int['NetworkInterfaces'][0]['NetworkInterfaceId']


def delete_net_fw_route(route_table_id, destination_cidr_block):
    try:
        response = ec2_client.delete_route(
            DryRun=False,
            RouteTableId=route_table_id,
            DestinationCidrBlock=destination_cidr_block,
        )
        return response
    except Exception as e:
        logger.info('Got Exception adding route {}'.format(e))


def add_route_net_fw_nh(route_table_id, destination_cidr_block, vpce_id):
    """
    Adds a route to a VPC route table with next hop of the Firewall vpce_id
    :param route_table_id:
    :param destination_cidr_block:
    :param transit_gateway_id:
    :return:
    """

    try:
        response = ec2_client.create_route(
            DryRun=False,
            RouteTableId=route_table_id,
            DestinationCidrBlock=destination_cidr_block,
            VpcEndpointId=vpce_id
        )
        return response
    except Exception as e:
        logger.info('Got Exception adding route {}'.format(e))


def delete_firewall(fw_name):
    try:
        response = vpcfw_client.delete_firewall(
            FirewallName=fw_name
        )
        logger.info('Got response to delete_firewall {}'.format(response))
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response
        else:
            return
    except Exception as e:
        logger.info('Got Exception deleting fw {}'.format(e))
        return


def get_eni_attachment_id(fw_subnet_id):
    try:
        interfaces_dict = ec2_client.describe_network_interfaces(
            Filters=[
                {
                    'Name': 'subnet-id',
                    'Values': [fw_subnet_id]
                },
                {
                    'Name': 'attachment.device-index',
                    'Values': ['0']
                }]
        )
        return interfaces_dict
    except:
        logger.info('Could not find firewall nic')
        return


def detach_fw_nic(fw_eni_attachment_id, force=True, dryrun=False):
    response = ec2_client.detach_network_interface(
        AttachmentId=fw_eni_attachment_id,
        DryRun=dryrun,
        Force=force
    )


def delete_firewall_policy(fw_name):
    try:
        response = vpcfw_client.delete_firewall_policy(
            FirewallPolicyName=fw_name)
        logger.info('Got response to delete_firewall_policy {}'.format(response))
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:

            return response
        else:
            return
    except vpcfw_client.exceptions.ResourceNotFoundException:
        print('Resource group {} not found'.format(fw_name))
        return


def delete_fw_rule_group(rg_name: str, type: str) -> dict:
    try:
        result = vpcfw_client.delete_rule_group(
            RuleGroupName=rg_name,
            Type=type)
        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('Got response to delete_fw_rule_group {}'.format(result))
            return result
        else:
            return
    except vpcfw_client.exceptions.ResourceNotFoundException as error:
        logger.info('Rule group {} not found'.format(rg_name))
        return
    except Exception as e:
        logger.info('Got exception calling delete_fw_rule_group {}'.format(e))


def check_fw_ready(fw_name):
    while True:
        fw = vpcfw_client.describe_firewall(FirewallName=fw_name)
        if fw['FirewallStatus']['Status'] == 'READY':
            logger.info('Firewall Ready')
            break
        else:
            time.sleep(20)
            logger.info('Firewall not ready')
            continue
    return True


def get_fw_vpce_by_az(fw_name):
    '''
    Returns a Dict containing attachments by AZ

    '''

    fw = vpcfw_client.describe_firewall(FirewallName=fw_name)
    logger.info('fw data {}'.format(fw))
    attachment_data = []

    try:
        fw_attachments = fw['FirewallStatus']['SyncStates']
        # check that we have the vpce
        for k in fw_attachments:
            new_dict = {k: fw_attachments[k]['Attachment']['EndpointId']}
            attachment_data.append({k: fw_attachments[k]['Attachment']['EndpointId']})

        logger.info('attachment data {}'.format(attachment_data))
        return attachment_data
    except Exception as e:
        logger.info('Got exception checking attachments {}'.format(e))


def check_firewall_exists(fw_name):
    try:
        fw_list = vpcfw_client.list_firewalls()
        if fw_list:
            for fw in fw_list['Firewalls']:
                logger.info('Checking list entry {}'.format(fw))
                if fw['FirewallName'] == fw_name:
                    logger.info('Found firewall {}'.format(fw['FirewallName']))
                    return True

            logger.info('Firewall not found')
            return False
    except Exception as e:
        return True


def lambda_handler(event, context):
    # logger.info('Got event {}'.format(event))
    response_data = {}
    if event['RequestType'] in ['Create']:
        logger.info('Event = ' + event['RequestType'])
        rule_groups = []
        stateless_rules = json.loads((read_file_from_s3(STATELESS_RG_FILENAME, s3_bucket).decode("utf-8")))
        stateless_rg = create_stateless_ipfilter_rulegroup(fw_stateless_rg_name, STATELESS_RG_DESC, stateless_rules)
        stateless_rg_arn = stateless_rg['RuleGroupArn']
        logger.info('Stateless RG ARN {}'.format(stateless_rg_arn))
        domain_rg = create_domain_filter_rule_group(fw_domain_rg_name, filtered_domains, 'DENYLIST')
        domain_rg_arn = domain_rg['RuleGroupArn']
        logger.info('Domain RG ARN {}'.format(domain_rg_arn))
        # stateful_rules = read_file_from_s3(STATEFUL_TCP_RG_FILENAME, s3_bucket).decode("utf-8")
        # stateful_rg = create_stateful_rule_group(fw_stateful_rg_name, STATEFUL_TCP_RG_DESC, stateful_rules,
        #                                          dry_run=False)
        stateful_rg_arns = [domain_rg_arn]

        fw_policy = create_fw_policy(fw_policy_name, stateless_rg_arn, stateful_rg_arns, "aws:forward_to_sfe",
                                     FW_POLICY_DESC)
        fw_policy_desc = vpcfw_client.describe_firewall_policy(FirewallPolicyName=fw_policy_name)
        fw_policy_arn = fw_policy_desc['FirewallPolicyResponse']['FirewallPolicyArn']

        subnet_mapping = [
            {
                'SubnetId': fw_subnet_id,
            }
        ]
        fw = create_fw(fw_name, fw_policy_arn, subnet_mapping, vpc_id, fw_description)
        time.sleep(45)
        if check_fw_ready(fw_name):
            fw_attachments = get_fw_vpce_by_az(fw_name)
            logger.info('FW attachments {}'.format(fw_attachments))

        subnet_info = ec2_client.describe_subnets(SubnetIds=[fw_subnet_id])
        logger.info('subnet info {}'.format(subnet_info))
        az = subnet_info['Subnets'][0]['AvailabilityZone']
        for attachment in fw_attachments:
            if az in attachment:
                fw_vpce = attachment[az]

        logger.info('Creating route entry')
        # Remove existing routes
        delete_net_fw_route(route_table_id, DESTINATION_CIDR_BLOCK)
        # Add routes using Network Firewall as next hop
        add_route_net_fw_nh(route_table_id, DESTINATION_CIDR_BLOCK, fw_vpce)
        add_route_net_fw_nh(gw_route_table_id, private_subnet_cidr, fw_vpce)
        response_data["Status"] = "Success"
        cfnresponse_send(event, context, 'SUCCESS', response_data)
        return
    elif event['RequestType'] in ['Update']:
        logger.info('Event = ' + event['RequestType'])
        response_data["Status"] = "Success"
        cfnresponse_send(event, context, 'SUCCESS', response_data)
        return
    elif event['RequestType'] in ['Delete']:

        logger.info('Event = ' + event['RequestType'])
        response_data["Status"] = "Success"
        delete_net_fw_route(route_table_id, DESTINATION_CIDR_BLOCK)
        delete_net_fw_route(gw_route_table_id, private_subnet_cidr)
        if delete_firewall(fw_name):
            while True:
                if check_firewall_exists(fw_name):
                    time.sleep(10)
                    logger.info('Sleeping waiting for firewall to delete')
                    continue
                else:
                    break
            # Additional wait while policy lock is released
            time.sleep(30)
            if delete_firewall_policy(fw_policy_name):
                # Additional wait while rg lock is released
                time.sleep(60)
                delete_fw_rule_group(fw_stateless_rg_name, 'STATELESS')
                delete_fw_rule_group(fw_domain_rg_name, 'STATEFUL')

        cfnresponse_send(event, context, 'SUCCESS', response_data)
        return


if __name__ == '__main__':
    event = {
        "RequestType": "Create",
        "ServiceToken": "arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12",
        "ResponseURL": "https:\/\/cloudformation-custom-resource-response-useast2.s3.us-east-2.amazonaws.com\/arn%3Aaws%3Acloudformation%3Aus-east-2%3A517716713836%3Astack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424%7CTriggerLambda%7Cfd9e5caa-a2c8-4f3b-a7d8-71767f00fb24?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20201001T182718Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIAVRFIPK6PJGXMVAWW%2F20201001%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Signature=49ab44a3e5cfdfc3392429576e14f6bab2d61cb3f1113735ffba0c7d001ea533",
        "StackId": "arn:aws:cloudformation:us-east-2:517716713836:stack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424",
        "RequestId": "fd9e5caa-a2c8-4f3b-a7d8-71767f00fb24",
        "LogicalResourceId": "TriggerLambda",
        "ResourceType": "Custom::TriggerLambda",
        "ResourceProperties": {
            "ServiceToken": "arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12"
        }
    }
    context = ()
    lambda_handler(event, context)
