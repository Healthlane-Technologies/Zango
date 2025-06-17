from celery import shared_task


@shared_task
def health_check_periodic_task():
    return "Celery beat is alive"


@shared_task
def health_check():
    import requests

    from django.conf import settings

    try:
        resp = requests.get(settings.HEALTH_CHECK_URL)
        resp.raise_for_status()
        return {"result": "success"}
    except Exception as e:
        import traceback

        return {"result": "failure", "error": traceback.format_exc()}
