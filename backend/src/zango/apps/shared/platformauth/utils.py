import time

import jwt
import redis
import requests

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate

from django.conf import settings

from zango.apps.shared.platformauth.constants import (
    GOOGLE_OAUTH_BASE_URL,
    MICROSOFT_KEY_URL,
)


class OpenIDValidator:
    """
    Class to decode token and validate nonce.

    Attributes:
        config (dict): Configuration dictionary containing provider information.
        token (str): The token to decode and validate.
        username (str or None): The username extracted from the token.
        public_key (str): The public key used for token verification.
    """

    provider_username_field = {"azure": "preferred_username", "google": "email"}

    def __init__(self, config, token, provider):
        """
        Initialize the OpenIDValidator with configuration and token.

        Args:
            config (dict): Configuration dictionary containing provider information.
            token (str): The token to decode and validate.
        """
        self.config = config
        self.token = token
        self.provider = provider
        self.public_key = ""

    def get_public_key(self):
        """
        Retrieve the public key for token verification based on the provider.

        Returns:
            str: The public key as a string.
        """

        if not self.public_key:
            token_header = jwt.get_unverified_header(self.token)
            provider = self.provider
            if provider == "azure":
                keys = requests.get(url=MICROSOFT_KEY_URL).json()["keys"]
                kid = token_header["kid"]
                key = [d for d in keys if d["kid"] == kid][0]
                pubkey = key["x5c"][0]
        return pubkey

    def decode_token(self):
        """
        Decode the token using the appropriate method for the provider.

        Returns:
            bool: True if the token was successfully decoded, False otherwise.
        """
        try:
            provider = self.provider
            if provider == "azure":
                public_key = self.get_public_key()
                cert_str = (
                    "-----BEGIN CERTIFICATE-----\n"
                    + public_key
                    + "\n-----END CERTIFICATE-----\n"
                )
                cert_obj = load_pem_x509_certificate(
                    cert_str.encode(), default_backend()
                )
                public_key = cert_obj.public_key()
                cert_obj = load_pem_x509_certificate(
                    cert_str.encode(), default_backend()
                )
                public_key = cert_obj.public_key()
                decoded = jwt.decode(
                    self.token,
                    public_key,
                    algorithms=["RS256"],
                    audience=self.config["client_id"],
                )
            elif provider == "google":
                url = GOOGLE_OAUTH_BASE_URL + "tokeninfo?id_token=%s" % (self.token)
                decoded = requests.get(url).json()
            self.decoded_token = decoded
            return True
        except Exception as e:
            import traceback

            traceback.print_exc()
            return False

    def validate_nonce(self):
        """
        Validate the nonce value from the decoded token against a Redis store.

        Returns:
            bool: True if the nonce is valid, False otherwise.
        """

        r = redis.from_url(settings.REDIS_URL)
        try:
            nonce = self.decoded_token["nonce"]
            result = r.hgetall(nonce)
            result = {k.decode("utf-8"): v.decode("utf-8") for k, v in result.items()}
            expiry_at = result["expiry_at"]
            if float(expiry_at) > time.time():
                return True
            else:
                return False
        except Exception as e:
            import traceback

            traceback.print_exc()
            return False

    def delete_nonce(self):
        """
        Delete the nonce from the Redis store.
        """

        try:
            r = redis.from_url(settings.REDIS_URL)
            nonce = self.decoded_token["nonce"]
            r.delete(nonce)
        except Exception as e:
            pass
        return

    def get_username(self):
        """
        Retrieve the username from the decoded token.

        Returns:
            str: The username extracted from the token.
        """

        validate_nonce = self.validate_nonce()
        username_field = self.provider_username_field.get(self.provider)

        if username_field:
            username = self.decoded_token.get(username_field)
            return username
        else:
            return False

    def is_validated(self):
        """
        Check if the token is decoded and nonce is validated.

        Returns:
            bool: True if both token decoding and nonce validation succeed, False otherwise.
        """
        if not self.decode_token() or not self.validate_nonce():
            return False
        return True
