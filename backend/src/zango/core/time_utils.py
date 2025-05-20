import json

from datetime import datetime

import pytz

from django.conf import settings


def process_timestamp(timestamp, timezone=None):
    try:
        ts = json.loads(timestamp)
        if not timezone:
            timezone = settings.TIME_ZONE
        tz = pytz.timezone(timezone)
        ts["start"] = tz.localize(
            datetime.strptime(ts["start"] + "-" + "00:00", "%Y-%m-%d-%H:%M"),
            is_dst=None,
        )
        ts["end"] = tz.localize(
            datetime.strptime(ts["end"] + "-" + "23:59", "%Y-%m-%d-%H:%M"),
            is_dst=None,
        )
        return ts
    except Exception:
        import traceback

        traceback.print_exc()
        return None
