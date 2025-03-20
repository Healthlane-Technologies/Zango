from celery import shared_task


@shared_task
def health_check_periodic_task():
    return "Celery beat is alive"
