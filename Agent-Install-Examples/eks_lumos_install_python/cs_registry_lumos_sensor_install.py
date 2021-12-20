"""
Install the CrowdStrike Falcon Container sensor via the registry

- mccbryan3, jhseceng, jshcodes@CrowdStrike
"""
import base64
import logging
import os
import sys
import json
import yaml
import docker
import boto3
from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes import utils as k8s_utils
try:
    from falconpy.sensor_download import Sensor_Download
    from falconpy.falcon_container import FalconContainer
    from falconpy.oauth2 import OAuth2
except ImportError as no_falconpy:
    raise SystemExit(
        "CrowdStrike FalconPy must be installed in order to use this application.\n"
        "Please execute `python3 -m pip install crowdstrike-falconpy` and try again."
    ) from no_falconpy


def graceful_failure(err_msg: str, no_log: bool = False):
    """
    Logs any error messages and gracefully exits the routine
    """
    if not no_log:
        log.error(err_msg)
    raise SystemExit(err_msg)


def get_latest_sensor(package_os_name: str):
    """
    Download the latest container sensor and extract info
    """
    result = falcon.GetCombinedSensorInstallersByQuery(
        parameters={
            "filter": "os:'" + package_os_name + "'"
        }
    )

    if result["status_code"] != 200:
        graceful_failure("Error accessing GetCombinedSensorInstallersByQuery : " +
                         str(result['status_code']))

    # Retrieve result and exit if empty keys
    try:
        file_name = result['body']['resources'][0]['name']

    except KeyError as err:
        graceful_failure("Error retrieving data:", err)

    return file_name


def docker_login(username, password):
    """
    Logs into the docker registry
    """
    try:
        res = docker_client.login(username=username, password=password,
                                  registry='https://registry.crowdstrike.com')
        success = bool(res['Status'] == 'Login Succeeded')

    except Exception as err:
        graceful_failure(f'Error {err}', no_log=True)

    return success


def get_image_pull_token():
    """
    Retrieves the image pull token
    """
    docker_config_file_path = os.path.expanduser('~') + '/.docker/config.json'
    try:
        with open(docker_config_file_path, "r") as file:
            contents = file.read()
            config_file_bytes = contents.encode('ascii')
    except IOError:
        log.info('Unable to open docker config file %s', docker_config_file_path)
    base64_bytes = base64.b64encode(config_file_bytes)
    # Use dedicated config file
    # base64_bytes = base64.b64encode(json.dumps(auth_config).encode('utf-8'))
    token = base64_bytes.decode('ascii')

    return token


def generate_manifest(image_name: str, cid: str, output_file: str):
    """
    Generate and save manifest for falcon-container injector deployment
    """
    log.info("Generating manifest from: '%s'", image_name)
    image_pull_token = get_image_pull_token()

    try:
        resp = docker_client.containers.run(image_name,
                                            "-image=" + image_name + " -pulltoken=" + image_pull_token
                                            + " -namespaces=" + NAMESPACES + " -cid=" + cid)
        manifest = yaml.safe_dump_all(yaml.safe_load_all(resp))
        log.info("Writing manifest file to '%s'", output_file)
        with open(output_file, "w+") as file_handle:
            file_handle.write(manifest)

    except Exception as err:
        log.info("Exception %s", err)

    return manifest


def deploy_manifest(yaml_file):
    "Deploy the injector manifest"
    k8s_config.load_kube_config()
    k8s = k8s_client.ApiClient()
    try:
        resp = k8s_utils.create_from_yaml(k8s, yaml_file)
        log.info(resp)
    except Exception as err:
        graceful_failure('Error {} deploying manifest'.format(err))


def main():
    """
    Main routine
    """
    username1 = 'fc-' + str(config['falcon_cid'].split('-')[0]).lower()
    pwd = falcon_container.get_credentials()['body']['resources'][0]['token']
    docker_login(username1, pwd)
    auth_config['auths']['registry.crowdstrike.com'].update(username=username1)
    auth_config['auths']['registry.crowdstrike.com'].update(password=pwd)
    # Download sensor and extract useful data
    file_name = get_latest_sensor(OS_NAME)
    sensor_tag = str(file_name).split('.container', maxsplit=1)[0].replace('falcon-sensor-', 'falcon-sensor:')
    cc_up = str(CS_CLOUD).upper()
    image_name = f'registry.crowdstrike.com/falcon-container/{CS_CLOUD}/release/{sensor_tag}.container.x86_64.Release.{cc_up}'
    generate_manifest(image_name=image_name,
                      cid=falcon_cid.lower(),
                      output_file=OUTPUT_FILE)

    deploy_manifest(OUTPUT_FILE)


# Setup logging
logging.basicConfig(stream=sys.stdout, format='%(levelname)-8s%(message)s')
log = logging.getLogger('lumos_sensor_tasks')
logging.getLogger().setLevel(logging.INFO)

NAMESPACES = "default,busybox"
OS_NAME = "Container"
# FALCON_REPO = 'falcon-container-sensor'
# download_path = "cs_registry_install"
# output_file = FALCON_REPO + ".yaml"
OUTPUT_FILE = "falcon-container-sensor.yaml"
auth_config = {
    "auths": {
        "registry.crowdstrike.com": {
        }
    }
}
# Verify docker is running
try:
    docker_client = docker.from_env()
    docker_client.containers.list()
except docker.errors.DockerException:
    graceful_failure("DockerError: Please ensure Docker is running")


# Load objects for boto3.ECR
ecr_client = client = boto3.client('ecr')

# Get credentials for falconpy SDK
config_file = os.path.expanduser("./config.json")
if not os.path.exists(config_file):
    graceful_failure("ConfigFileError: Please verify ~/config.json exists", no_log=True)

with open(config_file, 'r') as file_config:
    config = json.loads(file_config.read())

try:
    falcon_cid = config["falcon_cid"]
except KeyError:
    graceful_failure("Set the falcon_cid key-value in the config.json")

# Set the base_url variable to match the Falcon platform API
# Change this variable to meet your needs
falcon_cloud = config['falcon_cloud'].lower()
if falcon_cloud == 'us-1':
    BASE_URL = "https://api.crowdstrike.com"
    CS_CLOUD = "us1"
elif falcon_cloud == 'us-2':
    BASE_URL = "https://api.us-2.crowdstrike.com"
    CS_CLOUD = "us2"
elif falcon_cloud == 'eu-1':
    BASE_URL = "https://api.eu-1.crowdstrike.com"
    CS_CLOUD = "eu1"
else:
    graceful_failure("config falcon_cloud not recognised Values are us-1, us-2 or eu-1")

auth = OAuth2(client_id=config["falcon_client_id"],
              client_secret=config["falcon_client_secret"],
              base_url=BASE_URL
              )

# Instantiate object for ServiceClass
falcon = Sensor_Download(auth_object=auth)

falcon_container = FalconContainer(auth_object=auth)

if __name__ == '__main__':
    main()
