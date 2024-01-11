from django_celery_beat.models import CrontabSchedule


def validate_minute(cron_minute):
    _minutes = cron_minute.split(",")
    validated = True
    try:
        for m in _minutes:
            if int(m) < 0 or int(m) >= 60:
                validated = False
    except:
        validated = False
    return validated


def validate_hour(cron_hours):
    _hours = cron_hours.split(",")
    validated = True
    try:
        for h in _hours:
            if int(h) < 0 or int(h) > 24:
                validated = False
    except:
        validated = False
    return validated


def validate_day_of_week(dow):
    _dow = dow.split(",")
    validated = True
    try:
        for d in _dow:
            if int(d) < 1 or int(d) > 7:
                validated = False
    except:
        validated = False
    return validated


def validate_day_of_month(dom):
    _dom = dom.split(",")
    validated = True
    try:
        for d in _dom:
            if int(d) < 1 or int(d) > 31:
                validated = False
    except:
        validated = False
    return validated


def validate_month_of_year(moy):
    _moy = moy.split(",")
    validated = True
    try:
        for m in _moy:
            if int(m) < 1 or int(m) > 12:
                validated = False
    except:
        validated = False
    return validated


def validate_cron_input(crontab):
    if crontab.get("minute"):
        if crontab["minute"] != "*" and not validate_minute(crontab["minute"]):
            return False
    if crontab.get("hour"):
        if crontab["hour"] != "*" and not validate_hour(crontab["hour"]):
            return False
    if crontab.get("day_of_week"):
        if crontab["day_of_week"] != "*" and not validate_day_of_week(
            crontab["day_of_week"]
        ):
            return False
    if crontab.get("day_of_month"):
        if crontab["day_of_month"] != "*" and not validate_day_of_month(
            crontab["day_of_month"]
        ):
            return False
    if crontab.get("month_of_year"):
        if crontab["month_of_year"] != "*" and not validate_month_of_year(
            crontab["month_of_year"]
        ):
            return False
    return True


def get_crontab_obj(crontab={}):
    if not validate_cron_input(crontab):
        raise ValueError("Invalid cron expression")
    
    if not crontab:
        crontab = {
          "minute": "*",
          "hour": "*",
          "day_of_week": "*",
          "day_of_month": "*",
          "month_of_year": "*"
        }

    schedule, created = CrontabSchedule.objects.get_or_create(**crontab)
    if created:
        return schedule, True
    return schedule, False
