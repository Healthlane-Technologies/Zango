import pytz

__all__ = [
    "TIMEZONES",
    "DATEFORMAT",
    "DATETIMEFORMAT",
]

TIMEZONES = [(tz, tz) for tz in pytz.all_timezones]

DATEFORMAT = (
              ('%d %b %Y','04 Oct 2017'),
              ('%d %B %Y','04 October 2017'),
              ('%d/%m/%Y','04/10/2017'),
              ('%d/%m/%y','04/10/17'),
              ('%m/%d/%y','10/04/17'),
              ('%d/%m/%Y','04/10/2017'),
              )

DATETIMEFORMAT = (
              ('%d %b %Y %H:%M','04 Oct 2017 13:48'),
              ('%d %b %Y %I:%M %p','04 Oct 2017 01:48 PM'),
              ('%d %B %Y %H:%M','04 October 2017 13:48'),
              ('%d %B %Y %I:%M %p','04 October 2017 01:48 PM'),
              ('%d/%m/%Y %H:%M','04/10/2017 13:48'),
              ('%d/%m/%y %I:%M %p','04/10/17 01:48 PM'),
              ('%m/%d/%y %H:%M','10/04/17 13:48'),
              ('%d/%m/%Y %I:%M %p','04/10/2017 01:48 PM'),
              )