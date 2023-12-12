import requests
import json
from importlib import import_module

from django.db import connection
from django.test import RequestFactory


original_post = requests.post
original_get = requests.get
original_put = requests.put
original_delete = requests.delete


def fake_get_response(request):
    # This could be a mock response, or just a pass-through.
    return request


def get_domain_from_url(url):
    from django_tenants.utils import get_tenant_domain_model, remove_www

    domain = url.split("://")[-1].split("/")[0]
    domain = remove_www(domain.split(":")[0])
    domain_obj = get_tenant_domain_model().objects.filter(domain=domain).first()
    return domain_obj


def process_internal_request(fake_request, tenant, **kwargs):
    fake_request.tenant = tenant
    fake_request.internal_routing = True
    connection.set_tenant(tenant)
    ws_module = import_module("zelthy.apps.dynamic_models.workspace.base")
    ws_klass = getattr(ws_module, "Workspace")
    ws = ws_klass(tenant, fake_request)
    ws.ready()
    view, resolve = ws.match_view(fake_request)
    response = view(fake_request, (), **kwargs)
    return response


def process_request_headers(headers):
    headers_dict = {}
    for k, v in headers.items():
        if k not in ["Content-Type"]:
            headers_dict[k] = v
    return headers_dict


def internal_request_post(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", {})
        headers = kwargs.get("headers", {})
        query_params = kwargs.get("params", {})

        content_type = headers.get("Content-Type", "")

        fake_request = fake_request.post(
            url,
            data=data,
            # headers=headers, # TODO
            content_type=content_type,
            query_params=query_params,
        )

        response = process_internal_request(fake_request, tenant, **kwargs)

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


def internal_request_put(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", {})
        headers = kwargs.get("headers", {})
        query_params = kwargs.get("params", {})

        content_type = headers.get("Content-Type", "")

        fake_request = fake_request.put(
            url,
            data=data,
            # headers=headers, # TODO
            content_type=content_type,
            query_params=query_params,
        )

        response = process_internal_request(fake_request, tenant, **kwargs)

        # Convert Django response to something that mimics requests.Response
        class InternalResponse:
            def __init__(self, django_response):
                self.content = django_response.content
                self.status_code = django_response.status_code

            def json(self):
                return json.loads(self.content)

        return InternalResponse(response)

    # If domain is not internal, proceed with the normal requests.get call
    return original_put(url, **kwargs)


def internal_request_get(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        headers = kwargs.get("headers", {})
        query_params = kwargs.get("params", {})
        fake_request = fake_request.get(url, headers=headers, data=query_params)

        response = process_internal_request(fake_request, tenant, **kwargs)

        # Convert Django response to something that mimics requests.Response
        class InternalResponse:
            def __init__(self, django_response):
                self.content = django_response.content
                self.status_code = django_response.status_code

            def json(self):
                return json.loads(self.content)

        return InternalResponse(response)

    # If domain is not internal, proceed with the normal requests.get call
    return original_get(url, **kwargs)


def internal_request_delete(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", {})
        headers = kwargs.get("headers", {})
        query_params = kwargs.get("params", {})

        content_type = headers.get("Content-Type", "")

        fake_request = fake_request.put(
            url,
            data=data,
            # headers=headers, # TODO
            content_type=content_type,
            query_params=query_params,
        )

        response = process_internal_request(fake_request, tenant, **kwargs)

        # Convert Django response to something that mimics requests.Response
        class InternalResponse:
            def __init__(self, django_response):
                self.content = django_response.content
                self.status_code = django_response.status_code

            def json(self):
                return json.loads(self.content)

        return InternalResponse(response)

    # If domain is not internal, proceed with the normal requests.get call
    return original_delete(url, **kwargs)


# Patch the requests.get method
requests.post = internal_request_post
requests.put = internal_request_put
requests.get = internal_request_get
requests.delete = internal_request_delete
