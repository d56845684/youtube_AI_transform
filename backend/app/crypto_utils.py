"""Utility helpers for symmetric encryption of sensitive fields.

If the ``cryptography`` package is unavailable (for example, when installing
dependencies offline), the helpers fall back to a lightweight XOR-based
mechanism. The fallback keeps the application running without the optional
dependency while still providing reversible obfuscation for stored secrets.
"""

import base64
import os
from itertools import cycle
from typing import Optional

try:  # ``cryptography`` may be unavailable in offline environments.
    from cryptography.fernet import Fernet, InvalidToken

    _CRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when dependency is missing.
    Fernet = None  # type: ignore

    class InvalidToken(Exception):
        """Fallback placeholder when ``cryptography`` is absent."""

    _CRYPT_AVAILABLE = False


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


def _derive_key_from_secret(secret: str) -> bytes:
    padded_secret = secret.encode("utf-8")
    # Fernet keys must be 32 url-safe base64-encoded bytes
    return base64.urlsafe_b64encode(padded_secret.ljust(32, b"0")[:32])


def _xor_encrypt(value: str, key: bytes) -> str:
    encrypted_bytes = bytes(b ^ k for b, k in zip(value.encode("utf-8"), cycle(key)))
    return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")


def _xor_decrypt(value: str, key: bytes) -> str:
    try:
        decoded = base64.urlsafe_b64decode(value.encode("utf-8"))
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive guard.
        raise EncryptionError("Unable to decode stored value") from exc

    try:
        decrypted_bytes = bytes(b ^ k for b, k in zip(decoded, cycle(key)))
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive guard.
        raise EncryptionError("Unable to decrypt value") from exc


def _get_key() -> bytes:
    secret = os.getenv("SECRET_KEY", "change-me")
    return _derive_key_from_secret(secret)


def _get_fernet(key: bytes) -> Optional[Fernet]:
    if not _CRYPT_AVAILABLE:
        return None
    return Fernet(key)


def encrypt_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    key = _get_key()
    fernet = _get_fernet(key)
    if fernet:
        token = fernet.encrypt(value.encode("utf-8"))
        return token.decode("utf-8")
    return _xor_encrypt(value, key)


def decrypt_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    key = _get_key()
    fernet = _get_fernet(key)
    if fernet:
        try:
            decrypted = fernet.decrypt(value.encode("utf-8"))
        except InvalidToken as exc:
            raise EncryptionError("Unable to decrypt value") from exc
        return decrypted.decode("utf-8")
    return _xor_decrypt(value, key)
