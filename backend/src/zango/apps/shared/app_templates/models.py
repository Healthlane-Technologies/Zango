"""App templates — the catalogue of products Zelthy ships, in the public schema.

A template is a product a new client *describes* rather than develops. Each one
has three parts, and a version holds all three together:

* catalogue metadata — what the gallery, quick view and detail page show;
* a requirement builder — the JSON Schema the requirement YAML must satisfy,
  UI hints for the console's builder panel, the interview the analyst follows,
  starter/example YAML and cross-reference rules;
* a build skill — the files the build agent loads to turn the approved YAML
  into a working app (``AppTemplateFile`` rows).

Versions are immutable once published, and apps pin the version they were
built from (``AppTemplateBinding``; tenant requirements pin by uuid, since a
foreign key cannot cross schemas). Publishing a new version therefore never
changes an existing app — moving an app forward is an explicit upgrade.
"""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from zango.core.model_mixins import FullAuditMixin


SLUG_RE = r"^[a-z][a-z0-9_-]{1,63}$"
SEMVER_RE = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$"

# A build skill is a tree of text files. The limits keep a pack reviewable and
# keep materialising it onto disk cheap.
MAX_FILE_BYTES = 512 * 1024
MAX_VERSION_BYTES = 5 * 1024 * 1024
MAX_VERSION_FILES = 200


class ImmutableVersionError(ValidationError):
    """Raised when something tries to change a published version's content."""


class TemplateStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class VersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    DEPRECATED = "deprecated", "Deprecated"


class SpecFormat(models.TextChoices):
    MARKDOWN = "markdown", "Markdown"
    YAML = "yaml", "YAML"


class BindingSource(models.TextChoices):
    SCAFFOLD = "scaffold", "Created from the template"
    REQUIREMENT = "requirement", "Adopted during a requirement"
    UPGRADE = "upgrade", "Upgraded"


class AppTemplate(FullAuditMixin):
    """A template's stable identity, and what the gallery lists."""

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    slug = models.CharField(
        max_length=64, unique=True, validators=[RegexValidator(SLUG_RE)]
    )
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True, default="")
    icon = models.CharField(max_length=64, blank=True, default="")
    one_liner = models.TextField(blank=True, default="")
    is_beta = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=TemplateStatus.choices,
        default=TemplateStatus.DRAFT,
        db_index=True,
    )
    current_version = models.ForeignKey(
        "AppTemplateVersion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        db_table = "app_templates_template"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.slug


class AppTemplateVersion(FullAuditMixin):
    """One complete, versioned pack. Immutable once published."""

    # Everything that makes up the pack. Once published none of it may change;
    # only `status` may move on (to deprecated).
    CONTENT_FIELDS = (
        "version",
        "catalogue",
        "spec_format",
        "spec_root",
        "json_schema",
        "ui_schema",
        "interview_md",
        "schema_md",
        "starter_yaml",
        "example_yaml",
        "rules",
        "build_skill_name",
        "workspace_sha",
        "workspace_engine_paths",
        "builder_html",
        "builder_adapter",
        "references",
        "drafting_md",
    )

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    template = models.ForeignKey(
        AppTemplate, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.CharField(max_length=32, validators=[RegexValidator(SEMVER_RE)])
    status = models.CharField(
        max_length=16,
        choices=VersionStatus.choices,
        default=VersionStatus.DRAFT,
        db_index=True,
    )
    changelog = models.TextField(blank=True, default="")

    # --- catalogue: description, aka, fits_when, gives_you, packages, roles,
    # workflows, data_objects, integrations, compliance, recommended_agents,
    # app_name_prefill, app_prompt_prefill.
    catalogue = models.JSONField(default=dict, blank=True)

    # --- requirement builder
    spec_format = models.CharField(
        max_length=16, choices=SpecFormat.choices, default=SpecFormat.YAML
    )
    spec_root = models.CharField(max_length=64, blank=True, default="")
    json_schema = models.JSONField(default=dict, blank=True)
    # {"sections": [{"id", "title", "pointer", "hint", "order"}]}
    ui_schema = models.JSONField(default=dict, blank=True)
    interview_md = models.TextField(blank=True, default="")
    # The prose vocabulary the analyst reads; json_schema is what is enforced.
    schema_md = models.TextField(blank=True, default="")
    starter_yaml = models.TextField(blank=True, default="")
    example_yaml = models.TextField(blank=True, default="")
    rules = models.JSONField(default=list, blank=True)

    # --- build skill (files live in AppTemplateFile)
    build_skill_name = models.CharField(max_length=64, blank=True, default="")

    # --- workspace: the app skeleton (engine, config layer, frontend…) a new
    # app starts from, as one zip in Zango's app-template layout. Optional: a
    # template without one is built on a blank Zango app. Its hash is part of
    # the version's content, so a published zip can never change.
    workspace_zip = models.BinaryField(null=True, blank=True, editable=False)
    workspace_sha = models.CharField(max_length=64, blank=True, default="")
    workspace_size = models.PositiveIntegerField(default=0)
    # Paths inside the workspace that belong to the template, not the app
    # (e.g. backend/template/). Restored from the zip before every build;
    # everything else is the app's own.
    workspace_engine_paths = models.JSONField(default=list, blank=True)

    # --- custom builder: a template's own requirement-builder page (for PSP,
    # Journey Studio) shown in the Agent tab instead of the schema-driven
    # panel. The page is used as-is; ``builder_adapter`` is the small script
    # injected after it that speaks the platform's postMessage protocol.
    builder_html = models.TextField(blank=True, default="")
    builder_adapter = models.TextField(blank=True, default="")

    # --- one-pass drafting: curated reference journeys a draft can start
    # from ([{id, title, summary, tags, yaml}]), and the guide the analyst
    # follows to draft a whole journey from the user's documents.
    references = models.JSONField(default=list, blank=True)
    drafting_md = models.TextField(blank=True, default="")

    # Set at publish, over every content field and file: the cache key and
    # the on-disk directory name, so it can never go stale.
    content_sha = models.CharField(max_length=64, blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "app_templates_version"
        ordering = ["template", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "version"], name="app_template_version_unique"
            ),
            models.UniqueConstraint(
                fields=["template"],
                condition=Q(status="draft"),
                name="app_template_one_draft",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.template_id}@{self.version} ({self.status})"

    @property
    def is_draft(self) -> bool:
        return self.status == VersionStatus.DRAFT

    @property
    def has_workspace(self) -> bool:
        return bool(self.workspace_sha)

    @property
    def has_builder(self) -> bool:
        return bool(self.builder_html and self.builder_adapter)

    @property
    def sections(self) -> list:
        sections = (self.ui_schema or {}).get("sections") or []
        return [s for s in sections if isinstance(s, dict) and s.get("id")]

    def save(self, *args, **kwargs):
        if self.pk:
            stored = (
                AppTemplateVersion.objects.filter(pk=self.pk)
                .values("status", *self.CONTENT_FIELDS)
                .first()
            )
            if stored and stored["status"] != VersionStatus.DRAFT:
                changed = [
                    f for f in self.CONTENT_FIELDS if getattr(self, f) != stored[f]
                ]
                if changed:
                    raise ImmutableVersionError(
                        f"{self} is {stored['status']}; its content cannot change "
                        f"(tried to change {', '.join(changed)}). Create a new version."
                    )
                if self.status == VersionStatus.DRAFT:
                    raise ImmutableVersionError(f"{self} cannot go back to draft.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != VersionStatus.DRAFT:
            raise ImmutableVersionError(
                f"{self} is {self.status} and cannot be deleted; deprecate it instead."
            )
        return super().delete(*args, **kwargs)


class AppTemplateFile(FullAuditMixin):
    """One file of a version's build skill, by path relative to the skill dir."""

    version = models.ForeignKey(
        AppTemplateVersion, on_delete=models.CASCADE, related_name="files"
    )
    path = models.CharField(max_length=255)
    content = models.TextField(blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")
    size = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "app_templates_file"
        ordering = ["version", "path"]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "path"], name="app_template_file_unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.version} {self.path}"

    def save(self, *args, **kwargs):
        from .services.paths import normalise_pack_path, sha256_text

        if not self.version.is_draft:
            raise ImmutableVersionError(
                f"{self.version} is {self.version.status}; its files cannot change."
            )
        self.path = normalise_pack_path(self.path)
        encoded = self.content.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise ValidationError(f"{self.path} is larger than {MAX_FILE_BYTES} bytes.")
        self.size = len(encoded)
        self.sha256 = sha256_text(self.content)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self.version.is_draft:
            raise ImmutableVersionError(
                f"{self.version} is {self.version.status}; its files cannot change."
            )
        return super().delete(*args, **kwargs)


class AppTemplateBinding(FullAuditMixin):
    """Which template version an app is built on. One per app."""

    tenant = models.OneToOneField(
        "tenancy.TenantModel",
        on_delete=models.CASCADE,
        related_name="template_binding",
    )
    template = models.ForeignKey(
        AppTemplate, on_delete=models.PROTECT, related_name="bindings"
    )
    version = models.ForeignKey(
        AppTemplateVersion, on_delete=models.PROTECT, related_name="bindings"
    )
    bound_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(
        max_length=16, choices=BindingSource.choices, default=BindingSource.SCAFFOLD
    )

    class Meta:
        db_table = "app_templates_binding"

    def __str__(self) -> str:
        return f"{self.tenant_id} → {self.version}"
