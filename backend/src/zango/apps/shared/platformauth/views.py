from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect

from django.utils.decorators import method_decorator

from axes.decorators import axes_dispatch
@method_decorator(axes_dispatch, name='dispatch')
# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("/platform")

from django.utils.decorators import method_decorator

from axes.decorators import axes_dispatch
@method_decorator(axes_dispatch, name='dispatch')
class PlatformUserLogoutView(LogoutView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        return redirect("/auth/login")
