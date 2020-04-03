import requests, base64, json, os
from .authorization import Authorization
from .auth_method import AuthMethod
from pytify.core import BadRequestError

def get_auth_key(client_id, client_secret):
    byte_keys = bytes(f'{client_id}:{client_secret}', 'utf-8')
    encoded_key = base64.b64encode(byte_keys)
    return encoded_key.decode('utf-8')

def _client_credentials(config):
    auth_key = get_auth_key(config.client_id, config.client_secret)
    headers = {'Authorization': f'Basic {auth_key}'}

    options = {
        'grant_type': 'client_credentials',
        'json': 'true'
    }

    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers = headers,
        data    = options
    )

    content = json.loads(response.content.decode('utf-8'))

    if response.status_code == 400:
        error_description = content.get('error_description')
        raise BadRequestError(error_description)

    access_token = content.get('access_token', None)
    token_type   = content.get('token_type', None)
    expires_in   = content.get('expires_in', None)
    scope        = content.get('scope', None)

    return Authorization(access_token, token_type, expires_in, scope, None)

def authenticate(config):
    if config.auth_method == AuthMethod.CLIENT_CREDENTIALS:
        return _client_credentials(config)
    
    return _authorization_code(config)

def _refresh_access_token(auth_key, refresh_token):
    headers = {'Authorization': f'Basic {auth_key}'}

    options = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers = headers,
        data = options
    )

    content = json.loads(response.content.decode('utf-8'))

    if not response.ok:
        error_description = content.get('error_description', None)
        raise BadRequestError(error_description)

    access_token = content.get('access_token', None)
    token_type   = content.get('token_type', None)
    expires_in   = content.get('expires_in', None)
    scope        = content.get('scope', None)
    
    return Authorization(access_token, token_type, expires_in, scope, None)
    # TODO: Extract common functionality between this & _client_credentials()

def _authorization_code(conf):
    current_dir = os.path.abspath(os.curdir)
    file_path = os.path.join(current_dir, '.pytify')
    auth_key = get_auth_key(conf.client_id, conf.client_secret)

    try:
        with open(file_path, mode = 'r', encoding = 'UTF-8') as file:
            refresh_token = file.readline()
            if refresh_token:
                return _refresh_access_token(auth_key, refresh_token)
    except IOError:
        raise IOError('Application not authorized. File \'.pytify\' not found.')