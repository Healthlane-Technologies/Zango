from django.core.validators import RegexValidator
from django.db import models

from zango.apps.auditlogs.registry import auditlog
from zango.core.encrypted_fields import EncryptedTextField, ZEncryptedFieldMixin
from zango.core.model_mixins import FullAuditMixin


class SecretsModel(ZEncryptedFieldMixin, FullAuditMixin):
    key = models.CharField(
        "Secret key",
        max_length=50,
        validators=[
            RegexValidator(
                "^[A-Z][a-z0-9_]*$",
                "No Space, First Character Caps, No Special Character except _ allowed in Secret key",
            )
        ],
        unique=True,
    )
    value = EncryptedTextField("Secret Value", blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.key

    def get_unencrypted_val(self):
        return self.decrypter(self.value)


auditlog.register(SecretsModel, exclude_fields=["value"])
