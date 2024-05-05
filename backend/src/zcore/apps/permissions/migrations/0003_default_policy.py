from django.db import migrations


def create_default_policies(apps, schema_editor):
    """
    Creates default system policies
    """
    policy_model = apps.get_model("permissions", "PolicyModel")
    policy_model.objects.create(
        name="AllowFromAnywhere",
        type="system",
        statement={"permissions": [{"type": "userAccess", "accessIP": ["0.0.0.0/0"]}]},
        description="Policy to allow access from anywhere",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("permissions", "0002_policymodel_type_alter_policymodel_expiry"),
    ]

    operations = [
        migrations.RunPython(create_default_policies),
    ]
