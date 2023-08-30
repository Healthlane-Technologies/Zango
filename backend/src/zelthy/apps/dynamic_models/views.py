
import asyncio
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator

from django.views.generic import View
from django.http import Http404

from .workspace.base import Workspace

class PermMixin:

    def has_user_access_perm(self, request, *args, **kwargs):
        return True
    
    def has_view_perm(self, request, *args, **kwargs):
        return True


@method_decorator(csrf_exempt, name='dispatch')
class DynamicView(View, PermMixin):
    """
        this class is responsible for building the     
    """
    
    def get_view(self, request):
        ws = Workspace(request.tenant, request)
        ws.ready()
        view =  ws.match_view(request)
        return view

    def dispatch(self, request, *args, **kwargs):
        if self.has_user_access_perm(request, *args, **kwargs) and \
                            self.has_view_perm(request, *args, **kwargs):
            view = self.get_view(request)
            if view:
                response = csrf_protect(view)(request, *args, **kwargs)
                return response

            return Http404()
        return HttpResponseForbidden("You don't have permission to view this page")
    


