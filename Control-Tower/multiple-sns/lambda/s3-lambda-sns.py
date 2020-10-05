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
#


import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

topic_arns = os.environ[topic_arns]

s3 = boto3.client('s3')


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    logger.info('Got context {}'.format(context))

    # Create an SNS client
    sns = boto3.client('sns')

    # Publish a simple message to the specified SNS topics
    for topic in topic_arns:
        response = sns.publish(
            TopicArn=topic,
            Message=json.dumps(event),
        )
    logger.info('Publish response {}'.format(response))
