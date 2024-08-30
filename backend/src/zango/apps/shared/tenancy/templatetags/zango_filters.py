"""
Module containing custom template filters
"""

import os
import re

from django import template
from django.conf import settings


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
        time_total += f"{int(days)} days"
        seconds = seconds - days * 86400

    if seconds > 3600:
        hrs = seconds // 3600
        time_total += f" {int(hrs)} hours"
        seconds = seconds - hrs * 3600

    if seconds > 60:
        mins = seconds // 60
        time_total += f" {int(mins)} minutess"
        seconds = seconds - mins * 60

    if seconds > 0:
        time_total += f" {int(seconds)} seconds"
    return time_total


@register.filter()
def use_latest(build_path):
    """
    Returns the latest version of a static file based on a given file path pattern.

    Args:
        build_path (str): the original file path pattern

    Returns:
        str: The path to the latest version of the file, or the original path if no match is found.

    Example:
        Usage in a Django template to reference the latest static file:

        <script src="{% static 'app_panel/js/build.*.min.js'|use_latest %}"></script>

        Make sure to load the zango filters with {% load zango_filters %}.
    """
    buildir = os.path.dirname(build_path)
    filep = os.path.basename(build_path)
    for dir in settings.STATICFILES_DIRS:
        for dirpath, dirnames, filenames in os.walk(dir):
            filenames = sorted(filenames, reverse=True)
            for filename in filenames:
                if re.match(filep, filename):
                    return os.path.join(buildir, filename)
    return build_path
