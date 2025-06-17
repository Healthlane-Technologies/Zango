from django.db import migrations
from django.db.utils import OperationalError


def add_periodic_task(apps, schema_editor):
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
        CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')

        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute='*',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )


        PeriodicTask.objects.get_or_create(
            crontab=crontab_schedule,
            name='health_check_task',
            task='zango.apps.tasks.tasks.health_check',
            defaults={
                'enabled': False,
            }
        )
    except OperationalError:
        print("django_celery_beat tables not found. Skipping periodic task creation.")


def remove_periodic_task(apps, schema_editor):
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

        PeriodicTask.objects.filter(name='health_check_task').delete()
    except OperationalError:
        print("django_celery_beat tables not found. Skipping periodic task removal.")


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0018_improve_crontab_helptext'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_periodic_task, reverse_code=remove_periodic_task),
    ]
