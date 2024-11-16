import secrets
import string
import base64
import json
from Crypto.Cipher import DES3
from django.utils import timezone

def generate_tx_ref():
    char_set = string.ascii_uppercase + string.digits
    unique_part = ''.join(secrets.choice(char_set) for _ in range(36))
    tx_ref = f"TAWKTOOLS_{unique_part}-{timezone.now()}"
    return tx_ref


def encrypt_data(key, data):
    # Convert data dictionary to a JSON string
    plain_text = json.dumps(data)
    
    # Ensure the key is 24 bytes long for 3DES encryption
    key = key.encode('utf-8')
    if len(key) < 24:
        key = key + (24 - len(key)) * b'0'  # Pad the key if it's less than 24 bytes
    elif len(key) > 24:
        key = key[:24]  # Truncate the key if it's more than 24 bytes

    # Pad the plaintext to a multiple of 8 bytes for 3DES
    block_size = 8
    pad_diff = block_size - (len(plain_text) % block_size)
    plain_text_padded = plain_text + (chr(pad_diff) * pad_diff)

    # Encrypt using 3DES in ECB mode
    cipher = DES3.new(key, DES3.MODE_ECB)
    encrypted_text = cipher.encrypt(plain_text_padded.encode('utf-8'))
    
    # Encode the encrypted text in base64
    encrypted_text_base64 = base64.b64encode(encrypted_text).decode('utf-8')
    return encrypted_text_base64
