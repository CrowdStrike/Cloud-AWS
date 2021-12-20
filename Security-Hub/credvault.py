"""Credential / configuration lookup handler."""
import urllib
import json
import boto3


class CredVault():  # pylint: disable=R0902
    """Class to handle configuration lookups."""

    def __init__(self, logger):
        """Init the object and base parameters."""
        region_lookup = "http://169.254.169.254/latest/meta-data/placement/availability-zone"
        with urllib.request.urlopen(region_lookup) as region_check:
            self.region = region_check.read().decode()[:-1]
        self.logger = logger
        self.falcon_client_id = None
        self.falcon_client_secret = None
        self.app_id = None
        self.sqs_queue_name = None
        self.api_base_url = None
        self.severity_threshold = None
        self.confirm_provider = None
        self.ssl_verify = None

    def get_parameter(self, param_name):
        """
        This function reads a secure parameter from AWS' SSM service.
        The request must be passed a valid parameter name, as well as
        temporary credentials which can be used to access the parameter.
        The parameter's value is returned.
        """
        # Create the SSM Client
        ssm = boto3.client('ssm',
                           region_name=self.region
                           )

        # Get the requested parameter
        response = ssm.get_parameters(
            Names=[
                param_name,
            ],
            WithDecryption=True
        )
        # Store the credentials in a variable
        not_found = False
        for invalid in response['InvalidParameters']:
            self.logger.status_write(f"{str(invalid)} SSM parameter not found")
            not_found = True
        if not_found:
            credentials = ""
        else:
            credentials = response['Parameters'][0]['Value']
            self.logger.status_write(f"{str(param_name)} parameter loaded successfully.")

        return credentials

    def get(self):
        """Retrieve all configuration parameters."""
        # API Client ID
        self.falcon_client_id = self.get_parameter("FIG_FALCON_CLIENT_ID")
        # API Client Secret
        self.falcon_client_secret = self.get_parameter("FIG_FALCON_CLIENT_SECRET")
        # Application Identifier - Used for Event Streams
        self.app_id = self.get_parameter("FIG_APP_ID")
        # Severity Threshold - Only alert on detections at or greater
        self.severity_threshold = int(self.get_parameter("FIG_SEVERITY_THRESHOLD"))
        # AWS SQS queue to publish to
        self.sqs_queue_name = self.get_parameter("FIG_SQS_QUEUE_NAME")
        # CrowdStrike base URL (Defaults to US-1)
        self.api_base_url = self.get_parameter("FIG_API_BASE_URL")
        # Should we only alert on detections in AWS? - Defaults to True
        self.confirm_provider = self.get_parameter("FIG_CONFIRM_PROVIDER")
        if "f" in self.confirm_provider.lower():
            self.confirm_provider = False
        else:
            self.confirm_provider = True
        # Should we enable SSL Verification for Request calls? - Defaults to True
        self.ssl_verify = self.get_parameter("FIG_SSL_VERIFY")
        if "f" in self.ssl_verify.lower():
            self.ssl_verify = False
        else:
            self.ssl_verify = True
        del self.logger
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
