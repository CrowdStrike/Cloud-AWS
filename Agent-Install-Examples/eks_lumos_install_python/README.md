# Falcon Container Install Script (Existing cluster)

NOTE: This script will use the defaults of your currently configured `aws cli` including region

NOTE: Be sure to set the `base_url` variable in the `lumos_sensor_install.py` script to meet your needs

NOTE: The API `base_url` info can be found when creating the API credentials in Falcon
## Requirements

* Falcon API credentials with Sensor Download permissions
* Python packages listed in requirements.txt
* Existing EKS cluster
* Existing ECR registry
* Authenticated AWS CLI with permissions to create ECR repositories and push
* Docker needs to be running on the local machine where the script is ran
* Kubectl installed and authenticated to the target cluster for deployment
* This was ran and tested on MacOS but should work on any bash based shell
* Create a file with the name `config.json` located in your home directory i.e `~/config.json`

Example of the `config.json` file

NOTE: The`base_url` will be provided when creating the API keys.

```
{
        "falcon_client_id": "8972331hiusgdaugd987987231213",
        "falcon_client_secret": "cdHJKASDsdad7t8sdsajhkasdasd",
        "falcon_cid": "JHDSHJDHFS9879EHKSJDAHKJHFA-JH",
        "base_url": "https://api.us-2.crowdstrike.com"
}
```

## Usage

* Ensure requirements are met
* Clone the repository contents
* Run `pip3 install -r requirements.txt`
* Run `python3 lumos_sensor_install.py`
* Use `kubectl` to verify deployment and operations


## Known limitations

* Currently removal of the deployment will need to be done with the saved file in `/tmp`.
* This is early version. Please report or even fix issues.
