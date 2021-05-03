from decouple import config
from dateutil import parser
import json
from oauth2client.client import OAuth2Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from application.drive_linker.drive_linker import browse_library_from_line

# Setup client config
client_secrets_json_contents = json.loads(config('CLIENT_SECRET_JSON_CONTENTS'))
client_config = client_secrets_json_contents['web']
client_config['redirect_uri'] = client_config.pop('redirect_uris')[0]
client_config['revoke_uri'] = None

# Setup credentials
mycreds_txt_contents = json.loads(config('MYCREDS_TXT_CONTENTS'))
mycreds = {k: v for k, v in mycreds_txt_contents.items() if k not in ['invalid', '_class', '_module']}
mycreds['token_expiry'] = parser.parse(mycreds['token_expiry'], ignoretz=True)
credentials = OAuth2Credentials(**mycreds)

GoogleAuth.DEFAULT_SETTINGS['client_config_backend'] = 'settings'
gauth = GoogleAuth()
gauth.client_config = client_config
gauth.credentials = credentials
drive = GoogleDrive(gauth)
