from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="appllmtool",
            name="memory_policy",
            field=models.CharField(
                choices=[
                    ("include", "Include — replay verbatim in session history"),
                    (
                        "exclude",
                        "Exclude — drop from loaded history (side-effect tools)",
                    ),
                ],
                default="include",
                help_text=(
                    "include: replay tool call/result verbatim in session history (default). "
                    "exclude: drop from loaded history — use for side-effect tools (send_email, etc.)."
                ),
                max_length=10,
            ),
        ),
    ]
