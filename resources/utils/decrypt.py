import os
from cryptography.fernet import Fernet

def initialize_credential_decryption():
    key = os.environ.get("FERNET_KEY").encode()
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