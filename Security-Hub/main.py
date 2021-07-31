"""
CrowdStrike / Security Hub integration

Original version: Dixon Styres
Modification: 11.15.20 - jshcodes@CrowdStrike, SQS integration
Modification: 07.15.20 - jshcodes@CrowdStrike, MSSP functionality

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
import boto3
import threading
import stream as event_stream
import credvault
import logger
import atexit
from falconpy import api_complete as FalconSDK
from botocore.exceptions import ClientError, EndpointConnectionError


def shutdown():
    status.statusWrite("Process terminated")
    raise SystemExit("Process terminated")


def startStreaming(new_streams, cid):
    # Loop thru each stream in our list
    for active_stream in new_streams:
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
                status.statusWrite("Starting listener on partition number {}...".format(str(active.partition)))
                # Create a thread to handle stream processing, daemonize so the thread shuts down when we do
                t = threading.Thread(target=active.process, daemon=True)
                # Begin processing the stream's contents
                t.start()

    return True


def loadConfig(config_file: str = "config.json"):
    cfg = False
    try:
        with open(config_file, 'r') as file_config:
            cfg = json.loads(file_config.read())
        status.statusWrite("Configuration parameters loaded from local file")
    except FileNotFoundError:
        status.statusWrite("Specified configuration file not found")

    return cfg


# Force clean exit handling
atexit.register(shutdown)
# Define our process logfile
status = logger.Logger("fig-service.log", "service")

# Load configuration parameters
if platform.system().lower() in "windows,darwin".split(","):
    # We're running locally, read in the config from the local config file
    config = loadConfig()
    if not config:
        status.statusWrite("Unable to load configuration parameters")
        raise SystemExit("Unable to load configuration parameters")
else:
    config = loadConfig()
    if not config:
        # That didn't work
        try:
            # Try to get our creds from ssm
            config = json.loads(credvault.CredVault(status).get())
            status.statusWrite("Configuration parameters loaded from SSM Parameter Store.")

        except Exception as err:
            # Total failure
            status.statusWrite("Unable to load configuration parameters: %s" % err)
            raise SystemExit("Unable to load configuration parameters: %s" % err)

# MAIN ROUTINE
try:
    # Check to see if they've specified a different API base url
    baseURL = config["api_base_url"]
    if baseURL == "":
        baseURL = "https://api.crowdstrike.com"
except KeyError:
    # Any failure assume we're doing commercial
    baseURL = "https://api.crowdstrike.com"

try:
    verify_ssl_connections = config["ssl_verify"]
    if verify_ssl_connections == "":
        verify_ssl_connections = True
except KeyError:
    verify_ssl_connections = True
    config["ssl_verify"] = verify_ssl_connections

# Connect to the API
falcon = FalconSDK.APIHarness(creds={'client_id': config["falcon_client_id"],
                                     'client_secret': config["falcon_client_secret"]
                                     }, base_url=baseURL, ssl_verify=verify_ssl_connections)
# Authenticate to the API
falcon.authenticate()
# Cry about our bad keys
if not falcon.authenticated:
    status.statusWrite(f"Failed to connect to the API on {baseURL}. Check base_url and ssl_verify configuration settings.")
    raise SystemExit(f"Failed to connect to the API on {baseURL}.  Check base_url and ssl_verify configuration settings.")
else:
    # Retrieve our current CID (MSSP functionality) or add it to config?
    # This method requires Sensor Install API, our fallback option uses the Hosts API but a device must exist
    try:
        current_cid = falcon.command("GetSensorInstallersCCIDByQuery")["body"]["resources"][0][:-3]
    except KeyError:
        try:
            current_cid = falcon.command("GetDeviceDetails",
                                         ids=falcon.command("QueryDevicesByFilter")["body"]["resources"][0]
                                         )["body"]["resources"][0]["cid"]
        except IndexError:
            try:
                current_cid = config["falcon_cid"]
            except KeyError:
                status.statusWrite("Unable to retrieve CID")
                raise SystemExit("Unable to retrieve CID")
    # Default to confirming this is an AWS alert
    if "confirm_provider" not in config:
        config["confirm_provider"] = True
    # Ask for a list of available streams
    new_streams = falcon.command(action="listAvailableStreamsOAuth2", parameters={"appId": "{}".format(config["app_id"])})
    if "resources" in new_streams["body"]:
        # Retrieve the SQS queue we'll use for notifications
        try:
            queue = boto3.resource('sqs', region_name=config["region"]).get_queue_by_name(QueueName=config["sqs_queue_name"])
        except ClientError:
            status.statusWrite("Unable to retrieve specified SQS queue")
        except EndpointConnectionError:
            status.statusWrite("Invalid region specified")
        else:
            startStreaming(new_streams["body"]["resources"], current_cid)
            # Only sleep if we have threads opened
            while threading.active_count() > 0:
                status.statusWrite("All threads started, main process sleeping.")
                # Force a wake up / restart of all streams
                time.sleep(21600)
                status.statusWrite("Restarting service and refreshing all streams.")
                # Discard all objects and restart the main service thread
                os.execv(sys.executable, [os.path.abspath(sys.argv[0]), "main.py"])

    else:
        status.statusWrite("No streams available")
