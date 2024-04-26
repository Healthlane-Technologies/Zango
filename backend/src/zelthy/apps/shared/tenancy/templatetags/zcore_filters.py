"""
Module containing custom template filters
"""
from django import template

register = template.Library()


@register.filter()
def humanize_timedelta(timedeltaobj):
    """
    Calculate the total number of days, hours, minutes, and seconds from the given timedelta object.

    Parameters:
    timedeltaobj (timedelta): A timedelta object representing a duration of time.

    Returns:
    str: A formatted string with the total days, hours, minutes, and seconds calculated from the timedelta object.
    """
    secs = timedeltaobj.total_seconds()
    timetot = ""
    if secs > 86400:  # 60sec * 60min * 24hrs
        days = secs // 86400
        timetot += "{} days".format(int(days))
        secs = secs - days * 86400

    if secs > 3600:
        hrs = secs // 3600
        timetot += " {} hours".format(int(hrs))
        secs = secs - hrs * 3600

    if secs > 60:
        mins = secs // 60
        timetot += " {} minutes".format(int(mins))
        secs = secs - mins * 60

    if secs > 0:
        timetot += " {} seconds".format(int(secs))
    return timetot
