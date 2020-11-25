# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <https://unlicense.org>
import logging

import boto3
import cfnresponse
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ssm_client = boto3.client('ssm')

def delete_ssm_params(parameter_names):
    try:
        response = ssm_client.delete_parameters(
            Names=parameter_names
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    except:
        logger.error("Unidentified error")

def create_ssm_param(parameter_name, parameter_description, parameter_value, parameter_type, overwrite):
    try:
        response = ssm_client.put_parameter(
            Name=parameter_name,
            Description=parameter_description,
            Value=parameter_value,
            Type=parameter_type,
            Overwrite=overwrite,
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    except ClientError as err:
        if err.response['Error']['Code'] == "ParameterAlreadyExists":
            logger.error("Parameter already exists")
        else:
            logger.error(str(err.response['Error']['Code']))
    except:
        logger.error("Unidentified error")


def lambda_handler(event, context):
    responseData = {}
    try:
        logger.info(event)
        if event['RequestType'] == 'Create':
            if "ResourceProperties" in event:
                keys = event["ResourceProperties"]
                for key in keys:
                    create_ssm_param(key, "", keys[key], "SecureString", True)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        elif event['RequestType'] == 'Update':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        elif event['RequestType'] == 'Delete':
            if "ResourceProperties" in event:
                parameter_list = []
                keys = event["ResourceProperties"]
                for key in keys:
                    parameter_list.append(key)
                delete_ssm_params(parameter_list)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        logger.error(str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {})
