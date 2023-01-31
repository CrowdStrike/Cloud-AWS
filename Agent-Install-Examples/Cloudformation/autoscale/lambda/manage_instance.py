##
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
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#    OTHER DEALINGS IN THE SOFTWARE.

import json
import logging
import os
from base64 import b64decode

import boto3
from botocore.exceptions import ClientError
from falconpy import Hosts

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ['REGION']
CS_CLOUD = os.environ['CS_CLOUD']
SECRET_STORE_NAME = os.environ['SECRET_STORE_NAME']
SECRET_STORE_REGION = AWS_REGION


def get_secret(secret_name, secret_region):
    """
    Args:
        secret_name string: Name of the secret store
        secret_region string: Region where the secret store exists

    Returns dict: Returns CrowdStrike API clientID and secret in a dict

    """

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=secret_region
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

    except ClientError as error:
        logger.info('Error {} retrieving secrets'.format(error.response['Error']['Code']))
    except Exception:
        logger.info('Secrets manager client error')

    else:
        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']

        else:
            secret = b64decode(get_secret_value_response['SecretBinary'])
        return secret


def hide_falcon_instance(id_to_retrieve):
    """Hide the host from the Falcon Console."""

    try:

        print("Hiding terminated instance in Falcon")
        secret_str = get_secret(SECRET_STORE_NAME, AWS_REGION)
        if secret_str:
            secrets_dict = json.loads(secret_str)
            FalconClientId = secrets_dict['client_id']
            FalconSecret = secrets_dict['client_secret']

            hosts = Hosts(client_id=FalconClientId,
                          client_secret=FalconSecret,
                          base_url=CS_CLOUD
                          )

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
                    raise ValueError(
                        f"Received non success response {code} while attempting to hide host. Error: {msg}")

            else:
                returned = f"AWS instance: {id_to_retrieve} was not found in your Falcon tenant"

            return returned
        else:
            logger.info('Unable to retrieve secret from secret store {}'.format(SECRET_STORE_NAME))
    except Exception as err:
        logger.info('Failure while interacting with CrowdStrike backend Error {}'.format(err))


def lifecycle_hook_message(asg_message, lifecycle_result):
    """
    Method to send a response to the
    auto-scale life cycle action.

    :param asg_message:
    :return:
    """
    asg = boto3.client('autoscaling', AWS_REGION)
    result = "ABANDON"

    # call autoscaling
    try:
        asg.complete_lifecycle_action(
            AutoScalingGroupName=asg_message['AutoScalingGroupName'],
            LifecycleHookName=asg_message['LifecycleHookName'],
            LifecycleActionToken=asg_message['LifecycleActionToken'],
            LifecycleActionResult=lifecycle_result)
    except Exception as e:
        logger.error("[complete_lifecycle_action]: {}".format(e))


def lifecycle_hook_success(asg_message):
    """
    Method to send a successful response to an
    ASG lifecycle action.

    :param asg_message:
    :return:
    """
    asg = boto3.client('autoscaling', AWS_REGION)
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
              is to handle life-cycle hooks to manage the visibility of hosts in the CrowdStrike console.

    :param event: Encodes all the input variables to the lambda function, when
                      the function is invoked.
                      Essentially AWS Lambda uses this parameter to pass in event
                      data to the handler function.
    :param context: AWS Lambda uses this parameter to provide runtime information to your handler.
    :return: None
    """

    logger.debug('Got event {}'.format(event))
    if 'Records' not in event:
        logger.info("[ERROR]: Not found any records in event")
        return
    # Coming here via Sns?
    else:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        logger.info("[MESSAGE]: {}".format(message))
        if 'Event' in message:
            if message.get('Event') == "autoscaling:TEST_NOTIFICATION":
                logger.info("[INFO]: GOT TEST NOTIFICATION. Do nothing")
                return
            elif message.get('Event') == "autoscaling:EC2_INSTANCE_LAUNCH":
                logger.info("[INFO]: GOT launch notification...will get launching event from lifecycle hook")
                # logger.info("[EVENT]: {}".format(event))
                return
            elif message.get('Event') == "autoscaling:EC2_INSTANCE_TERMINATE":
                logger.info("[INFO]: GOT terminate notification....will get terminating event from lifecycle hook")
                return
            elif message.get('Event') == "autoscaling:EC2_INSTANCE_TERMINATE_ERROR":
                logger.info("[INFO]: GOT a GW terminate error...raise exception for now")
                return
            elif message.get('Event') == "autoscaling:EC2_INSTANCE_LAUNCH_ERROR":
                logger.info("[INFO]: GOT a GW launch error...raise exception for now")
                return
        elif 'LifecycleTransition' in message:
            if message.get('LifecycleTransition') == "autoscaling:EC2_INSTANCE_LAUNCHING":
                logger.info("[INFO] Lifecycle hook Launching\n")
                logger.info('Got launch message')
                result = "CONTINUE"

            elif message.get('LifecycleTransition') == "autoscaling:EC2_INSTANCE_TERMINATING":
                logger.info("[INFO] Lifecycle hook Terminating\n")
                logger.info('Got terminate message')
                ec2_instanceid = message['EC2InstanceId']
                logger.info('EC2 Instance : ' + ec2_instanceid)
                hide_falcon_instance(ec2_instanceid)
                result = "CONTINUE"
            else:
                logger.info("[ERROR]/[INFO] One of the other lifecycle transition messages received\n")
        # Send lifecycle message
        lifecycle_hook_message(message, result)
