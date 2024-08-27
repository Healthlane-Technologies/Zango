import re

from axes.handlers.proxy import AxesProxyHandler

from django.contrib.auth import signals
from django.http import HttpResponse, HttpResponseForbidden

from zango.apps.appauth.models import AppUserModel


def capture_failed_login_attempt(request, credentials):
    """
    Capture and handle a failed login attempt.
    Parameters:
    - request (HttpRequest): The HTTP request object.
    - credentials (dict): A dictionary containing the login credentials, with the username as the key.
    Returns:
    None
    """

    try:
        username_type, username = "", credentials.get("username", "")
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", username):
            username_type = "email"

        elif re.match(r"^\+[1-9]\d{1,14}$", username):
            username_type = "mobile"

        if username_type:
            filter_query = {username_type: username}
            app_user = AppUserModel.objects.filter(**filter_query).last()
            if app_user:
                signals.user_login_failed.send(
                    sender=app_user,
                    request=request,
                    credentials=credentials,
                )
    except Exception:
        import traceback

        print(traceback.format_exc())


def user_authentication_failed(request, credentials):
    """
    This function handles the case when user authentication fails.
    It captures the failed login attempt by calling the 'capture_failed_login_attempt' function with
    the given request and credentials.
    Parameters:
    - request: The HTTP request object.
    - credentials: A dictionary containing the user's credentials.
    Returns:
    If the request is not allowed by the AxesProxyHandler, it returns a dictionary with the following keys:
    - 'is_locked': True
    - 'message': "Account locked"
    - 'status': The HTTP status code for HttpResponseForbidden
    If the request is allowed by the AxesProxyHandler, it returns a dictionary with the following keys:
    - 'is_locked': False
    - 'message': "This account is permitted to log in"
    - 'status': The HTTP status code for HttpResponse
    """
    capture_failed_login_attempt(request, credentials)

    if not AxesProxyHandler.is_allowed(request):
        return {
            "is_locked": True,
            "message": "Account locked",
            "status": HttpResponseForbidden.status_code,
        }
    else:
        return {
            "is_locked": False,
            "message": "This account is permitted to log in",
            "status": HttpResponse.status_code,
        }
