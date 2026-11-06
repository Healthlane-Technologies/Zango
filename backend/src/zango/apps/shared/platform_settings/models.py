"""Platform-wide defaults — public schema, singleton.

Everything here is applied **when an app is created**, never retroactively:
each new tenant is stamped with these values and owns them from then on, so
changing a default later cannot silently move an existing app's dates,
timezone or theme out from under its users.
"""

from __future__ import annotations

import uuid

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


class PlatformAIAccount(FullAuditMixin):
    """An AI service account set up once for the whole platform (public schema).

    Apps link to it instead of holding their own key: an app's ``AppLLMProvider``
    with ``source="platform"`` reads this account's credentials when it calls the AI,
    so a key is rotated here once and every linked app follows. Budgets and usage
    stay per app, on the app's own provider row.

    App Studio links the spec's AI account to the default account when one is set
    up and working; otherwise it creates a placeholder for the app creator to fill.
    The key lives only in ``config_encrypted`` (never in settings or the env) and no
    API returns it; see ``masked_config()``.
    """

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    provider_slug = models.CharField(
        max_length=50, help_text="Registered provider class, e.g. 'anthropic'"
    )
    config_encrypted = models.BinaryField(null=True, blank=True)
    default_model = models.CharField(max_length=100, blank=True, default="")
    # [{id, name, context_window?, ...}] the apps may pick from; empty = the service's list
    model_list = models.JSONField(default=list, blank=True)
    app_monthly_budget_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly cap given to each app that links to this account. Null = none.",
    )
    is_default = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "platform_ai_account"
        ordering = ["-is_default", "name"]
        verbose_name = "Platform AI account"

    def __str__(self) -> str:
        return f"{self.name} ({self.provider_slug})"

    @property
    def usable(self) -> bool:
        return bool(self.is_enabled and self.is_validated and self.config_encrypted)

    @classmethod
    def default(cls) -> "PlatformAIAccount | None":
        """The working default account, or None."""
        acc = cls.objects.filter(is_default=True).first()
        return acc if acc is not None and acc.usable else None

    def provider_class(self):
        from zango.ai.providers.registry import get_provider_class

        return get_provider_class(self.provider_slug)

    def secret_fields(self) -> list[str]:
        from zango.ai.providers.registry import PROVIDER_REGISTRY

        cls = PROVIDER_REGISTRY.get(self.provider_slug)
        fields = getattr(cls, "config_fields", []) if cls else []
        return [f["name"] for f in fields if f.get("type") == "secret"] or ["api_key"]

    def get_config(self) -> dict:
        """Decrypt the stored config. In memory only; never serialize this."""
        if not self.config_encrypted:
            return {}
        from zango.ai.encryption import decrypt_config

        return decrypt_config(self.config_encrypted)

    def set_config(self, config: dict) -> None:
        from zango.ai.encryption import encrypt_config

        self.config_encrypted = encrypt_config(config)

    def masked_config(self) -> dict:
        from zango.ai.encryption import mask_config

        try:
            return mask_config(self.get_config(), self.secret_fields())
        except Exception:  # noqa: BLE001
            return {}

    def model_ids(self) -> list[str]:
        ids = [m.get("id") for m in self.model_list or [] if m.get("id")]
        if ids:
            return ids
        try:
            return [
                m["id"] for m in getattr(self.provider_class(), "supported_models", [])
            ]
        except Exception:  # noqa: BLE001
            return []

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # one default at a time
        if self.is_default:
            type(self).objects.exclude(pk=self.pk).filter(is_default=True).update(
                is_default=False
            )
