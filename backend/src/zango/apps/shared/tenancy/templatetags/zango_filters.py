"""
Module containing custom template filters
"""

from django import template

register = template.Library()


@register.filter()
def humanize_timedelta(timedelta_obj):
    """
    Calculate the total number of days, hours, minutes, and seconds from the given timedelta object.
    Parameters:
    timedelta_obj (timedelta): A timedelta object representing a duration of time.
    Returns:
    str: A formatted string with the total days, hours, minutes, and seconds calculated from the timedelta object.
    """
    seconds = timedelta_obj.total_seconds()
    time_total = ""
    if seconds > 86400:  # 60sec * 60min * 24hrs
        days = seconds // 86400
        time_total += "{} days".format(int(days))
        seconds = seconds - days * 86400

    if seconds > 3600:
        hrs = seconds // 3600
        time_total += " {} hours".format(int(hrs))
        seconds = seconds - hrs * 3600

    if seconds > 60:
        mins = seconds // 60
        time_total += " {} minutess".format(int(mins))
        seconds = seconds - mins * 60

    if seconds > 0:
        time_total += " {} seconds".format(int(seconds))
    return time_total
