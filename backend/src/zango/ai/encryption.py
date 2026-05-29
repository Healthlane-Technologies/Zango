"""
Encryption utilities for storing API keys and other secrets in provider configs.
Reuses Zango's existing FIELD_ENCRYPTION_KEY + Fernet infrastructure.

- API keys are encrypted before storage and decrypted only when needed
- Decrypted keys are NEVER returned in API responses (always masked)
- Decryption happens only at the moment of making an LLM call, in memory
"""

import copy
import json

from zango.core.encrypted_fields import ZEncryptedFieldMixin


_encryptor = ZEncryptedFieldMixin()


def encrypt_config(config_dict: dict) -> bytes:
    """
    Encrypt a config dict as a JSON blob.
    Returns encrypted bytes suitable for storage in BinaryField.
    """
    json_str = json.dumps(config_dict, sort_keys=True)
    return _encryptor.encrypt_str(json_str)


def decrypt_config(encrypted_blob: bytes) -> dict:
    """
    Decrypt an encrypted config blob back to a dict.
    Handles both bytes and memoryview inputs (PostgreSQL BinaryField
    may return memoryview).
    """
    if isinstance(encrypted_blob, memoryview):
        encrypted_blob = bytes(encrypted_blob)
    json_str = _encryptor.decrypter(encrypted_blob)
    return json.loads(json_str)


def mask_config(config_dict: dict, secret_field_names: list[str]) -> dict:
    """
    Return a copy of config with secret values masked.
    Used for API responses — secrets are never sent back in plaintext.

    Masking format: first 6 chars + "...****" + last 4 chars,
    or just "****" if the value is too short.
    """
    masked = copy.deepcopy(config_dict)
    for field_name in secret_field_names:
        if field_name in masked and masked[field_name]:
            value = str(masked[field_name])
            if len(value) > 12:
                masked[field_name] = value[:6] + "...****" + value[-4:]
            else:
                masked[field_name] = "****"
    return masked
