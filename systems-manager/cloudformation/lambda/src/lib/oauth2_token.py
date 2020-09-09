__author__ = 'CrowdStrike'

import datetime
import json
import logging

import requests


# When using CrowdStrike OAuth2 APIs, we need to generate a Token using an API key. The Token will be valid
# for 30 minutes, after which we need to get a new Token.
class OAuth2Token:
    def __init__(self):
        self.token = None
        self.tokenCreationTime = datetime.datetime.utcnow() + datetime.timedelta(
            -1000)  # Just some date way into the past
        self.tokenValidSeconds = 29 * 60  # The number of seconds that a token is valid for
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def _get_new_token(self, client_id, client_secret, server, proxy):
        self.logger('Attempting to get OAuth2 token from CrowdStrike server...')
        url = server + '/oauth2/token'
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'client_id': client_id, 'client_secret': client_secret}
        newToken = None
        try:
            # Print all logs to check we are calling url correctly, should only be enabled in the deveopment mode
            # self.qpylib.log('url:' + url)
            # self.qpylib.log('payload:' + str(payload))
            # self.qpylib.log('proxy:' + str(proxy))
            # self.qpylib.log('headers:' + json.dumps(headers, indent=2))

            result = requests.post(url, data=payload, proxies=proxy, headers=headers)
            self.logger('Status code: {0}'.format(result.status_code))
            content = json.loads(result.content)
            newToken = content['access_token']
            self.tokenCreationTime = datetime.datetime.utcnow()
            self.tokenValidSeconds = content['expires_in']
            self.logger('Successfully received JWT token from {0} which expires in {1} seconds'.format(server,
                                                                                                       self.tokenValidSeconds))
        except Exception as e:
            raise Exception('Error when getting JWT token: ' + str(e))
        return newToken

    def get_token(self, server, client_id, client_secret, proxy):
        secondsSinceJwtCreation = self.timedelta_total_seconds(datetime.datetime.utcnow() - self.tokenCreationTime)
        if (self.token == None) or (secondsSinceJwtCreation > self.tokenValidSeconds):
            # Get a new JWT token
            if self.token == None:
                self.logger('OAuth2Token() class does not have a token. Getting a new one.')
            elif (secondsSinceJwtCreation > self.tokenValidSeconds):
                self.logger('JWT token has expired. Getting a new one.')
            self.token = self._get_new_token(client_id, client_secret, server, proxy)
            return self.token
        else:
            return self.token

    # Python 2.6 does not have the timedelta.total_seconds method :(
    def timedelta_total_seconds(self, td):
        return (
                       td.microseconds + 0.0 +
                       (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
