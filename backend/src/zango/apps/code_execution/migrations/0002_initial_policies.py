"""Seed the three permission policies for Code Execution.

These records are referenced by the API layer to gate use / edit / run. They
also let tenants attach the policies to specific user roles via PolicyGroupModel.
"""

from django.db import migrations


POLICIES = [
    {
        "name": "codexec.use",
        "path": "platform.code_execution.use",
        "description": "View Code Execution snippets and run history.",
    },
    {
        "name": "codexec.edit",
        "path": "platform.code_execution.edit",
        "description": "Create, update, and archive Code Execution snippets and their files.",
    },
    {
        "name": "codexec.run",
        "path": "platform.code_execution.run",
        "description": "Trigger a Code Execution run.",
    },
]


def seed_policies(apps, schema_editor):
    PolicyModel = apps.get_model("permissions", "PolicyModel")
    for p in POLICIES:
        PolicyModel.objects.update_or_create(
            name=p["name"],
            path=p["path"],
            defaults={
                "description": p["description"],
                "statement": {
                    "permissions": [{"type": "platform", "name": p["path"]}],
                },
                "type": "system",
                "is_active": True,
            },
        )


def remove_policies(apps, schema_editor):
    PolicyModel = apps.get_model("permissions", "PolicyModel")
    for p in POLICIES:
        PolicyModel.objects.filter(name=p["name"], path=p["path"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("code_execution", "0001_initial"),
        ("permissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_policies, remove_policies),
    ]
