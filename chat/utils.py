import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings

def generate_and_save_key():
    key = Fernet.generate_key()
    key_base64 = base64.urlsafe_b64encode(key).decode('utf-8')
    key_file_path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
    with open(key_file_path, 'a') as key_file:
        key_file.write(key_base64 + '\n')

def load_keys():
    key_file_path = os.path.join(settings.BASE_DIR, 'Encryption_Key.key')
    if os.path.exists(key_file_path):
        with open(key_file_path, 'r') as key_file:
            key_base64_list = key_file.readlines()
        return [base64.urlsafe_b64decode(key.strip()) for key in key_base64_list]
    return []

