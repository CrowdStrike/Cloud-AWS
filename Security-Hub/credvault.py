"""Credential / configuration lookup handler."""
import urllib
import json
import requests
import boto3


class CredVault():  # pylint: disable=R0902
    """Class to handle configuration lookups."""

    def __init__(self, logger):
        """Init the object and base parameters."""
        self.logger = logger
        self.region = self._get_region()
        self.falcon_client_id = None
        self.falcon_client_secret = None
        self.app_id = None
        self.sqs_queue_name = None
        self.api_base_url = None
        self.severity_threshold = None
        self.confirm_provider = None
        self.ssl_verify = None

    # We need to get the region depending on the version of IMDS
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html

    def _get_region(self):
        """
        Retrieve the region from IMDS.
        This function will check the version of IMDS and retrieve the region.
        """
        # Define the URLs and headers
        token_url = "http://169.254.169.254/latest/api/token"
        token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        region_url = "http://169.254.169.254/latest/meta-data/placement/availability-zone"

        # Attempting a GET request for IMDSv1
        try:
            with urllib.request.urlopen(region_url, timeout=5) as region_check:
                region = region_check.read().decode()[:-1]
                return region
        except urllib.error.HTTPError:
            self.logger.status_write("Failed to retrieve region with IMDSv1. Attempting IMDSv2.")

        # Try IMDSv2
        try:
            token_response = requests.put(token_url, headers=token_headers, timeout=5)
            token_response.raise_for_status()  # Raise an exception for HTTP errors
            token = token_response.text
            # Using the token to access the region information
            region_response = requests.get(
                region_url,
                headers={"X-aws-ec2-metadata-token": token},
                timeout=5
            )
            region_response.raise_for_status()  # Raise an exception for HTTP errors
            region = region_response.text[:-1]
            return region
        except requests.exceptions.RequestException as e:
            self.logger.status_write("Failed to retrieve region with IMDSv2. Exiting.")
            raise SystemExit(e) from e

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
