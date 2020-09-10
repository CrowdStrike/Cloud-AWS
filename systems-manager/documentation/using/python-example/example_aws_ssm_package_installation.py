#!/usr/bin/python

#######################################################################################################################
#######################################################################################################################
##
##  Usage Examples -
##      python3 test_aws_ssm_package_installation.py --package_version 5.31.0-9606 --package_name FalconSensor-Windows [--target_instances=[]]
##
#######################################################################################################################
#######################################################################################################################

import datetime
import getopt
import logging
import os
import sys
import time
from configparser import ConfigParser
from os.path import dirname

import boto3

LIB_DIR = os.path.join(dirname(__file__), '../lib')
sys.path.append(os.path.normpath(os.path.join(LIB_DIR)))

# Constants
RETRY_WAIT_COUNT = 60
RETRY_WAIT_SLEEP = 10
DOCUMENT_INSTALL_ACTION = 'Install'
DOCUMENT_UNINSTALL_ACTION = 'Uninstall'

# Logger
logger = logging.getLogger('example_aws_ssm_package_installation')
handler = logging.FileHandler('./example_aws_ssm_package_installation.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


###########################
# Logging helper Functions
###########################


def print_log_info(logger, message):
    """Prints to std out and logs to log file."""
    print('[INFO] ' + message)
    logger.info(message)


def print_log_error(logger, message, fatal):
    """Prints to std out and logs to log file."""

    print('[ERROR] ' + message)
    logger.error(message)
    if fatal:
        sys.exit(2)


def print_log_warn(logger, message):
    """Prints to std out and logs to log file."""

    print('[WARNING] ' + message)
    logger.warning(message)


def __start_automation_execution(client, document_name, document_version, parameters):
    return client.start_automation_execution(
        DocumentName=document_name,
        DocumentVersion=document_version,
        Parameters=parameters,
    )


def __get_automation_execution(client, id):
    return client.get_automation_execution(
        AutomationExecutionId=id
    )


def usage():
    print(
        'Usage: python example_aws_ssm_package_installation.py --package_version=<package_version>  --package_name=<package_name> --target_instances=[]'
    )
    print('  --package_name=<String>     [Required]  Sensor install version for which we are building the package')
    print('  --package_version=<String>  [Required]  Sensor type supported values are linux/windows ')
    print('  --target_instances=[]     [Required]  [CAUTION] instance ids to target ')
    sys.exit(2)


def build_automation_params(config, action, package_name, package_version, target):
    date_object = datetime.date.today()
    if package_name.__contains__("Linux"):
        install_params = "--tags=\"SSMAutomation,{}\"".format(date_object)
    else:
        install_params = "GROUPING_TAGS=\"SSMAutomation,{}\"".format(date_object)
    parameters = {
        "InstallerParams": [install_params],
        "Action": [action],
        "InstallationType": ["Uninstall and reinstall"],
        "PackageName": [package_name],
        "PackageVersion": [package_version],
        "APIGatewayHostKey": [config['apiGatewayHost']],
        "APIGatewayClientIDKey": [config['apiGatewayClientID']],
        "APIGatewayClientSecretKey": [config['apiGatewayClientSecretKey']],
        "AutomationAssumeRole": [config['automation_assume_role']],
    }
    if len(target) > 0:
        parameters['InstanceIds'] = target
    else:
        type = package_name.split('-')[1].lower()
        #
        # No instance ids specified so filter by tag.
        # Assume instances have a tag 'os-platform' with value 'linux' or 'windows'
        #
        parameters["Targets"] = ["{\"Key\": \"tag:os-platform\", \"Values\": [{}]}".format(type)]

    return parameters


def trigger_automation_execution(logger, ssm_client, package_name, package_version, automation_config, target_instances,
                                 action):
    start_time = time.time()
    document_name = automation_config['document_name']
    document_version = automation_config['document_version']

    logger.info(
        "Starting automation document {} version {} execution with {} action. Target pacakge {}, target version{}".format(
            document_name, document_version,
            action, package_name, package_version))

    install_automation_resp = __start_automation_execution(
        ssm_client,
        document_name,
        document_version,
        build_automation_params(automation_config, action, package_name, package_version, target_instances)
    )

    if install_automation_resp['ResponseMetadata']['HTTPStatusCode'] != 200:
        print_log_error(logger,
                        "Failed to start automation execution  for install action. HTTP response from SSM : {}".format(
                            install_automation_resp['ResponseMetadata']), True)

    install_execution_id = install_automation_resp['AutomationExecutionId']
    print_log_info(logger,
                   "Successfully started automation execution for install action with automation id: {}".format(
                       install_execution_id))

    status = ""
    install_status_resp = {}
    for i in range(RETRY_WAIT_COUNT):
        install_status_resp = ssm_client.get_automation_execution(AutomationExecutionId=install_execution_id)

        if install_status_resp['ResponseMetadata']['HTTPStatusCode'] != 200:
            print_log_error(logger,
                            "Failed to get automation execution info. HTTP response from SSM: {}".format(
                                install_status_resp['ResponseMetadata']), True)

        # ['Pending', 'InProgress', 'Waiting', 'Success', 'TimedOut', 'Cancelling', 'Cancelled', 'Failed']:
        status = install_status_resp['AutomationExecution']['AutomationExecutionStatus']
        if status in ['Pending', 'InProgress', 'Waiting']:
            print_log_info(logger,
                           "... Automation execution shows status '{}', will check status again after {}s. Attempt {}/{}".format(
                               status, RETRY_WAIT_SLEEP, i + 1, RETRY_WAIT_COUNT))
            time.sleep(RETRY_WAIT_SLEEP)
        else:
            break

        if i == RETRY_WAIT_COUNT:
            print_log_error(logger,
                            "Execution Timed Out. Status {} Response {}".format(status,
                                                                                install_status_resp),
                            True)

    for eachStep in install_status_resp['AutomationExecution']['StepExecutions']:
        if eachStep['StepStatus'] in ['TimedOut', 'Cancelling', 'Cancelled', 'Failed']:
            print_log_error(logger,
                            "Automation execution exited with status '{}' for step '{}'. Failure message: {}".format(
                                eachStep['StepStatus'], eachStep['StepName'],
                                eachStep['FailureMessage']), True)

    print_log_info(logger,
                   "Successfully finished automation for {} action. Took {}m".format(action, (
                           time.time() - start_time) / 60))


def main():
    start_time = time.time()
    # Loading command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "",
                                   ["package_name=", "package_version=",
                                    "target_instances="])

    except getopt.GetoptError as err:
        print_log_error(logger, "Failed read command line arguments : {}".format(err), False)
        usage()

    package_name = ""
    package_version = ""
    target_instances = []
    for opt, arg in opts:
        if opt == '--package_name':
            package_name = arg
        if opt == '--package_version':
            package_version = arg
        if opt == '--target_instances':
            target_instances = arg.split(",")

    # Validating input params
    if len(package_name) == 0 \
            or len(package_version) == 0:
        print_log_error(logger, "Command line arguments failed validation.", False)
        usage()

    print_log_info(logger,
                   "Starting automation automation test for package {} version{}".format(
                       package_name, package_version))
    # Loading config.ini file
    config_object = ConfigParser()
    config_object.read('config.ini')
    automation_config = config_object['AUTOMATION']
    print("Successfully loaded config from {}".format('config.ini'))

    # Setting AWS client
    session = boto3.Session()
    print_log_info(logger, "Successfully established AWS session")

    execution_region = automation_config['aws_region']

    ssm_client = session.client('ssm', region_name=execution_region)

    # install action
    trigger_automation_execution(logger, ssm_client, package_name, package_version, automation_config,
                                 target_instances, DOCUMENT_INSTALL_ACTION)
    print(logger, "Sleeping for 60 seconds ... ")
    time.sleep(60)


if __name__ == "__main__":
    main()
