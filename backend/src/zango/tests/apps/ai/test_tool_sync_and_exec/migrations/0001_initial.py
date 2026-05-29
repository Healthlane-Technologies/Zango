import django.db.models.deletion
import uuid

import zango.apps.dynamic_models.mixin
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appauth', '0006_appusermodel_app_objects'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('object_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('age', models.IntegerField(default=0)),
                ('created_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='appauth.appusermodel')),
                ('modified_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='appauth.appusermodel')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, zango.apps.dynamic_models.mixin.DynamicModelMixin),
        ),
    ]
