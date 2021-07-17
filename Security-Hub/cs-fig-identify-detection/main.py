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

import json
import os
from functions import handleRecord


def lambda_handler(event, context):
    # Check for our debug flag
    try:
        debug = os.environ["DEBUG"]
        if "t" in str(debug).lower():
            debug = True
        else:
            debug = False
    except KeyError:
        debug = False

    try:
        # Process any SQS events
        if "Records" in event:
            # Originated from SQS, loop thru all of the records
            for record in event["Records"]:
                if "body" in record:
                    decoded_line = json.loads(record["body"])
                    return_msg = json.dumps(handleRecord(decoded_line))
        # Process any direct events
        elif "instance_id" in event:
            decoded_line = event
            return_msg = json.dumps(handleRecord(decoded_line))
        # Ignore all others
        else:
            return_msg = {"message": "No action performed"}
    except Exception as err:
        return_msg = {"message": f"Execution failure: {err}"}

    # Debug output
    if debug:
        print(return_msg)

    return {
        'statusCode': 200,
        'body': return_msg
    }
