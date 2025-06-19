import json

from typing import Optional, TypedDict

from django.contrib import messages


class ActionSchema(TypedDict, total=False):
    text: str
    url: Optional[str]


def ztoast(
    request,
    message,
    title="",
    level="success",
    primary_action: ActionSchema | None = None,
    secondary_action: ActionSchema | None = None,
    placement="bottomRight",
):
    if title == "":
        title = level.capitalize()

    if level == "success":
        level = messages.SUCCESS
    elif level == "error":
        level = messages.ERROR
    elif level == "warning":
        level = messages.WARNING
    else:
        raise ValueError("Invalid level: %s" % level)

    msg = {
        "message": message,
        "title": title,
        "primary_action": primary_action,
        "secondary_action": secondary_action,
        "placement": placement,
    }
    messages.add_message(request, level, json.dumps(msg))
