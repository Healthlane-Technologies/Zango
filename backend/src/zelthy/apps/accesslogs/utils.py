from django.contrib.auth import signals

from axes.handlers.proxy import AxesProxyHandler
from django.http import HttpResponseForbidden, HttpResponse

from ..appauth.models import AppUserModel


def capture_failed_login_attempt(request, credentials):
    try:

        username_type, username = "", credentials.get("username", "")
        if "@" in username and "." in username:
            username_type = "email"

        elif username.replace("+", "").isdigit():
            username_type = "mobile"

        if username_type:
            filter_query = {username_type: username}
            app_user = AppUserModel.objects.get(**filter_query)
            signals.user_login_failed.send(
                sender=app_user,
                request=request,
                credentials=credentials,
            )
    except:
        import traceback

        print(traceback.format_exc())


def user_authentication_failed(request, credentials):

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
