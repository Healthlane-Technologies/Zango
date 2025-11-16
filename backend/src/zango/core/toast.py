import json

from typing import Dict, Literal, Optional, TypedDict

from django.contrib import messages
from django.http import request


class ActionSchema(TypedDict, total=False):
    text: str
    url: Optional[str]


def ztoast(
    request: request.HttpRequest,
    message: str,
    title: str = "",
    level: Literal["success", "error", "warning", "info"] = "success",
    primary_action: ActionSchema | None = None,
    secondary_action: ActionSchema | None = None,
    duration: int | None = None,
    extra_tags: str = "",
):
    """
    Displays a toast notification with the specified parameters.

    Args:
        request: The HTTP request object.
        message: The message content of the toast notification.
        title: The title of the toast notification. Defaults to an empty string,
            which will result in the title being set to the capitalized `level`.
        level: The severity level of the toast notification. Defaults to "success".
            Accepted values are "success", "error", "warning", and "info".
        primary_action: An optional primary action for the toast, defined by an
            ActionSchema dictionary with 'text' and 'url' keys.
        secondary_action: An optional secondary action for the toast, defined by an
            ActionSchema dictionary with 'text' and 'url' keys.
        duration: The duration the toast should be visible, in milliseconds. Defaults to None.
        extra_tags: Additional tags to categorize the toast notification. Defaults to "".

    Raises:
        ValueError: If `level` is not one of the accepted values.

    """

    if title == "":
        title = level.capitalize()

    msg_level = messages.SUCCESS

    if level == "success":
        msg_level = messages.SUCCESS
    elif level == "error":
        msg_level = messages.ERROR
    elif level == "warning":
        msg_level = messages.WARNING
    elif level == "info":
        msg_level = messages.INFO
    else:
        raise ValueError("Invalid level: %s" % level)

    msg: Dict[str, str | ActionSchema | None | int] = {
        "message": message,
        "title": title,
        "primary_action": primary_action,
        "secondary_action": secondary_action,
    }
    if duration is not None:
        msg["duration"] = duration
    if extra_tags:
        extra_tags = f"{extra_tags} zango"
    else:
        extra_tags = "zango"
    messages.add_message(request, msg_level, json.dumps(msg), extra_tags=extra_tags)
