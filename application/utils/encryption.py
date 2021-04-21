import os
import base64
from decouple import config
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def initialize_credential_decryption(path):
    # TODO (Rayhan) specify path prepending. I intend to save enc_creds and enc_json in drive_linker folder
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
    
    print ("Decryption carried out successfully.")

def encrypt_fernet(data, salt):
    return Fernet(derive_key(salt).encode()).encrypt(data.encode()).decode()

def decrypt_fernet(data, salt):
    return Fernet(derive_key(salt).encode()).decrypt(data.encode()).decode()

def derive_key(salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(config('FERNET_MASTER').encode())).decode()
    return key