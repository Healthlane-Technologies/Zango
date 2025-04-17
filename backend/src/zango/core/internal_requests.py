import io
import json
import mimetypes

from importlib import import_module

import requests

from requests.cookies import extract_cookies_to_jar
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers
from urllib3.response import HTTPResponse

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connection
from django.http.response import HttpResponse
from django.template.response import ContentNotRenderedError
from django.test import RequestFactory


original_post = requests.post
original_get = requests.get
original_put = requests.put
original_delete = requests.delete


def build_response(req, resp):
    response = Response()

    # Fallback to None if there's no status_code, for whatever reason.
    response.status_code = getattr(resp, "status", None)

    # Make headers case-insensitive.
    response.headers = CaseInsensitiveDict(getattr(resp, "headers", {}))

    # Set encoding.
    response.encoding = get_encoding_from_headers(response.headers)
    response.raw = resp
    response.reason = response.raw.reason

    if isinstance(req.url, bytes):
        response.url = req.url.decode("utf-8")
    else:
        response.url = req.url

    # Add new cookies from the server.
    extract_cookies_to_jar(response.cookies, req, resp)

    # Give the Response some context.
    response.request = req

    return response


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
    ws_module = import_module("zango.apps.dynamic_models.workspace.base")
    ws_klass = getattr(ws_module, "Workspace")
    ws = ws_klass(tenant, fake_request)
    ws.ready()
    view, resolve = ws.match_view(fake_request)
    if not view:
        return HttpResponse(status=404)

    captured_kwargs = getattr(resolve, "captured_kwargs", {})
    if captured_kwargs:
        kwargs.update(captured_kwargs)

    kwargs.pop("data", None)
    kwargs.pop("headers", None)
    kwargs.pop("params", None)
    kwargs.pop("files", None)

    response = view(fake_request, fake_request.META["PATH_INFO"], **kwargs)

    return response


def process_request_headers(headers):
    headers_dict = {}
    for k, v in headers.items():
        if k not in ["content-type"]:
            headers_dict[k] = v
    return headers_dict


def internal_request_post(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", {})
        headers = kwargs.get("headers", {})

        content_type = headers.pop("Content-Type", "")
        files = kwargs.get("files", {})
        cookies = kwargs.get("cookies", {})
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        if not headers.get("cookies"):
            headers["Cookie"] = cookie_header

        req_args = {"path": url, "data": data}
        if headers:
            req_args["headers"] = headers
        if content_type:
            req_args["content_type"] = content_type

        fake_request = fake_request.post(**req_args)
        uploaded_files = {}

        # Process each file in the list
        if isinstance(files, list):
            for file_info in files:
                try:
                    field_name, (file_name, file_obj, content_type) = file_info
                except ValueError:
                    field_name, file_obj, content_type = file_info
                    file_name = file_obj.name

                # Create an InMemoryUploadedFile object
                uploaded_file = InMemoryUploadedFile(
                    file=file_obj,
                    field_name=field_name,
                    name=file_name,
                    content_type=content_type,
                    size=file_obj.seek(
                        0, 2
                    ),  # Move to the end of the file to get its size
                    charset=None,
                )

                # Reset the file pointer to the beginning
                file_obj.seek(0)

                # Add the file to the dictionary
                if field_name in uploaded_files:
                    uploaded_files[field_name].append(uploaded_file)
                else:
                    uploaded_files[field_name] = [uploaded_file]

            # Add the files to request.FILES
            for field_name, files in uploaded_files.items():
                for file in files:
                    fake_request.FILES.appendlist(field_name, file)
        if isinstance(files, dict):
            for field_name, file_obj in files.items():
                # Create an InMemoryUploadedFile object
                uploaded_file = InMemoryUploadedFile(
                    file=file_obj,
                    field_name=field_name,
                    name=file_obj.name,
                    content_type=mimetypes.guess_type(file_obj.name)[0],
                    size=file_obj.seek(
                        0, 2
                    ),  # Move to the end of the file to get its size
                    charset=None,
                )

                # Reset the file pointer to the beginning
                file_obj.seek(0)

                # Add the file to request.FILES
                fake_request.FILES[field_name] = uploaded_file

        # query_dict = QueryDict(urlencode(data, doseq=True), mutable=True)

        # fake_request.POST = query_dict
        # fake_request.data = query_dict

        django_response = process_internal_request(fake_request, tenant, **kwargs)

        try:
            resp_body = django_response.content
        except ContentNotRenderedError:
            resp_body = getattr(django_response, "data", "")

        if isinstance(resp_body, dict):
            resp_body = json.dumps(resp_body).encode("utf-8")
        elif isinstance(resp_body, str):
            resp_body = resp_body.encode("utf-8")
        elif isinstance(resp_body, bytes):
            resp_body = resp_body
        else:
            raise ValueError(f"Unknown response type: {type(resp_body)} returned")

        # Convert Django response to urllib3.response.HTTPResponse
        urllib_response = HTTPResponse(
            body=io.BytesIO(resp_body),
            headers=django_response.headers,
            status=django_response.status_code,
            reason=getattr(django_response, "reason_phrase", ""),
            decode_content=False,
            preload_content=False,
        )

        # Set additional attributes on the urllib response
        urllib_response.reason = getattr(django_response, "reason_phrase", "")

        # Convert urllib response to requests.Response using the existing build_response function
        req = requests.Request("POST", url, data=data, headers=headers).prepare()
        response = build_response(req, urllib_response)
        if hasattr(django_response, "cookies"):
            for cookie_name, cookie_obj in django_response.cookies.items():
                # Extract cookie properties
                cookie_value = cookie_obj.value
                cookie_dict = {
                    "value": cookie_value,
                    "path": cookie_obj.get("path", "/"),
                    "domain": cookie_obj.get("domain", None),
                    "secure": cookie_obj.get("secure", False),
                }
                # Set the cookie in the requests.Response object
                response.cookies.set(cookie_name, **cookie_dict)
        return response

    # If domain is not internal, proceed with the normal requests.get call
    return original_post(url, **kwargs)


def internal_request_put(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", kwargs.get("json", {}))
        headers = kwargs.get("headers", {})
        files = kwargs.get("files", {})
        cookies = kwargs.get("cookies", {})
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        if not headers.get("cookies"):
            headers["Cookie"] = cookie_header

        content_type = headers.pop("Content-Type", "")

        req_args = {"path": url, "data": data}
        if headers:
            req_args["headers"] = headers
        if content_type:
            req_args["content_type"] = content_type

        fake_request = fake_request.put(**req_args)
        uploaded_files = {}

        # Process each file in the list
        if isinstance(files, list):
            for file_info in files:
                try:
                    field_name, (file_name, file_obj, content_type) = file_info
                except ValueError:
                    field_name, file_obj, content_type = file_info
                    file_name = file_obj.name

                # Create an InMemoryUploadedFile object
                uploaded_file = InMemoryUploadedFile(
                    file=file_obj,
                    field_name=field_name,
                    name=file_name,
                    content_type=content_type,
                    size=file_obj.seek(
                        0, 2
                    ),  # Move to the end of the file to get its size
                    charset=None,
                )

                # Reset the file pointer to the beginning
                file_obj.seek(0)

                # Add the file to the dictionary
                if field_name in uploaded_files:
                    uploaded_files[field_name].append(uploaded_file)
                else:
                    uploaded_files[field_name] = [uploaded_file]

            # Add the files to request.FILES
            for field_name, files in uploaded_files.items():
                for file in files:
                    fake_request.FILES.appendlist(field_name, file)
        if isinstance(files, dict):
            for field_name, file_obj in files.items():
                # Create an InMemoryUploadedFile object
                uploaded_file = InMemoryUploadedFile(
                    file=file_obj,
                    field_name=field_name,
                    name=file_obj.name,
                    content_type=mimetypes.guess_type(file_obj.name)[0],
                    size=file_obj.seek(
                        0, 2
                    ),  # Move to the end of the file to get its size
                    charset=None,
                )

                # Reset the file pointer to the beginning
                file_obj.seek(0)

                # Add the file to request.FILES
                fake_request.FILES[field_name] = uploaded_file

        django_response = process_internal_request(fake_request, tenant, **kwargs)

        try:
            resp_body = django_response.content
        except ContentNotRenderedError:
            resp_body = getattr(django_response, "data", "")

        if isinstance(resp_body, dict):
            resp_body = json.dumps(resp_body).encode("utf-8")
        elif isinstance(resp_body, str):
            resp_body = resp_body.encode("utf-8")
        elif isinstance(resp_body, bytes):
            resp_body = resp_body
        else:
            raise ValueError(f"Unknown response type: {type(resp_body)} returned")

        # Convert Django response to urllib3.response.HTTPResponse
        urllib_response = HTTPResponse(
            body=io.BytesIO(resp_body),
            headers=django_response.headers,
            status=django_response.status_code,
            reason=getattr(django_response, "reason_phrase", ""),
            decode_content=False,
            preload_content=False,
        )

        # Set additional attributes on the urllib response
        urllib_response.reason = getattr(django_response, "reason_phrase", "")

        # Convert urllib response to requests.Response using the existing build_response function
        req = requests.Request("PUT", url, data=data, headers=headers).prepare()
        response = build_response(req, urllib_response)
        if hasattr(django_response, "cookies"):
            for cookie_name, cookie_obj in django_response.cookies.items():
                # Extract cookie properties
                cookie_value = cookie_obj.value
                cookie_dict = {
                    "value": cookie_value,
                    "path": cookie_obj.get("path", "/"),
                    "domain": cookie_obj.get("domain", None),
                    "secure": cookie_obj.get("secure", False),
                }
                # Set the cookie in the requests.Response object
                response.cookies.set(cookie_name, **cookie_dict)
        return response

    # If domain is not internal, proceed with the normal requests.put call
    return original_put(url, **kwargs)


def internal_request_get(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        headers = kwargs.get("headers", {})
        cookies = kwargs.get("cookies", {})
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        if not headers.get("cookies"):
            headers["Cookie"] = cookie_header

        req_args = {
            "path": url,
        }
        if headers:
            req_args["headers"] = headers

        fake_request = fake_request.get(**req_args)

        django_response = process_internal_request(fake_request, tenant, **kwargs)

        try:
            resp_body = django_response.content
        except ContentNotRenderedError:
            resp_body = getattr(django_response, "data", "")

        if isinstance(resp_body, dict):
            resp_body = json.dumps(resp_body).encode("utf-8")
        elif isinstance(resp_body, str):
            resp_body = resp_body.encode("utf-8")
        elif isinstance(resp_body, bytes):
            resp_body = resp_body
        else:
            raise ValueError(f"Unknown response type: {type(resp_body)} returned")

        # Convert Django response to urllib3.response.HTTPResponse
        urllib_response = HTTPResponse(
            body=io.BytesIO(resp_body),
            headers=django_response.headers,
            status=django_response.status_code,
            reason=getattr(django_response, "reason_phrase", ""),
            decode_content=False,
            preload_content=False,
        )

        # Convert urllib response to requests.Response using the existing build_response function
        req = requests.Request("GET", url, headers=headers).prepare()
        response = build_response(req, urllib_response)
        if hasattr(django_response, "cookies"):
            for cookie_name, cookie_obj in django_response.cookies.items():
                cookie_value = cookie_obj.value
                cookie_dict = {
                    "value": cookie_value,
                    "path": cookie_obj.get("path", "/"),
                    "domain": cookie_obj.get("domain", None),
                    "secure": cookie_obj.get("secure", False),
                }
                response.cookies.set(cookie_name, **cookie_dict)
        return response

    # If domain is not internal, proceed with the normal requests.get call
    return original_get(url, **kwargs)


def internal_request_delete(url, **kwargs):
    domain_obj = get_domain_from_url(url)
    if domain_obj:
        tenant = domain_obj.tenant
        fake_request = RequestFactory()

        data = kwargs.get("data", {})
        headers = kwargs.get("headers", {})
        cookies = kwargs.get("cookies", {})
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        if not headers.get("cookies"):
            headers["Cookie"] = cookie_header

        req_args = {"path": url, "data": data}
        if headers:
            req_args["headers"] = headers

        fake_request = fake_request.delete(**req_args)

        django_response = process_internal_request(fake_request, tenant, **kwargs)

        try:
            resp_body = django_response.content
        except ContentNotRenderedError:
            resp_body = getattr(django_response, "data", "")

        if isinstance(resp_body, dict):
            resp_body = json.dumps(resp_body).encode("utf-8")
        elif isinstance(resp_body, str):
            resp_body = resp_body.encode("utf-8")
        elif isinstance(resp_body, bytes):
            resp_body = resp_body
        else:
            raise ValueError(f"Unknown response type: {type(resp_body)} returned")

        # Convert Django response to urllib3.response.HTTPResponse
        urllib_response = HTTPResponse(
            body=io.BytesIO(resp_body),
            headers=django_response.headers,
            status=django_response.status_code,
            reason=getattr(django_response, "reason_phrase", ""),
            decode_content=False,
            preload_content=False,
        )

        # Set additional attributes on the urllib response
        urllib_response.reason = getattr(django_response, "reason_phrase", "")

        # Convert urllib response to requests.Response using the existing build_response function
        req = requests.Request("DELETE", url, data=data, headers=headers).prepare()
        response = build_response(req, urllib_response)
        if hasattr(django_response, "cookies"):
            for cookie_name, cookie_obj in django_response.cookies.items():
                cookie_value = cookie_obj.value
                cookie_dict = {
                    "value": cookie_value,
                    "path": cookie_obj.get("path", "/"),
                    "domain": cookie_obj.get("domain", None),
                    "secure": cookie_obj.get("secure", False),
                }
                response.cookies.set(cookie_name, **cookie_dict)
        return response

    # If domain is not internal, proceed with the normal requests.delete call
    return original_delete(url, **kwargs)


# Patch the requests.get method
requests.post = internal_request_post
requests.put = internal_request_put
requests.get = internal_request_get
requests.delete = internal_request_delete
