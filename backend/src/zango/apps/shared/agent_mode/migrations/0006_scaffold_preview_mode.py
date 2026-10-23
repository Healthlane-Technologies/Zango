from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent_mode_platform", "0005_scaffold_documents"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentappscaffold",
            name="preview_mode",
            field=models.CharField(blank=True, default="kit", max_length=8),
        ),
    ]
