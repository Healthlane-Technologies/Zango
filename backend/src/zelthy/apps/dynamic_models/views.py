import asyncio
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator

from django.views.generic import View
from django.http import Http404
from django.core import signing

from .workspace.base import Workspace
from zelthy.core.utils import get_current_role
from zelthy.apps.dynamic_models.permissions import is_platform_user


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


@method_decorator(csrf_exempt, name="dispatch")
class DynamicView(View, PermMixin):
    """
    this class is responsible for building the
    """

    def get_view(self, request):
        ws = Workspace(request.tenant, request)
        ws.ready()
        view, resolve = ws.match_view(request)
        return view, resolve

    def dispatch(self, request, *args, **kwargs):
        if self.has_user_access_perm(request, *args, **kwargs):
            view, resolve = self.get_view(request)
            view_name = ".".join(resolve.__dict__["_func_path"].split(".")[5:]) if resolve else None
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
                        return redirect("/app/home/")
                    return HttpResponseForbidden(
                        "You don't have permission to view this page"
                    )
            
            # View Not Found
            if request.path == "/":
                return redirect("/app/home/")

            raise Http404()
        return HttpResponseForbidden("You don't have permission to view this page")
