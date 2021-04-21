from decouple import config
import pathlib
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from application.drive_linker.drive_linker import browse_library_from_line

CLIENT_SECRETS_FILE_PATH = pathlib.Path(__file__).resolve().parent.joinpath("client_secrets.json")
MYCREDS_FILE_PATH = pathlib.Path(__file__).resolve().parent.joinpath("mycreds.txt")

with open(CLIENT_SECRETS_FILE_PATH, 'w') as f:
    f.write(config('CLIENT_SECRET_JSON_CONTENTS'))

with open(MYCREDS_FILE_PATH, 'w') as f:
    f.write(config('MYCREDS_TXT_CONTENTS'))

GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = CLIENT_SECRETS_FILE_PATH
gauth = GoogleAuth()
gauth.LoadCredentialsFile(MYCREDS_FILE_PATH)
drive = GoogleDrive(gauth)

pathlib.Path(CLIENT_SECRETS_FILE_PATH).unlink(missing_ok=True)
pathlib.Path(MYCREDS_FILE_PATH).unlink(missing_ok=True)
