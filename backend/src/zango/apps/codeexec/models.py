import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from zango.apps.shared.platformauth.models import PlatformUserModel
from zango.core.model_mixins import FullAuditMixin
from zango.core.storage_utils import ZFileField

from .guards import validate_imports


class ZangoAdminCodeExecutionModel(FullAuditMixin):
    slug_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(
        _("name"), max_length=100, help_text=_("Example: 'flatpages/default.html'")
    )
    description = models.CharField(
        _("Description"), max_length=1000, help_text=_("Template Description")
    )
    code = models.TextField(_("content"), blank=True)
    artifact = ZFileField(
        verbose_name="ZangoAdminCodeExecution Artifact", null=True, blank=True
    )
    author = models.ForeignKey(PlatformUserModel, null=True, on_delete=models.SET_NULL)
    execution_history = models.JSONField(null=True, blank=True, default=[])
    output_file = ZFileField(
        verbose_name="ZangoAdminCodeExecution Output", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        not_allowed_imports = validate_imports(self.code)
        if not_allowed_imports:
            raise ValidationError("Code contains imports which are not allowed to use.")

        super(ZangoAdminCodeExecutionModel, self).save(*args, **kwargs)
