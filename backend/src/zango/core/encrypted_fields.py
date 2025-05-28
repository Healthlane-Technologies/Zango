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
        value = super().get_db_prep_save(value, connection)

        if value is None:
            return value

        if isinstance(value, bytes):
            try:
                self.decrypter(value)
                return value
            except InvalidToken:
                value = value.decode("utf-8")

        try:
            self.decrypter(value)
            return value.encode("utf-8")
        except InvalidToken:
            encrypted_value_bytes = self.encrypt_str(str(value))
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
