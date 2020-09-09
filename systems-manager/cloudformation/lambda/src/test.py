import requests


def check_for_install_token(credentials) -> bool:
    url = "https://api.crowdstrike.com/installation-tokens/queries/tokens/v1?filter=status:'valid'"
    auth_token = get_auth_token(credentials['CS_API_GATEWAY_CLIENT_ID'], credentials['CS_API_GATEWAY_CLIENT_SECRET'])
    if auth_token:
        auth_header = get_auth_header(auth_token)
    else:
        print("Failed to auth token")
        sys.exit(1)
    headers = {
        'Content-Type': 'application/json',
    }
    headers.update(auth_header)

    try:
        response = requests.request('GET', url, headers=headers)
        response_content = json.loads(response.text)
        logger.info('Response to register = {}'.format(response_content))
        good_exit = 200
        if response.status_code == good_exit:
            # Tokens are listed in response[]
            if len(response.resources) > 0:
                return True
            else:
                return False
    except Exception as e:
        logger.info('Got exception {}'.format(e))
        return False


if __name__ == '__main__':
