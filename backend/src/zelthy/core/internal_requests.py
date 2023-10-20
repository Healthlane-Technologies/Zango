import requests
import json
from urllib.parse import urlparse
from django.urls import resolve
from django.http import HttpRequest
from django.conf import settings
from django.db import connection
from importlib import import_module
from django.test import RequestFactory


from django_tenants.utils import get_tenant_domain_model, remove_www

original_post = requests.post

def fake_get_response(request):
    # This could be a mock response, or just a pass-through.
    return request

def internal_request_post(url, **kwargs):
    domain = url.split("://")[-1].split("/")[0]
    domain = remove_www(domain.split(':')[0])
    domain_obj = get_tenant_domain_model().objects.filter(domain=domain).first()
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()
        fake_request = fake_request.post(url, data=kwargs.get('data', {}), content_type='application/json')
        fake_request.tenant = tenant
        fake_request.internal_routing = True
        connection.set_tenant(tenant)
        ws_module = import_module('zelthy.apps.dynamic_models.workspace.base')
        ws_klass = getattr(ws_module, 'Workspace')
        ws = ws_klass(tenant, fake_request)
        ws.ready()
        view, resolve = ws.match_view(fake_request)
        response = view(fake_request, (), **kwargs)
        # Convert Django response to something that mimics requests.Response
        class InternalResponse:
            def __init__(self, django_response):
                self.content = django_response.content
                self.status_code = django_response.status_code

            def json(self):
                return json.loads(self.content)

        return InternalResponse(response)

    # If domain is not internal, proceed with the normal requests.get call
    return original_post(url, **kwargs)

# Patch the requests.get method
requests.post = internal_request_post
