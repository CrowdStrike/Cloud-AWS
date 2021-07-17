# import os
import boto3
import urllib
import json


class CredVault():

    def __init__(self, logger):
        region_lookup = "http://169.254.169.254/latest/meta-data/placement/availability-zone"
        self.region = urllib.request.urlopen(region_lookup).read().decode()[:-1]
        self.logger = logger

    def _getParameter(self, param_name):
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
            self.logger.statusWrite("{} SSM parameter not found".format(str(invalid)))
            not_found = True
        if not_found:
            credentials = ""
        else:
            credentials = response['Parameters'][0]['Value']
            self.logger.statusWrite("{} parameter loaded successfully.".format(str(param_name)))

        return credentials

    def get(self):
        # API Client ID
        try:
            self.falcon_client_id = self._getParameter("FIG_FALCON_CLIENT_ID")
        except Exception:
            pass
        # API Client Secret
        try:
            self.falcon_client_secret = self._getParameter("FIG_FALCON_CLIENT_SECRET")
        except Exception:
            pass
        # Application Identifier - Used for Event Streams
        try:
            self.app_id = self._getParameter("FIG_APP_ID")
        except Exception:
            pass
        # Severity Threshold - Only alert on detections at or greater
        try:
            self.severity_threshold = int(self._getParameter("FIG_SEVERITY_THRESHOLD"))
        except Exception:
            pass
        # AWS SQS queue to publish to
        try:
            self.sqs_queue_name = self._getParameter("FIG_SQS_QUEUE_NAME")
        except Exception:
            pass
        # CrowdStrike base URL (Defaults to US-1)
        try:
            self.api_base_url = self._getParameter("FIG_API_BASE_URL")
        except Exception:
            pass
        # Should we only alert on detections in AWS? - Defaults to True
        self.confirm_provider = True
        try:
            self.confirm_provider = self._getParameter("FIG_CONFIRM_PROVIDER")
        except Exception:
            pass

        del self.logger
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)
