from __future__ import unicode_literals

import cryptography.fernet

from cryptography.fernet import InvalidToken

import django.db
import django.db.models

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ZEncryptedFieldMixin:
    def get_crypter(self):
        configured_keys = getattr(settings, "FIELD_ENCRYPTION_KEY", None)

        if configured_keys is None:
            raise ImproperlyConfigured(
                "FIELD_ENCRYPTION_KEY must be defined in settings"
            )

        try:
            # Allow the use of key rotation
            if isinstance(configured_keys, (tuple, list)):
                keys = [
                    cryptography.fernet.Fernet(
                        k if isinstance(k, bytes) else k.encode("utf-8")
                    )
                    for k in configured_keys
                ]
            else:
                # else turn the single key into a list of one
                keys = [
                    cryptography.fernet.Fernet(
                        configured_keys
                        if isinstance(configured_keys, bytes)
                        else configured_keys.encode("utf-8")
                    ),
                ]
        except Exception as e:
            raise ImproperlyConfigured(
                "FIELD_ENCRYPTION_KEY defined incorrectly: {}".format(str(e))
            ) from e

        if len(keys) == 0:
            raise ImproperlyConfigured(
                "No keys defined in setting FIELD_ENCRYPTION_KEY"
            )

        return cryptography.fernet.MultiFernet(keys)

    def encrypt_str(self, s):
        CRYPTER = self.get_crypter()
        # be sure to encode the string to bytes
        # Fernet works on bytes
        return CRYPTER.encrypt(s.encode("utf-8"))

    def decrypter(self, t):
        CRYPTER = self.get_crypter()
        # be sure to decode the bytes to a string
        # Ensure input is bytes before decrypting
        input_bytes = t if isinstance(t, bytes) else t.encode("utf-8")
        return CRYPTER.decrypt(input_bytes).decode("utf-8")


class EncryptedMixin(ZEncryptedFieldMixin):
    """
    Saves encrypted value in Database
    For getting decrypted value, call the decryption function after getting the value
    """

    def get_db_prep_save(self, value, connection):
        # Use super() without arguments in Python 3
        value = super().get_db_prep_save(value, connection)

        if value is None:
            return value

        # In Python 3, strings are unicode by default.
        # We need to check if the value is already encrypted bytes or a string.
        # If it's bytes and decrypts successfully, assume it's already encrypted.
        # If it's a string or bytes that don't decrypt, encrypt it.

        # First, handle the case where the value might be bytes (e.g., coming from the DB)
        if isinstance(value, bytes):
            try:
                self.decrypter(value)  # Check if it's valid encrypted data
                return value  # It's already encrypted bytes, return as is
            except InvalidToken:
                # Not valid encrypted data, treat as raw value and encrypt
                value = value.decode("utf-8")  # Decode bytes to string for encryption

        # If it's a string or was invalid bytes, encrypt the string representation
        try:
            self.decrypter(value)  # Check if it's valid encrypted string
            return value.encode("utf-8")  # It's already encrypted, return bytes
        except InvalidToken:
            # Not valid encrypted string data, encrypt the raw value
            # encrypt_str returns bytes
            encrypted_value_bytes = self.encrypt_str(str(value))
            # Many database backends expect string type from get_db_prep_save
            # The original code decoded bytes back to string, we'll replicate that.
            return encrypted_value_bytes.decode("utf-8")

    def get_internal_type(self):
        return "TextField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        if "max_length" in kwargs:
            del kwargs["max_length"]

        return name, path, args, kwargs


class EncryptedCharField(EncryptedMixin, django.db.models.CharField):
    pass


class EncryptedTextField(EncryptedMixin, django.db.models.TextField):
    pass
