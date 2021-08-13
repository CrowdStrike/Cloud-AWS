import base64
import logging
import os
import yaml
from falconpy.sensor_download import Sensor_Download
import json
import docker
import re
import sys
import boto3
from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes import utils as k8s_utils

# Setup logging
logging.basicConfig(stream=sys.stdout, format='%(levelname)-8s%(message)s')
log = logging.getLogger('lumos_sensor_tasks')
logging.getLogger().setLevel(logging.INFO)


# Set the base_url variable to match the Falcon platform API
# Change this variable to meet your needs


# Set the repo name to be used for ECR
os_name = "Container"
falcon_repo = 'falcon-container-sensor'
download_path = "/tmp"
output_file = download_path + "/" + falcon_repo + ".yaml"


# Verify docker is running
try:
    docker_client = docker.from_env()
    docker_client.containers.list()
except docker.errors.DockerException:
    log.error("DockerError: Please ensure Docker is running")
    exit()

# Load objects for boto3.ECR
ecr_client = client = boto3.client('ecr')

# Get credentials for falconpy SDK
config_file = os.path.expanduser("~/config.json")
if os.path.exists(config_file) == False:
    log.error("ConfigFileError: Please verify ~/config.json exists")
    exit()

with open(config_file, 'r') as file_config:
    config = json.loads(file_config.read())

try:
    falcon_cid = config["falcon_cid"]
except KeyError:
    log.error("Set the falcon_cid key-value in the config.json")
    exit()

try:
    base_url = config["api_base_url"]
except KeyError:
    log.error("Set the api_base_url key-value in the config.json")
    exit()

# Instantiate object for ServiceClass
falcon = Sensor_Download(creds={
    "client_id": config["falcon_client_id"],
    "client_secret": config["falcon_client_secret"]
},
    base_url=base_url
)


def download_latest_sensor(os_name: str, download_path: str):
    "Download the latest container sensor and extract info"
    result = falcon.GetCombinedSensorInstallersByQuery(
        parameters={
            "filter": "os:'" + os_name + "'"
        }
    )

    if result["status_code"] != 200:
        log.error("Error accessing GetCombinedSensorInstallersByQuery : " +
                  str(result['status_code']))
        exit()

    # Retrieve result and exit if empty keys
    try:
        file_name = result['body']['resources'][0]['name']
        latest_sha = result['body']['resources'][0]['sha256']
    except KeyError as err:
        log.error("Error retrieving data:", err)
        exit()

    # Download falcon-container-sensor
    if os.path.exists(download_path + "/" + file_name) == False:
        falcon.DownloadSensorInstallerById(
            parameters={
                "id": latest_sha,
            },
            download_path=download_path,
            file_name=file_name
        )
        log.info("Downloaded Falcon Sensor: '%s'" % (file_name))
    return file_name


def import_container_sensor(download_path: str, file_name: str, repo_uri: str):
    "Import the sensor into the local repo from archive"
    # Extract version info for tag
    with open(download_path + "/" + file_name, 'rb') as f:
        local_image = docker_client.images.load(f)
    image_name = local_image[0].tags[0]
    import_tag = image_name.split(":")[1]
    tag_pattern = '(\d+\.){2}\d+-\d+'
    tag = re.search(tag_pattern, import_tag).group()
    resp = local_image[0].tag(repository=repo_uri, tag=tag)
    if resp:
        log.info("Successfully tagged image " + image_name)
    else:
        log.error("Error tagging image")
        exit()
    return image_name, tag


def create_ecr(falcon_repo: str):
    "Create ECR repo if it is not present"
    repos = ecr_client.describe_repositories()
    repo_names = [r['repositoryName'] for r in repos['repositories']]

    if falcon_repo not in repo_names:
        log.info("creating repo " + falcon_repo)
        response = ecr_client.create_repository(
            repositoryName=falcon_repo,
            imageTagMutability='MUTABLE',
            imageScanningConfiguration={
                'scanOnPush': False
            }
        )
        ecr_repo_uri = response['repository']['repositoryUri']
        log.info("Created repository: '%s'", ecr_repo_uri)
    else:
        ecr_repo_uri = repos['repositories'][0]['repositoryUri']
        log.info("Repository exists, using: '%s'", ecr_repo_uri)
    return ecr_repo_uri


def push_image_ecr(ecr_repo_uri: str, tag: str):
    "Push local image to ECR repo"
    token_reponse = ecr_client.get_authorization_token()
    token = token_reponse['authorizationData'][0]['authorizationToken']
    token = base64.b64decode(token).decode()
    username, password = token.split(':')
    auth_config = {'username': username, 'password': password}
    response = docker_client.images.push(
        repository=ecr_repo_uri,
        tag=tag,
        auth_config=auth_config
    )
    return response


def generate_manifest(image_name: str, falcon_cid: str, output_file: str):
    "Generate and save manifest for falcon-container injector deployment"
    log.info("Generating manifest from: '%s'" % (image_name))
    resp = docker_client.containers.run(
        image_name, "--image=" + image_name + " -cid=" + falcon_cid + " -pullpolicy=Always")
    manifest = yaml.safe_dump_all(yaml.safe_load_all(resp))
    log.info("Writing manifest file to '%s'" % (output_file))
    f = open(output_file, "w")
    f.write(manifest)
    return manifest


def deploy_manifest(yaml_file):
    "Deploy the injector manifest"
    k8s_config.load_kube_config()
    k8s = k8s_client.ApiClient()
    resp = k8s_utils.create_from_yaml(k8s, yaml_file)
    log.info(resp)


def main():

    # Download sensor and extract useful data
    file_name = download_latest_sensor(os_name=os_name,
                                       download_path=download_path
                                       )

    # Create ECR if necessary and return Uri
    ecr_repo_uri = create_ecr(falcon_repo=falcon_repo)

    # Import sensor from arhive into local repo
    import_result = import_container_sensor(download_path=download_path,
                                            file_name=file_name,
                                            repo_uri=ecr_repo_uri)

    tag = import_result[1]
    image_name = ecr_repo_uri + ":" + tag

    # Push sensor image to ECR and log response
    push_response = push_image_ecr(ecr_repo_uri=ecr_repo_uri,
                                   tag=tag)
    log.info(push_response)

    manifest = generate_manifest(image_name=image_name,
                                 falcon_cid=falcon_cid,
                                 output_file=output_file)

    deploy_manifest(output_file)


if __name__ == '__main__':
    main()
