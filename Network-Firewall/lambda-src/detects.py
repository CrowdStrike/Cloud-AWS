import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Detects:
    """Feed Hosts Class a good access_token and fire away"""

    def __init__(self, access_token):
        self.headers = {
            'Authorization': 'Bearer ' + access_token
        }
        self.base_url = 'https://api.crowdstrike.com'
        self.return_var = {'status_code': '', 'headers': '', 'body': ''}

    def GetAggregateDetects(self, body):
        # POST
        # Get detect aggregates as specified via json in request body.
        # https://assets.falcon.crowdstrike.com/support/api/swagger.html#/detects/GetAggregateDetects
        FULL_URL = self.base_url + '/detects/aggregates/detects/GET/v1'
        HEADERS = self.headers
        BODY = body
        return_var = self.return_var
        try:
            result = requests.request("POST", FULL_URL, json=BODY, headers=HEADERS, verify=False)
            return_var['status_code'] = result.status_code
            return_var['headers'] = dict(result.headers)
            return_var['body'] = result.json()
            return return_var
        except Exception as e:
            return_var['status_code'] = 500
            return_var['headers'] = {}
            return_var['body'] = str(e)
            return return_var

    def UpdateDetectsByIdsV2(self, body):
        # PATCH
        # Modify the state, assignee, and visibility of detections
        # https://assets.falcon.crowdstrike.com/support/api/swagger.html#/detects/UpdateDetectsByIdsV2
        FULL_URL = self.base_url + '/detects/entities/detects/v2'
        HEADERS = self.headers
        BODY = body
        return_var = self.return_var
        try:
            result = requests.request("PATCH", FULL_URL, json=BODY, headers=HEADERS, verify=False)
            return_var['status_code'] = result.status_code
            return_var['headers'] = dict(result.headers)
            return_var['body'] = result.json()
            return return_var
        except Exception as e:
            return_var['status_code'] = 500
            return_var['headers'] = {}
            return_var['body'] = str(e)
            return return_var

    def GetDetectSummaries(self, body):
        # POST
        # View information about detections
        # https://assets.falcon.crowdstrike.com/support/api/swagger.html#/detects/GetDetectSummaries

        FULL_URL = self.base_url + '/detects/entities/summaries/GET/v1'
        HEADERS = self.headers
        BODY = body
        return_var = self.return_var
        try:
            result = requests.request("POST", FULL_URL, json=BODY, headers=HEADERS, verify=False)
            return_var['status_code'] = result.status_code
            return_var['headers'] = dict(result.headers)
            return_var['body'] = result.json()
            return return_var
        except Exception as e:
            return_var['status_code'] = 500
            return_var['headers'] = {}
            return_var['body'] = str(e)
            return return_var

    def QueryDetects(self, parameters):
        # GET
        # Search for detection IDs that match a given query
        # https://assets.falcon.crowdstrike.com/support/api/swagger.html#/detects/QueryDetects
        FULL_URL = self.base_url + '/detects/queries/detects/v1'
        HEADERS = self.headers
        PARAMS = parameters
        return_var = self.return_var
        try:
            result = requests.request("GET", FULL_URL, params=PARAMS, headers=HEADERS, verify=False)
            return_var['status_code'] = result.status_code
            return_var['headers'] = dict(result.headers)
            return_var['body'] = result.json()
            return return_var
        except Exception as e:
            return_var['status_code'] = 500
            return_var['headers'] = {}
            return_var['body'] = str(e)
            return return_var
