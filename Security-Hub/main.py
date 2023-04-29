"""
CrowdStrike / Security Hub integration

Original version: Dixon Styres
Modification: 11.15.20 - jshcodes@CrowdStrike, SQS integration
Modification: 07.15.21 - jshcodes@CrowdStrike, MSSP functionality
Modification: 12.14.21 - jshcodes@CrowdStrike, FalconPy Updates, SSL verification tweaks

Event Streams -> {Parsed & Confirmed} -> SQS -> Lambda -> {Instance Confirmed} -> Security Hub
"""
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
import sys
import platform
import time
import threading
import atexit
from falconpy import APIHarness
try:
    import boto3
    from botocore.exceptions import ClientError, EndpointConnectionError
except ImportError as no_boto:
    raise SystemExit(
        "The AWS boto3 library is required to run Falcon Data Replicator.\nPlease execute 'pip3 install boto3'"
    ) from no_boto
import stream as event_stream
import credvault
import logger


def shutdown():
    """Inform the user of shutdown."""
    status.status_write("Process terminated")
    raise SystemExit("Process terminated")


def start_streaming(streams, cid):
    """Start streaming detections."""
    # Loop thru each stream in our list
    for active_stream in streams:
        # Connect to the stream
        with event_stream.Stream(active_stream, falcon, queue, config, cid) as active:
            start = False
            try:
                if active.partition in str(config["partition"]).split(","):
                    start = True
                if str(config["partition"]).lower() == "all":
                    start = True
            except KeyError:
                # Start all available streams if partition is not specified
                start = True
            if start:
                status.status_write(f"Starting listener on partition number {str(active.partition)}...")
                # Create a thread to handle stream processing, daemonize so the thread shuts down when we do
                stream_thread = threading.Thread(target=active.process, daemon=True)
                # Begin processing the stream's contents
                stream_thread.start()

    return True


def load_config(config_file: str = "config.json"):
    """Load our configuration parameters."""
    cfg = False
    try:
        with open(config_file, 'r', encoding="utf-8") as file_config:
            cfg = json.loads(file_config.read())
        status.status_write("Configuration parameters loaded from local file")
    except FileNotFoundError:
        status.status_write("Specified configuration file not found")

    return cfg


# Force clean exit handling
atexit.register(shutdown)
# Define our process logfile
status = logger.Logger("fig-service.log", "service")

# Load configuration parameters
if platform.system().lower() in "windows,darwin".split(","):
    # We're running locally, read in the config from the local config file
    config = load_config()
    if not config:
        status.status_write("Unable to load configuration parameters")
        raise SystemExit("Unable to load configuration parameters")
else:
    config = load_config()
    if not config:
        # That didn't work
        try:
            # Try to get our creds from ssm
            config = json.loads(credvault.CredVault(status).get())
            status.status_write("Configuration parameters loaded from SSM Parameter Store.")

        except Exception as err:
            # Total failure
            status.status_write("Unable to load configuration parameters.")
            raise SystemExit("Unable to load configuration parameters.") from err

# MAIN ROUTINE
try:
    # Check to see if they've specified a different API base url
    BASE_URL = config["api_base_url"]
    if BASE_URL == "":
        BASE_URL = "us1"
except KeyError:
    # Any failure assume we're doing commercial / US-1
    BASE_URL = "us1"

try:
    VERIFY_SSL_CONNECTIONS = config["ssl_verify"]
    if VERIFY_SSL_CONNECTIONS == "":
        VERIFY_SSL_CONNECTIONS = True
except KeyError:
    VERIFY_SSL_CONNECTIONS = True
    config["ssl_verify"] = VERIFY_SSL_CONNECTIONS

# Grab the version detail
try:
    with open("VERSION", "r", encoding="utf-8") as ver_file:
        vers = ver_file.read().strip()
except OSError:
    vers = "2.0.x"

# Connect to the API
falcon = APIHarness(client_id=config["falcon_client_id"],
                    client_secret=config["falcon_client_secret"],
                    base_url=BASE_URL,
                    ssl_verify=VERIFY_SSL_CONNECTIONS,
                    user_agent=f"crowdstrike-securityhub/{vers}"
                    )
# Authenticate to the API
falcon.authenticate()
# Cry about our bad keys
if not falcon.authenticated:
    status.status_write(f"Failed to connect to the API on {BASE_URL}. Check base_url and ssl_verify configuration settings.")
    raise SystemExit(f"Failed to connect to the API on {BASE_URL}.  Check base_url and ssl_verify configuration settings.")

# Retrieve our current CID (MSSP functionality) or add it to config?
# This method requires Sensor Install API, our fallback option uses the Hosts API but a device must exist
try:
    current_cid = falcon.command("GetSensorInstallersCCIDByQuery")["body"]["resources"][0][:-3]
except KeyError:
    try:
        current_cid = falcon.command("GetDeviceDetails",
                                     ids=falcon.command("QueryDevicesByFilter", limit=1)["body"]["resources"][0]
                                     )["body"]["resources"][0]["cid"]
    except IndexError:
        try:
            current_cid = config["falcon_cid"]
        except KeyError as no_cid:
            status.status_write("Unable to retrieve CID")
            raise SystemExit("Unable to retrieve CID") from no_cid
# Default to confirming this is an AWS alert
if "confirm_provider" not in config:
    config["confirm_provider"] = True
# Ask for a list of available streams
new_streams = falcon.command(action="listAvailableStreamsOAuth2", appId=config["app_id"])
if "resources" in new_streams["body"]:
    if new_streams["body"]["resources"]:
        # Retrieve the SQS queue we'll use for notifications
        try:
            queue = boto3.resource('sqs', region_name=config["region"]).get_queue_by_name(QueueName=config["sqs_queue_name"])
        except ClientError:
            status.status_write("Unable to retrieve specified SQS queue")
        except EndpointConnectionError:
            status.status_write("Invalid region specified")
        else:
            start_streaming(new_streams["body"]["resources"], current_cid)
            # Only sleep if we have threads opened
            while threading.active_count() > 0:
                status.status_write("All threads started, main process sleeping.")
                # Force a wake up / restart of all streams
                time.sleep(21600)
                status.status_write("Restarting service and refreshing all streams.")
                # Discard all objects and restart the main service thread
                os.execv(sys.executable, [os.path.abspath(sys.argv[0]), "main.py"])
    else:
        status.status_write("No streams available")

else:
    status.status_write("No streams available")
