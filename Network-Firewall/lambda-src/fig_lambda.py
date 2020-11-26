import json
import logging
import os

from functions import handleRecord

logger = logging.getLogger()


def lambda_handler(event, context):
    # Check for our debug flag
    try:
        debug = os.environ["DEBUG"]
        if "t" in str(debug).lower():
            debug = True
            logger.setLevel(logging.DEBUG)
        else:
            debug = False
            logger.setLevel(logging.INFO)
    except:
        debug = False
        logger.setLevel(logging.INFO)

    try:
        # Process any SQS events
        if "Records" in event:
            # Originated from SQS, loop thru all of the records
            for record in event["Records"]:
                logger.debug('Processing record {}'.format(record))
                if "body" in record:
                    decoded_line = json.loads(record["body"])
                    return_msg = json.dumps(handleRecord(decoded_line))
        # Process any direct events
        elif "instance_id" in event:
            decoded_line = event
            return_msg = json.dumps(handleRecord(decoded_line))
        # Ignore all others
        else:
            return_msg = {"message": "No action performed - no instance_id"}
    except Exception as e:
        logger.debug('Got exception processing message {}'.format(e))
        return_msg = {"message": "Execution failure"}

    # Debug output
    logger.debug('Return message {}'.format(return_msg))

    return {
        'statusCode': 200,
        'body': return_msg
    }
