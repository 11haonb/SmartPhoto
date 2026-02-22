import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_key() -> bytes:
    raw = settings.ENCRYPTION_KEY
    if len(raw) == 64:
        return bytes.fromhex(raw)
    return raw.encode("utf-8").ljust(32, b"\0")[:32]


def encrypt_api_key(plaintext: str) -> str:
    key = _get_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    key = _get_key()
    raw = base64.b64decode(encrypted)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
