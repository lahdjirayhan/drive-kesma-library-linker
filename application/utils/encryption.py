import os
import base64
from decouple import config
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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