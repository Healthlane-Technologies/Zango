import os

from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django.conf import settings

from django.views.generic import View
from django.http import Http404

from zelthy.core.utils import get_current_role
from zelthy.apps.dynamic_models.permissions import is_platform_user

from .workspace.base import Workspace


class PermMixin:
    def has_user_access_perm(self, request, *args, **kwargs):
        if is_platform_user(request):
            return True
        user_role = get_current_role()
        return user_role.has_perm(request, "userAccess")

    def has_view_perm(self, request, view_name, *args, **kwargs):
        if is_platform_user(request):
            return True
        user_role = get_current_role()
        return user_role.has_perm(request, "view", view_name=view_name)


def default_landing_view(request):
    """
    Renders the default landing page for the application.

    This view is displayed when the application root URL is accessed for the first time
    after installation and development server is not yet started.
    """

    project_name = os.path.basename(settings.BASE_DIR)
    context = {"project_name": project_name, "app_name": request.tenant.name}

    return render(request, "default_landing.html", context)


@method_decorator(csrf_exempt, name="dispatch")
class DynamicView(View, PermMixin):
    """
    this class is responsible for building the
    """

    def get_workspace(self, request):
        ws = Workspace(request.tenant, request)
        ws.ready()
        return ws

    def get_view(self, request):
        view, resolve = self.workspace.match_view(request)
        return view, resolve

    def dispatch(self, request, *args, **kwargs):
        if self.has_user_access_perm(request, *args, **kwargs):
            self.workspace = self.get_workspace(request)
            view, resolve = self.get_view(request)
            view_name = (
                ".".join(resolve.__dict__["_func_path"].split(".")[3:])
                if resolve
                else None
            )
            if view and view_name:
                kwargs = resolve.__dict__["kwargs"]
                if request.internal_routing or self.has_view_perm(
                    request, view_name, *args, **kwargs
                ):
                    response = csrf_protect(view)(request, *args, **kwargs)
                    return response
                else:
                    user_role = get_current_role()
                    if user_role.name == "AnonymousUsers":
                        return redirect("/login/")
                    return HttpResponseForbidden(
                        "You don't have permission to view this page"
                    )

            # View Not Found
            if request.path == "/" and not self.workspace.is_dev_started():
                return default_landing_view(request)

            raise Http404()
        return HttpResponseForbidden("You don't have permission to view this page")
