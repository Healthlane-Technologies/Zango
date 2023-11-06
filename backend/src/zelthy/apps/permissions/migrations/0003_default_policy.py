from django.db import migrations


def create_default_policies(apps, schema_editor):
    """
    creates AnonymousUsers & SystemUsers roles
    """
    user_role_model = apps.get_model("permissions", "PolicyModel")
    user_role_model.objects.create(
        name="AppLandingViewAccess",
        type="system",
        statement={
            "permissions": [
                {"name": "app_landing.views.AppLandingPageView", "type": "view"}
            ]
        },
        description="Policy to allow access to the App Landing view",
    )
    user_role_model.objects.create(
        name="AllowFromAnywhere",
        type="system",
        statement={"permissions": [{"type": "userAccess", "accessIP": ["0.0.0.0/0"]}]},
        description="",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("permissions", "0002_policymodel_type_alter_policymodel_expiry"),
    ]

    operations = [
        migrations.RunPython(create_default_policies),
    ]
