"""Fernet symmetric encryption for storing sensitive credentials.

Used to encrypt per-master Robokassa passwords at rest in the database.
Key is loaded from ENCRYPTION_KEY environment variable.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def get_fernet() -> Fernet:
    """Get Fernet instance using the app encryption key."""
    return Fernet(settings.encryption_key.encode("utf-8"))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str | None:
    """Decrypt a string value. Returns None if decryption fails."""
    try:
        f = get_fernet()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
