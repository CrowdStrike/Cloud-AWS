import logging
import os

import boto3


class CredVault():

    def __init__(self):
        self.region = os.environ['AWS_REGION']
        self.logger = logging.getLogger()
        self.logger.setLevel(level=logging.INFO)

    def _getParameter(self, param_name):
        """
        This function reads a secure parameter from AWS' SSM service.
        The request must be passed a valid parameter name, as well as
        temporary credentials which can be used to access the parameter.
        The parameter's value is returned.
        """
        # Create the SSM Client
        try:

            ssm = boto3.client('ssm', region_name=self.region)
            self.logger.debug('Got ssm Client {}'.format(ssm))
            # Get the requested parameter
            response = ssm.get_parameters(
                Names=[
                    param_name,
                ],
                WithDecryption=True
            )
            self.logger.debug('Got response to get params {}'.format(response))
        except Exception as e:
            self.logger.debug('Got exception to get params {}'.format(e))

        # Store the credentials in a variable
        credentials = response['Parameters'][0]['Value']
        return credentials

    def get(self):
        try:
            self.falcon_client_id = self._getParameter("FIG_FALCON_CLIENT_ID")
            self.falcon_client_secret = self._getParameter("FIG_FALCON_CLIENT_SECRET")
            self.logger.debug('self.falcon_client_id {}'.format(self.falcon_client_secret))
            result = {
                'falcon_client_id': self.falcon_client_id,
                'falcon_client_secret': self.falcon_client_secret
            }
            return result

        except Exception as e:
            self.logger.debug('Got exception to get params {}'.format(e))
            pass
