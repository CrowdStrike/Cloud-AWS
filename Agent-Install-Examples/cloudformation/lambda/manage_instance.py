#
#    This is free and unencumbered software released into the public domain.
#
#    Anyone is free to copy, modify, publish, use, compile, sell, or
#    distribute this software, either in source code form or as a compiled
#    binary, for any purpose, commercial or non-commercial, and by any
#    means.
#
#    In jurisdictions that recognize copyright laws, the author or authors
#    of this software dedicate any and all copyright interest in the
#    software to the public domain. We make this dedication for the benefit
#    of the public at large and to the detriment of our heirs and
#    successors. We intend this dedication to be an overt act of
#    relinquishment in perpetuity of all present and future rights to this
#    software under copyright law.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#    OTHER DEALINGS IN THE SOFTWARE.

import json
import logging
import os

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = os.environ['AWS_REGION']
client_id = os.environ['Falcon_ClientID']
client_secret = os.environ['Falcon_Secret']


def get_ssm_secure_string(parameter_name):
    ssm = boto3.client("ssm", region_name=region)
    return ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )


def get_auth_token(client_id, client_secret):
    try:

        url = "https://api.crowdstrike.com/oauth2/token"

        payload = 'client_secret=' + client_secret + '&client_id=' + client_id
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.ok:
            response_object = (response.json())
            token = response_object.get('access_token', '')
            if token:
                return token
            else:
                return
    except Exception as e:
        logger.info('Got Exception {} getting auth token'.format(e))
        return


def get_auth_header(_auth_token: str) -> dict:
    if _auth_token:
        _auth_header = "Bearer " + _auth_token
        _headers = {
            "Authorization": _auth_header
        }
        return _headers


def manage_falcon_host(aid: list, action: str, falcon_id, falcon_secret) -> bool:
    """

    :param aid:
    :param action:
    :return:
    """
    url = "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name=" + action
    payload = json.dumps({"ids": aid})
    _auth_token = get_auth_token(falcon_id, falcon_secret)
    _auth_header = get_auth_header(_auth_token)
    headers = {

        'Content-Type': 'application/json',
    }
    headers.update(_auth_header)
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info('Delete request response was {}'.format(response))
        if response.status_code == 202:
            logger.info('Deleted instance {}'.format(aid))
            return True
        else:
            return False
    except Exception as e:
        logger.info('Got exception {} hiding host'.format(e))
        return False


def query_falcon_host(_auth_header, _host_filter):
    _url = "https://api.crowdstrike.com/devices/queries/devices/v1"
    _PARAMS = {"offset": 0,
               "limit": 10,
               "filter": _host_filter
               }
    _headers = {
        "Authorization": _auth_header
    }

    _response = requests.request("GET", _url, headers=_headers, params=_PARAMS)

    _json_obj = json.loads(_response.text.encode('utf8'))
    if len(_json_obj['resources']) != 0:
        return _json_obj['resources'][0]
    else:
        return


def lifecycle_hook_abandon(asg_message):
    """
    Method to send a response to the
    auto scale life cycle action.

    :param asg_message:
    :return:
    """
    asg = boto3.client('autoscaling', region)
    result = "ABANDON"

    # call autoscaling
    try:
        asg.complete_lifecycle_action(
            AutoScalingGroupName=asg_message['AutoScalingGroupName'],
            LifecycleHookName=asg_message['LifecycleHookName'],
            LifecycleActionToken=asg_message['LifecycleActionToken'],
            LifecycleActionResult=result)
    except Exception as e:
        logger.error("[complete_lifecycle_action]: {}".format(e))


def lifecycle_hook_success(asg_message):
    """
    Method to send a successful response to an
    ASG lifecycle action.

    :param asg_message:
    :return:
    """
    asg = boto3.client('autoscaling', region)
    result = "CONTINUE"

    # call autoscaling
    try:
        asg.complete_lifecycle_action(
            AutoScalingGroupName=asg_message['AutoScalingGroupName'],
            LifecycleHookName=asg_message['LifecycleHookName'],
            LifecycleActionToken=asg_message['LifecycleActionToken'],
            LifecycleActionResult=result)
    except Exception as e:
        logger.error("[complete_lifecycle_action]: {}".format(e))
        return False
    return True


def lambda_handler(event, context):
    """
    The entry point when this lambda function gets
    invoked.

    .. note:: The primary objective of this lambda function
              is to handle life-cycle hooks and to create / delete
              elastic network interfaces to assign / disassociate to / from
              instances.

    :param event: Encodes all the input variables to the lambda function, when
                      the function is invoked.
                      Essentially AWS Lambda uses this parameter to pass in event
                      data to the handler function.
    :param context: AWS Lambda uses this parameter to provide runtime information to your handler.
    :return: None
    """

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    event_type = ""
    logger.info('Got event {}'.format(event))

    event_type = ""

    # Coming here via Sns?
    if ('Records' in event):
        message = json.loads(event['Records'][0]['Sns']['Message'])
        logger.info("[MESSAGE]: {}".format(message))
        if 'Event' in message:
            if (message.get('Event') == "autoscaling:TEST_NOTIFICATION"):
                logger.info("[INFO]: GOT TEST NOTIFICATION. Do nothing")
                return
            elif (message.get('Event') == "autoscaling:EC2_INSTANCE_LAUNCH"):
                logger.info("[INFO]: GOT launch notification...will get launching event from lifecyclehook")
                # logger.info("[EVENT]: {}".format(event))
                return
            elif (message.get('Event') == "autoscaling:EC2_INSTANCE_TERMINATE"):
                logger.info("[INFO]: GOT terminate notification....will get terminating event from lifecyclehook")
                return
            elif (message.get('Event') == "autoscaling:EC2_INSTANCE_TERMINATE_ERROR"):
                logger.info("[INFO]: GOT a GW terminate error...raise exception for now")
                raise Exception("Failed to terminate a GW in an autoscale event")
                return
            elif (message.get('Event') == "autoscaling:EC2_INSTANCE_LAUNCH_ERROR"):
                logger.info("[INFO]: GOT a GW launch error...raise exception for now")
                raise Exception("Failed to launch a GW in an autoscale event")
                return
        elif 'LifecycleTransition' in message:
            if (message.get('LifecycleTransition') == "autoscaling:EC2_INSTANCE_LAUNCHING"):
                logger.info("[INFO] Lifecyclehook Launching\n")
                event_type = 'launch'
            elif (message.get('LifecycleTransition') == "autoscaling:EC2_INSTANCE_TERMINATING"):
                logger.info("[INFO] Lifecyclehook Terminating\n")
                event_type = 'terminate'
            else:
                logger.info("[ERROR]/[INFO] One of the other lifeycycle transition messages received\n")
                event_type = 'other'
    else:
        logger.info("[ERROR]: Something else entirely")
        raise Exception("[ERROR]: Something else entirely")
        return

    logger.info('Message that we are parsing is {}'.format(message))
    logger.info('event_type is {}'.format(event_type))

    lifecycle_hook_name = message['LifecycleHookName']
    asg_name = message['AutoScalingGroupName']
    ec2_instanceid = message['EC2InstanceId']
    logger.info('ec2_instanceid: ' + ec2_instanceid)

    if event_type == 'terminate':

        host_query_filter = "platform_name: 'Linux' + instance_id: '" + ec2_instanceid + "'"
        # For the demo we will api keys in env variables but this should be changed to store the keys in ssm
        # client_id = get_ssm_secure_string('Falcon_ClientID')['Parameter']['Value']
        # client_secret = get_ssm_secure_string('Falcon_Secret')['Parameter']['Value']
        #
        client_id = os.environ['Falcon_ClientID']
        client_secret = os.environ['Falcon_Secret']
        #
        # Change the above to use SSM
        #
        auth_token = get_auth_token(client_id, client_secret)
        if auth_token:
            auth_header = "Bearer " + auth_token
        falcon_aid = query_falcon_host(auth_header, host_query_filter)
        logger.info('Falcon aid is {}'.format(falcon_aid))
        host_action = 'hide_host'
        logger.info('Calling manage_falcon_host {}{}'.format(falcon_aid, host_action))
        manage_falcon_host([falcon_aid], host_action, client_id, client_secret)
        lifecycle_hook_success(message)

    elif event_type == 'launch':
        lifecycle_hook_success(message)
    else:
        lifecycle_hook_success(message)
