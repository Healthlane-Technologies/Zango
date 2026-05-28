import django.db.models.deletion

from django.db import migrations, models

import zango.core.storage_utils


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0003_rename_memory_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppLLMInvocationFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "modified_by",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                (
                    "sha256",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        help_text="SHA-256 of the file bytes. Empty for URL-only attachments.",
                        max_length=64,
                    ),
                ),
                (
                    "size_bytes",
                    models.BigIntegerField(
                        default=0,
                        help_text="Size of the file bytes. 0 for URL-only attachments.",
                    ),
                ),
                ("media_type", models.CharField(blank=True, default="", max_length=120)),
                ("filename", models.CharField(blank=True, default="", max_length=512)),
                (
                    "source_kind",
                    models.CharField(
                        choices=[
                            ("upload", "Upload (django_file / bytes / path)"),
                            ("url", "Public URL (not mirrored)"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "source_url",
                    models.URLField(
                        blank=True,
                        default="",
                        help_text="Original URL when source_kind='url'.",
                        max_length=2048,
                    ),
                ),
                (
                    "blob",
                    zango.core.storage_utils.ZFileField(
                        blank=True, null=True, upload_to="", validators=[]
                    ),
                ),
                (
                    "invocation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="ai.appllminvocation",
                    ),
                ),
            ],
            options={
                "ordering": ["invocation_id", "id"],
                "indexes": [
                    models.Index(
                        fields=["sha256"],
                        name="ai_appllmin_sha256_8bd66f_idx",
                    ),
                    models.Index(
                        fields=["invocation", "id"],
                        name="ai_appllmin_invocat_f9363f_idx",
                    ),
                ],
            },
        ),
    ]
