"""Utility helpers for symmetric encryption of sensitive fields."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


def _derive_key_from_secret(secret: str) -> bytes:
    padded_secret = secret.encode("utf-8")
    # Fernet keys must be 32 url-safe base64-encoded bytes
    return base64.urlsafe_b64encode(padded_secret.ljust(32, b"0")[:32])


def _get_fernet() -> Fernet:
    secret = os.getenv("SECRET_KEY", "change-me")
    key = _derive_key_from_secret(secret)
    return Fernet(key)


def encrypt_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    fernet = _get_fernet()
    token = fernet.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(value.encode("utf-8"))
    except InvalidToken as exc:
        raise EncryptionError("Unable to decrypt value") from exc
    return decrypted.decode("utf-8")
