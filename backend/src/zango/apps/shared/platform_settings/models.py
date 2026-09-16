"""Platform-wide defaults — public schema, singleton.

Everything here is applied **when an app is created**, never retroactively:
each new tenant is stamped with these values and owns them from then on, so
changing a default later cannot silently move an existing app's dates,
timezone or theme out from under its users.
"""

from __future__ import annotations

from django.db import models

from zango.core.model_mixins import FullAuditMixin

from ..tenancy.utils import DATEFORMAT, DATETIMEFORMAT, TIMEZONES


class PlatformSettings(FullAuditMixin):
    """Singleton (singleton_id=1) platform configuration."""

    singleton_id = models.PositiveSmallIntegerField(
        default=1, unique=True, editable=False
    )

    # --- automatic domain allocation -------------------------------------
    # Tenants are resolved strictly by hostname, so an app with no Domain row
    # is unreachable. With this on, every new app gets one without an operator
    # having to remember.
    auto_domain_enabled = models.BooleanField(default=False)
    base_domain = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="e.g. zelthy.com — new apps get <random-words>.zelthy.com",
    )
    auto_domain_is_primary = models.BooleanField(default=True)

    # --- defaults stamped onto each new app ------------------------------
    default_timezone = models.CharField(
        max_length=255, blank=True, default="", choices=TIMEZONES
    )
    default_date_format = models.CharField(
        max_length=25, blank=True, default="", choices=DATEFORMAT
    )
    default_datetime_format = models.CharField(
        max_length=50, blank=True, default="", choices=DATETIMEFORMAT
    )
    default_language = models.CharField(max_length=50, blank=True, default="")
    # None means "use the framework's DEFAULT_THEME_CONFIG".
    default_theme_config = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "platform_settings"
        verbose_name = "Platform Settings"
        verbose_name_plural = "Platform Settings"

    def __str__(self) -> str:
        return "Platform Settings"

    def save(self, *args, **kwargs):
        # Normalise here rather than in the API view, so a value set from a
        # shell, a fixture or the admin is stored in the same shape. Anything
        # reading `base_domain` directly would otherwise get whatever was
        # pasted — scheme, trailing slash and all.
        from .domains import normalise_base_domain

        self.base_domain = normalise_base_domain(self.base_domain)
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "PlatformSettings":
        """The singleton row, created on first use."""
        obj, _ = cls.objects.get_or_create(singleton_id=1)
        return obj

    def tenant_defaults(self) -> dict:
        """Field values to stamp onto a new tenant.

        Only non-empty values are returned, so an unset platform default
        leaves the tenant's own column alone rather than blanking it.
        """
        mapping = {
            "timezone": self.default_timezone,
            "date_format": self.default_date_format,
            "datetime_format": self.default_datetime_format,
            "language": self.default_language,
        }
        return {k: v for k, v in mapping.items() if v}
