import json
import urllib

import boto3


class CredVault():

    def __init__(self):
        self.region = urllib.request.urlopen(
            'http://169.254.169.254/latest/meta-data/placement/availability-zone').read().decode()[:-1]

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
        credentials = response['Parameters'][0]['Value']
        return credentials

    def get(self):
        try:

            self.falcon_client_id = self._getParameter("AWS-NET-FW-DEMO-FALCONCLIENTID")
            self.falcon_client_secret = self._getParameter("AWS-NET-FW-DEMO-FALCONSECRET")
            return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

        except:
            pass
