import os
from decouple import config
from cryptography.fernet import Fernet
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def initialize_credential_decryption():
    key = config("FERNET_KEY").encode()
    with open("enc_creds.txt") as f:
        enc_creds = f.read().encode()
    
    with open("enc_json.txt") as f:
        enc_json = f.read().encode()
    
    fernet = Fernet(key)
    plain_creds = fernet.decrypt(enc_creds).decode()
    plain_json = fernet.decrypt(enc_json).decode()
    
    with open("mycreds.txt", "w") as f:
        f.write(plain_creds)
    
    with open("client_secrets.json", "w") as f:
        f.write(plain_json)
    
    print("Decryption carried out successfully.")

def make_drive_instance():
    initialize_credential_decryption()
    gauth = GoogleAuth()
    GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
    gauth.LoadCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)

    if os.path.isfile("client_secrets.json"):
        os.remove("client_secrets.json")
        print("File: client json removed successfully.")
    if os.path.isfile("mycreds.txt"):
        os.remove("mycreds.txt")
        print("File: creds txt removed successfully.")
    
    return drive